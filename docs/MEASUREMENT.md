# Measurement decisions

The old app reconstructed five IPIP domains and used centered responses with direction keys: `sum(direction * (response - 3)) + 30`. For ten items this is algebraically equivalent to summing 1–5 answers with reversed items scored `6-response`. That was substantive scoring work, not an arbitrary invented questionnaire.

Four old domain keys aligned with their intended direction. The old neuroticism key reversed several distress items incorrectly. The new key is `[1,-1,1,-1,1,1,1,1,1,1]`. The GUI’s openness/conscientiousness positional swap is removed by named features. The old age and education encodings do not survive: this model deliberately omits demographics.

The new public-domain instrument remains an IPIP Big Five factor-marker inventory, not a NEO-FFI-R reproduction. Intellect/Imagination is presented as openness, and Emotional Stability is reversed to neuroticism. No normative bands are invented.

The dataset describes 60-item NEO-FFI-R scores and separately measured impulsivity and sensation seeking. Exact historical item wording, edition-specific transformations and app redistribution rights for NEO are not established here. We include no proprietary NEO questionnaire, BIS questionnaire or ImpSS items. A raw-score range or correlation between instruments does not establish interchangeable features; a linear rescale or z-score transform is not a validated crosswalk.

A defensible end-to-end personal inference extension would need either licensed administration/scoring of the exact relevant instruments and a verified source transformation, or a consented paired-instrument validation dataset supporting the proposed bridge. Both still require external validation of the behavioral model and intended use. Until then, personal IPIP profiles and dataset-model demonstrations stay visibly separate.
