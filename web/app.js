"use strict";
const $ = (s) => document.querySelector(s),
  fmt = (x) => (100 * x).toFixed(1) + "%",
  title = (s) =>
    s.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase()),
  esc = (s) =>
    String(s).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
let report,
  examples,
  survey,
  view = "overview",
  step = 0,
  answers = {},
  finished = false;
const drugs = {
  alcohol: "Alcohol",
  amphetamines: "Amphetamines",
  amyl: "Amyl nitrite",
  benzodiazepines: "Benzodiazepines",
  caffeine: "Caffeine",
  cannabis: "Cannabis",
  chocolate: "Chocolate",
  cocaine: "Cocaine",
  crack: "Crack",
  ecstasy: "Ecstasy",
  heroin: "Heroin",
  ketamine: "Ketamine",
  legal_highs: "Legal highs",
  lsd: "LSD",
  methadone: "Methadone",
  mushrooms: "Mushrooms",
  nicotine: "Nicotine",
  vsa: "Volatile substances",
};
let target = {
    substances: ["amphetamines", "cocaine", "crack", "ketamine"],
    window: "month",
    minimum: 2,
  },
  recency = {};
const windows = { decade: 2, year: 3, month: 4, week: 5, day: 6 };
function hero(k, h, p) {
  return `<section class="hero"><div class="kicker">${k}</div><h1>${h}</h1><p class="lede">${p}</p></section>`;
}
function go(n) {
  view = n;
  document.querySelectorAll("nav button").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === n);
    b.setAttribute("aria-current", b.dataset.view === n ? "page" : "false");
  });
  render();
  window.scrollTo(0, 0);
}
function overview() {
  return (
    hero(
      "01 / The research",
      "Personality is a pattern.<br><em>Not a prediction of fate.</em>",
      "Explore your traits, define a research question, and see what a model can—and cannot—learn from a historical survey.",
    ) +
    `<div class="grid"><div class="card"><div class="label">SURVEY PARTICIPANTS</div><div class="stat">${report.rows.toLocaleString()}</div><p class="small">UCI Drug Consumption dataset</p></div><div class="card"><div class="label">MATCH THE DEFINED TARGET</div><div class="stat">${fmt(report.prevalence)}</div><p class="small">${report.positive_count} people in the full sample</p></div><div class="card"><div class="label">HELD-OUT AVERAGE PRECISION</div><div class="stat">${report.test.average_precision.toFixed(3)}</div><p class="small">Baseline: ${report.test_baselines.training_prevalence.average_precision.toFixed(3)} · ranking remains limited</p></div></div><div class="grid two"><section class="card dark"><div class="kicker">THE ORIGINAL IDEA, RECONSIDERED</div><h2>Turn curiosity into a testable question.</h2><p>Amir’s project connects personality measurement with machine learning. This edition makes the target explicit, separates people before training, and tests complex models against simple ones.</p><button data-go="profile">Explore your personality →</button></section><section class="card"><h2>What are we modeling?</h2><p>${esc(report.target.description)}.</p><p class="small">Reported behaviors in a survey, not a diagnosis, addiction measure, or prediction of future drug use.</p><button class="secondary" data-go="target">Inspect the target →</button></section></div><section class="card"><h2>Evidence before complexity.</h2><p>We compared logistic regression, a weighted baseline, a random forest, gradient boosting, and a voting ensemble. Training cross-validation selected <strong>${title(report.selected)}</strong>. All results remain visible.</p><button class="secondary" data-go="model">Open the model lab →</button></section>`
  );
}
function profile() {
  let intro = hero(
    "02 / Your personality",
    "A little more<br><em>self-understanding.</em>",
    "50 public-domain IPIP statements. Think about how you generally are, rather than how you would like to be. About 5–8 minutes.",
  );
  if (finished)
    return (
      intro +
      `<section class="card"><h2>Your IPIP profile</h2><p class="small">Raw totals from 10 to 50. These are not percentiles or diagnostic categories.</p>${survey
        .map((s) => {
          let score = s.items.reduce(
            (a, q, i) =>
              a +
              (q.direction === 1
                ? answers[s.trait][i]
                : 6 - answers[s.trait][i]),
            0,
          );
          return `<p><strong>${title(s.trait)}</strong> · ${score} / 50</p><progress value="${score - 10}" max="40" aria-label="${s.trait} score ${score}"></progress>`;
        })
        .join(
          "",
        )}<div class="notice">The dataset used NEO personality measurements, plus separate impulsivity and sensation-seeking scales. These IPIP totals cannot be substituted for those features. A validated conversion has not been established here, so we do not generate a personal drug-use estimate from your answers.</div><p class="small">Neuroticism here means sensitivity to negative emotions, the reverse of emotional stability. It is not a diagnosis. Trait names describe tendencies, not worth or destiny.</p><div class="actions"><button data-go="model">Explore research examples</button><button class="secondary" id="reset">Clear my answers</button></div></section>`
    );
  let s = survey[step];
  return (
    intro +
    `<section class="card"><div class="kicker">Section ${step + 1} of 5 · ${title(s.trait)}</div><progress value="${Object.values(answers).flat().filter(Boolean).length}" max="50" aria-label="Answered questions"></progress><p class="small">1 = very inaccurate · 2 = moderately inaccurate · 3 = neither · 4 = moderately accurate · 5 = very accurate</p>${s.items.map((q, i) => `<div class="question"><label for="q${i}">${step * 10 + i + 1}. ${esc(q.text)}</label><select id="q${i}" data-question="${i}"><option value="">Choose an answer</option>${[1, 2, 3, 4, 5].map((n) => `<option value="${n}" ${answers[s.trait]?.[i] === n ? "selected" : ""}>${n} — ${["Very inaccurate", "Moderately inaccurate", "Neither", "Moderately accurate", "Very accurate"][n - 1]}</option>`).join("")}</select></div>`).join("")}<p id="survey-error" class="error" role="alert"></p><div class="actions"><button class="secondary" id="previous" ${step === 0 ? "disabled" : ""}>Back</button><button id="next">${step === 4 ? "See my profile" : "Next section →"}</button><button class="secondary" id="reset">Clear answers</button></div><p class="small">Answers stay in memory in this tab. Reloading or closing clears them. Nothing is sent to the server.</p></section>`
  );
}
function targetPage() {
  return (
    hero(
      "03 / Define the question",
      "Make the label<br><em>mean something.</em>",
      "A count and a time window are easier to interpret than an average of recency categories. Try hypothetical responses below.",
    ) +
    `<section class="card"><h2>Choose substances</h2>${Object.entries(drugs)
      .map(
        ([k, n]) =>
          `<label class="check"><input type="checkbox" value="${k}" ${target.substances.includes(k) ? "checked" : ""}>${n}</label>`,
      )
      .join(
        "",
      )}<div class="actions"><label>At least <select id="minimum">${Array.from({ length: Math.max(1, target.substances.length) }, (_, i) => `<option ${target.minimum === i + 1 ? "selected" : ""}>${i + 1}</option>`).join("")}</select> substances</label><label> within the past <select id="window">${Object.keys(
      windows,
    )
      .map(
        (w) => `<option ${w === target.window ? "selected" : ""}>${w}</option>`,
      )
      .join(
        "",
      )}</select></label></div><div class="notice">This playground does not retrain the loaded model. Its target remains: ${esc(report.target.description)}.</div><h2>Hypothetical responses</h2>${target.substances.map((k) => `<div class="question"><label for="r-${k}">${drugs[k]}</label><select id="r-${k}" data-recency="${k}">${["Never", "Over a decade ago", "In the last decade", "In the last year", "In the last month", "In the last week", "In the last day"].map((s, i) => `<option value="${i}" ${(recency[k] || 0) === i ? "selected" : ""}>${s}</option>`).join("")}</select></div>`).join("")}<p id="target-result" class="result"></p><p class="small">“Last day” also counts toward “last month.” Methadone is not methamphetamine. “Legal highs” is the historical dataset label, not a statement of current legality.</p><button id="download-config" ${target.substances.length ? "" : "disabled"}>Download target configuration</button><p class="small">Use this JSON with the README training command. Repeated target exploration is not independent validation.</p></section>`
  );
}
function modelPage() {
  const m = report.test,
    c = m.confusion_matrix;
  return (
    hero(
      "04 / The model lab",
      "Look closely.<br><em>Keep the uncertainty.</em>",
      "A fixed split, transparent model comparison, and public survey examples. Scores describe the defined historical label in this sample.",
    ) +
    `<section class="card"><h2>Try a public dataset example</h2><p class="small">Six deliberately selected examples: three in each outcome class. A demonstration, not a representative sample. Features use the original dataset quantification; no questionnaire conversion is applied.</p><label for="example">Survey profile </label><select id="example">${examples.map((e, i) => `<option value="${i}">${e.label}</option>`).join("")}</select><div id="example-detail"></div><button id="predict">Run the model</button><div id="prediction" role="status"></div></section><div class="grid"><div class="card"><div class="label">HELD-OUT PRECISION</div><div class="stat">${fmt(m.precision)}</div><p class="small">Of positive classifications, how many matched?</p></div><div class="card"><div class="label">HELD-OUT RECALL</div><div class="stat">${fmt(m.recall)}</div><p class="small">Of reported matches, how many were found?</p></div><div class="card"><div class="label">AVERAGE PRECISION · 95% INTERVAL</div><div class="stat">${m.average_precision.toFixed(3)}</div><p class="small">${report.test_ci95.average_precision.map((x) => x.toFixed(3)).join(" – ")} · 300 bootstrap resamples</p></div></div><div class="grid two"><section class="card"><h2>Model comparison</h2><p class="small">Mean training-only 5-fold average precision. Selection happens before the held-out test.</p><table><thead><tr><th>Candidate</th><th>Mean AP</th></tr></thead><tbody>${Object.entries(
      report.cv_average_precision,
    )
      .sort((a, b) => b[1].mean - a[1].mean)
      .map(
        ([n, s]) =>
          `<tr><td>${title(n)}${n === report.selected ? " ✓" : ""}</td><td>${s.mean.toFixed(3)}</td></tr>`,
      )
      .join(
        "",
      )}</tbody></table></section><section class="card"><h2>Where it gets things wrong</h2><p class="small">${report.splits.test.count} test participants · ${report.splits.test.positive_count} actual matches · threshold ${report.threshold.toFixed(2)}, selected on validation F1.</p><table><thead><tr><th>Reported / predicted</th><th>No match</th><th>Match</th></tr></thead><tbody><tr><th>No match</th><td>${c[0][0]}</td><td>${c[0][1]}</td></tr><tr><th>Match</th><td>${c[1][0]}</td><td>${c[1][1]}</td></tr></tbody></table><p class="small">Brier score: ${m.brier.toFixed(4)} (lower is better); constant-prevalence baseline: ${report.test_baselines.training_prevalence.brier.toFixed(4)}.</p></section></div><section class="card"><h2>What this evidence does not establish</h2><ul>${report.limitations.map((s) => `<li>${esc(s)}</li>`).join("")}</ul><p class="small">Split: ${report.splits.train.count} train / ${report.splits.validation.count} validation / ${report.splits.test.count} test. No resampling before splitting. Seed ${report.seed}.</p><a class="button secondary" href="/api/report" download="report.json">Download full evaluation</a></section>`
  );
}
function render() {
  $("#content").innerHTML = {
    overview,
    profile,
    target: targetPage,
    model: modelPage,
  }[view]();
  document
    .querySelectorAll("[data-go]")
    .forEach((b) => (b.onclick = () => go(b.dataset.go)));
  if (view === "profile") {
    document.querySelectorAll("[data-question]").forEach(
      (el) =>
        (el.onchange = () => {
          (answers[survey[step].trait] ??= Array(10).fill(null))[
            Number(el.dataset.question)
          ] = el.value ? Number(el.value) : null;
        }),
    );
    $("#reset").onclick = () => {
      answers = {};
      step = 0;
      finished = false;
      render();
    };
    if (!finished) {
      $("#previous").onclick = () => {
        step--;
        render();
      };
      $("#next").onclick = () => {
        if ((answers[survey[step].trait] || []).filter(Boolean).length !== 10) {
          $("#survey-error").textContent =
            "Please answer all 10 statements before continuing.";
          return;
        }
        if (step === 4) finished = true;
        else step++;
        render();
        window.scrollTo(0, 0);
      };
    }
  }
  if (view === "target") {
    document.querySelectorAll("input[type=checkbox]").forEach(
      (el) =>
        (el.onchange = () => {
          target.substances = [
            ...document.querySelectorAll("input:checked"),
          ].map((e) => e.value);
          target.minimum = Math.min(
            target.minimum,
            Math.max(1, target.substances.length),
          );
          render();
        }),
    );
    $("#minimum").onchange = (e) => {
      target.minimum = Number(e.target.value);
      targetResult();
    };
    $("#window").onchange = (e) => {
      target.window = e.target.value;
      targetResult();
    };
    document.querySelectorAll("[data-recency]").forEach(
      (e) =>
        (e.onchange = () => {
          recency[e.dataset.recency] = Number(e.value);
          targetResult();
        }),
    );
    targetResult();
    $("#download-config").onclick = () => {
      const u = URL.createObjectURL(
        new Blob([JSON.stringify(target, null, 2)], {
          type: "application/json",
        }),
      );
      const a = document.createElement("a");
      a.href = u;
      a.download = "target.json";
      a.click();
      setTimeout(() => URL.revokeObjectURL(u), 1000);
    };
  }
  if (view === "model") {
    $("#example").onchange = showExample;
    showExample();
    $("#predict").onclick = async () => {
      const b = $("#predict");
      b.disabled = true;
      try {
        const r = await fetch("/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            features: examples[Number($("#example").value)].features,
            measurement: "uci373_quantified",
          }),
        });
        const d = await r.json();
        if (!r.ok) throw Error(d.error);
        $("#prediction").innerHTML =
          `<p class="result">${fmt(d.score)}</p><p>${d.matches ? "Classified as a match" : "Classified as no match"} at threshold ${d.threshold.toFixed(2)}.</p><p class="small">${esc(d.meaning)} This is not a calibrated personal or population probability.</p>`;
      } catch (e) {
        $("#prediction").textContent = e.message;
      } finally {
        b.disabled = false;
      }
    };
  }
}
function targetResult() {
  let n = target.substances.filter(
    (k) => (recency[k] || 0) >= windows[target.window],
  ).length;
  $("#target-result").textContent = target.substances.length
    ? `${n} qualifying · ${n >= target.minimum ? "Match" : "No match"}`
    : "Select at least one substance.";
}
function showExample() {
  let e = examples[Number($("#example").value)];
  $("#example-detail").innerHTML = `<p class="small">${Object.entries(
    e.features,
  )
    .map(([k, v]) => `${title(k)}: ${v.toFixed(2)}`)
    .join(
      " · ",
    )}</p><p>Reported target: <strong>${e.reported_match ? "match" : "no match"}</strong></p>`;
  $("#prediction").textContent = "";
}
document
  .querySelectorAll("nav button")
  .forEach((b) => (b.onclick = () => go(b.dataset.view)));
Promise.all(
  ["/api/report", "/api/examples", "/survey.json"].map((u) =>
    fetch(u).then((r) => {
      if (!r.ok) throw Error("Could not load application data.");
      return r.json();
    }),
  ),
)
  .then((d) => {
    [report, examples, survey] = d;
    render();
  })
  .catch((e) => {
    $("#content").textContent = e.message;
  });
