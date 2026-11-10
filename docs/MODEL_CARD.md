# Model card

**Purpose:** reproducible educational exploration of associations between quantified personality traits and a stated past-use label in UCI dataset 373. Not a clinical or future-risk model. No individual screening, employment, insurance, treatment or punitive use is supported.

**Target:** at least two of amphetamines, cocaine, crack and ketamine reported in CL4–CL6 (last month/week/day). A count, not a sum or mean of ordinal category numbers. No claim that severity, frequency, dependence or future behavior follows from this label.

**Data:** 1,885 historical self-reports; 98 positive labels. Source SHA-256 and version provenance are in `artifacts/report.json`. Original quantification occurred before release; fitting a scaler within each fold does not reverse source preprocessing. Sampling, demographic imbalance, self-report bias and transport to other populations remain limitations. Seven trait features only. Participants reporting the fictitious drug are retained; this choice is explicit, not a validated quality filter.

**Protocol:** seed 20261110, stratified 60/20/20 participant split; five-fold CV within training; selection by mean average precision; single threshold selected by validation F1 over 0.02–0.98, ties favor higher thresholds. Class weights are computed within training fits. No oversampling. No test-driven tuning. Candidate held-out audits at threshold 0.5 are supplemental and do not determine the winner. The shipped model is trained only on the training split, not refitted to all data.

**Candidates:** scaled logistic C=1; scaled class-weighted logistic; 200-tree weighted forest depth6/minleaf8; 120-step gradient boosting depth2/minleaf12/rate0.04/subsample0.85; equal-weight soft vote of unweighted logistic, forest and boosting. Sophisticated models were actually trained and evaluated; complexity did not win training CV.

**Result:** selected logistic; test AP0.1288, ROC AUC0.7759, precision0.1111, recall0.15, F1 0.1277 at threshold0.11. Confusion matrix rows actual/columns predicted: `[[333,24],[17,3]]`. The always-negative classifier has 94.7% accuracy versus this model’s89.1%; accuracy alone is misleading with a rare label. Brier0.04907 vs constant baseline0.05024. AP95% bootstrap interval0.0775–0.2435; 300 resamples of the held-out predictions, not a full uncertainty estimate across model fitting/selection. Probability calibration is not established. Reliability-bin data is included in the report.

**Inference:** safe portable JSON; exact named features; measurement identifier required; finite numbers within training ranges. The range gate is a conservative application rule, not proof of in-distribution validity. Selected-model inference was checked against sklearn on all in-range test rows; synthetic tests verify all export formats. Six public examples are deliberately balanced for illustration and are not performance evidence. No questionnaire-to-model conversion.

**Next research priorities:** externally validate the predeclared target; evaluate repeated/nested resampling without test-driven selection; assess calibration and uncertainty with sufficient positive examples; study subgroup validity where justified and sample sizes permit; resolve measurement comparability before personal inference. More complexity cannot compensate for measurement mismatch or an unsupported intended use.
