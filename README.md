# Personality Studio

A modern rebuild of Amir Edris’s [PredictingDrugUse](https://github.com/AmirMEdris/PredictingDrugUse): explore personality, construct an explicit research target, and inspect reproducible machine-learning results. The original repository is preserved.

**This models reported past use in a historical survey. It does not predict future risk, diagnose addiction, or support decisions about individuals.**

## Run the application

Install Python 3.12 or later, download or clone this repository, open a terminal in its folder, and run:

```sh
python -m personality.server
```

Open **http://127.0.0.1:8765**. On Windows, `py -3 -m personality.server` also works. Stop with Ctrl+C. No pip install, GPU, account, or data download is needed to use the shipped application. Use `--port 8766` if the default port is occupied.

The app includes:

- A responsive, keyboard-accessible 50-item IPIP questionnaire, with named trait wiring, reverse scoring, required answers, progress and reset.
- A configurable target playground: select substances, recency window and minimum count; inspect hypothetical responses and download a training configuration.
- A model lab with six public dataset examples, live inference, model comparison, confusion matrix, uncertainty and downloadable evaluation.
- Local-only serving, no analytics or cookies, no stored questionnaire responses and no remote scripts. Questionnaire answers stay in browser memory; reload clears them. Only public dataset examples go to the local inference endpoint.

## What is actually trained?

The default label is **at least two of amphetamines, cocaine, crack and ketamine reported within the past month** (CL4, CL5 or CL6). These four preserve the original project’s selected group; ketamine is not being labeled a stimulant. “Meth” in the dataset is methadone, not methamphetamine.

Seven named quantified features: neuroticism, extraversion, openness, agreeableness, conscientiousness, impulsivity and sensation seeking. Demographic features are excluded in this first rebuild. The fictitious Semeron response is not a selectable outcome; no respondents are removed based on it in this protocol.

The dataset has 1,885 people and 98 matches (5.20%). Fixed stratified splits: 1,131 training, 377 validation, 377 test. No balancing occurs before splitting. Five-fold training-only cross-validation compares logistic regression, weighted logistic regression, random forest, gradient boosting and a soft-voting ensemble. Validation selects the F1 operating threshold; the test set is evaluated afterward. All candidate specifications and seeds are explicit.

The selected model is **logistic regression**, not the more complex ensemble. On 377 held-out people:

| Measure | Result |
|---|---:|
| Average precision | 0.1288 |
| Constant-score AP baseline | 0.0531 |
| AP bootstrap 95% interval | 0.0775–0.2435 |
| ROC AUC | 0.7759 |
| Precision / recall at threshold 0.11 | 11.1% / 15.0% |
| True positive / false positive | 3 / 24 |
| False negative / true negative | 17 / 333 |
| Brier / constant-prevalence Brier | 0.04907 / 0.05024 |

Ranking is better than the constant-score baseline, but the operating classifier is weak. The test set contains only 20 positives. Bootstrap intervals do not include model-selection uncertainty. Scores are not calibrated population probabilities. See [the model card](docs/MODEL_CARD.md) and [full results](artifacts/report.json).

## Questionnaire and measurement boundary

IPIP items are public domain. The app scores each 10-item domain from 10 to 50; reverse-keyed answers contribute `6 - response`. Neuroticism is the reverse of the IPIP Emotional Stability direction. Openness is the conventional label used here for the IPIP Intellect/Imagination scale. These are raw sums, not norms or percentiles.

**The dataset used NEO-FFI-R, not this IPIP inventory.** It also includes separate impulsivity and sensation-seeking instruments. There is no established, validated conversion implemented here. Questionnaire totals therefore do not feed the drug-use model. This is a deliberate scientific boundary, not a claim that Amir’s questionnaire work was inherently unreliable. See [measurement notes](docs/MEASUREMENT.md).

## Reproduce or change an experiment

Training needs Python 3.12 and the pinned scientific dependencies. The data is downloaded from UCI separately, checked against a pinned SHA-256, and ignored by git.

```sh
python -m venv .venv
# Activate .venv (Windows: .venv\Scripts\activate; macOS/Linux: source .venv/bin/activate)
python -m pip install -r requirements.txt
python -m personality.data
python -m personality.experiment
```

The bounded entry point limits numerical libraries to one thread, uses CPU only and terminates a training job after four hours. This dataset is small; the verified cloud run took far less than that. Nothing uses your laptop’s GPU. For a downloaded target configuration:

```sh
python -m personality.experiment --config path/to/target.json --output experiments/my-target
```

Review the output before replacing the shipped `artifacts/` files. The playground alone never changes the model. A target needs at least 30 participants in each class for this protocol. Repeated target experiments reuse this dataset and are not independent external validation. Do not select a target or model by its test score.

## Verification

```sh
python -m unittest discover -s tests -v
node --check web/app.js
```

Nine unit/integration tests cover label boundaries, invalid inputs, split isolation, HTTP origin/host checks, measurement rejection, survey keys and portable inference parity for all five candidates. Scientific dependencies are needed for the training tests. Optional browser regression and recording, with the server already running:

```sh
python -m pip install playwright==1.62.0
python -m playwright install chromium ffmpeg
python tests/browser_smoke.py
```

The browser regression was not completed in the build workspace: its Chromium process could not create a required socket. No recording or visual verification is claimed. Unit/HTTP/model tests and JavaScript syntax checks passed.

Set `CHROMIUM_PATH` to an existing Chromium executable if needed. The browser script checks all 50 answers, trait maxima, no questionnaire POSTs, target boundaries, inference, reset and mobile overflow. Verification images/video are generated locally and ignored by git.

## Project layout

`personality/core.py`: target and safe JSON inference; `data.py`: acquisition/schema validation; `train.py`: reproducible experiment; `experiment.py`: resource bounds; `server.py`: loopback HTTP app. `web/`: dependency-free interface and IPIP keys. `artifacts/`: evaluated model, report and selected public examples. Models use JSON, never executable pickle.

[Sources and third-party permissions](docs/SOURCES.md). No software license is assigned on Amir’s behalf; dataset and IPIP permissions are separately documented. This application is intended for local research, not public internet hosting.
