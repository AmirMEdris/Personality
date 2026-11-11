# Engineering decisions and research contracts

## Preserve the creative part: define behavior precisely

The original insight was to turn multiple recency responses into a usable target and connect it to personality. The redesign makes that construction inspectable. A count of substances is not a severity score. Two reports within one month do not imply simultaneous consumption. Ordinal recency codes must not be averaged as if equally spaced or interpreted as dose.

Three useful directions:

1. **Recent breadth (implemented UCI benchmark):** count selected substances meeting a recency threshold. Transparent, reproducible and close to the original intention.
2. **Substance-specific profiles (proposed):** separate outcomes expose whether a broad label hides different patterns. A future multi-output model could share information, but sufficient events and predeclared reporting are required.
3. **Window sensitivity (proposed):** compare monthly versus yearly reported use as different estimands. Never choose the outcome retrospectively because it scores best on a test set.

For LISS, `ap08a130–133` are lifetime routing answers and `ap08a142–145` are recent frequency answers. Explicit lifetime non-use establishes no recent use; an unanswered routed question remains unknown. Frequency 1–4 establishes some use, 5 establishes none. For a threshold k, sum known positive answers as the lower bound and add missing outcomes for the upper bound: label positive when lower≥k, negative when upper<k, otherwise unknown. This retains only logically established labels; it does not impute behavior.

The adapter uses English codebook variable names; real export coding must be verified before use. It does not automatically download, accept terms, or run LISS training. Source: https://dataarchive.lissdata.nl/hosted-files/download/379

## Keep predictors and outcomes apart

UCI predictors are seven named quantified measurements. Drug recency, demographics and participant IDs are excluded. LISS would use 50 item responses, with five scored domains as an ablation; do not duplicate all items and scores without examining redundancy. A person ID joins waves, never predicts outcomes. A household-aware split is required when household clustering is present. Entirely unanswered questionnaires need exclusion or explicit abstention, not a fabricated profile.

Current LISS adapter tests cover structure and routing, not statistical suitability. Training remains blocked until authorised data access, matched cohort sizes, missingness, language translation, time alignment, household identifiers and model-release permissions are checked.

## Why these model families?

- **Regularized linear:** a stable low-variance baseline for small samples.
- **Pairwise interactions:** tests whether trait combinations add information while shrinking coefficients.
- **Extra Trees:** nonlinear thresholds and interactions, constrained by minimum leaf size.
- **Boosted trees:** shallow sequential residual corrections with a modest learning rate.
- **Stacking:** a learned combination of complementary predictions, with internal cross-fitting to avoid training its combiner on in-sample base scores.

We use five outer folds and three inner stack folds, all within training. A fixed candidate specification keeps the small sample from supporting an unbounded search. The selected model gets sigmoid calibration from training OOF predictions, then validation chooses an F1 threshold. Calibration fits after architecture selection, so the OOF calibration is not an unbiased estimate of the entire selection procedure. Audit data remains separate from those fitting steps, but has been exposed in prior work.

Average precision is useful under class imbalance; report the positive fraction beside it. F1 is an explicit experimental convention, not a clinical cost function. The interface lets users examine validation threshold trade-offs without silently changing the frozen audit threshold. Accuracy alone would hide the rare positive class.

## Explain without making causal claims

Permutation importance uses validation data and repeated shuffling. Correlated features can share or obscure importance; negative changes are retained in the report. Reliability curves use quantile bins, with few positives and no guarantee of calibration in a new population. Bootstrap intervals describe variation within the audit sample, not uncertainty from model selection, source bias or measurement substitution.

Architecture, comparison, precision–recall, reliability, threshold trade-offs and co-occurrence are visualized from real report fields. Hypothetical label examples are explicitly interactive examples; proposed architectures are marked as proposals.

## Reproducibility, resources and release

The runner pins source SHA-256 and seed, preserves the previous split, records fold scores and split hashes, and refuses output overwrite. A dedicated subprocess sets one numerical thread and a four-hour timeout. No GPU or external model API is used. Record a fresh external cohort before claiming generalization; repeated benchmark results do not reset that requirement.

The local checkpoint is executable joblib and is never loaded by the web server. Only trusted locally trained checkpoints belong in the CLI workflow. The original portable JSON inference remains separate. A matched-data production model would need a versioned input contract, support/abstention policy, verified safe serialization, external evaluation and explicit release rights before replacing it.

Sources: [StackingClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.StackingClassifier.html), [calibration principles](https://scikit-learn.org/stable/modules/calibration.html), [LISS agreement](https://liss.statements.centerdata.nl/). Dependencies are pinned to the tested versions in `requirements.txt`.
