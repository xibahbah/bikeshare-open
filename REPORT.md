# Results

The task is to predict daily Capital Bikeshare rentals, `cnt`. The fixed temporal split uses 2011 for training, January–June 2012 for validation, and July–December 2012 for testing. Calendar reindexing and missing-history removal leave 348 training, 182 validation, and 184 test rows. The feature set grows from 14 to 15 columns; the rows and model settings stay the same. All models, including ridge's scaler, fit on training rows only.

The table comes from `reports/metrics.json`. “Before” is its `before_feature` entry; “After” is the top-level result. MAE is measured in rides per day.

| Feature set | Model | Validation R² | Validation MAE | Test R² | Test MAE |
|---|---|---:|---:|---:|---:|
| Before | baseline_mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| Before | baseline_persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Before | ridge | 0.6475 | 832.9 | 0.5833 | 947.1 |
| Before | hgb | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| After | baseline_mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| After | baseline_persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| After | ridge | 0.6935 | 751.2 | 0.6051 | 902.4 |
| After | hgb | 0.2645 | 1253.8 | -0.5080 | 1986.5 |

The new feature, `cnt_range_3`, is the maximum minus minimum count over the three completed calendar days before prediction. January 29–31, 2011 have counts 1098, 1096, and 1501, so the February 1 expectation is 1501 − 1096 = 405. Commit `6b7ec2b` added the failing test before `0bd59a1` implemented the shifted rolling range. The feature improved validation R² by 0.0460 for both models; validation MAE fell by 81.7 for ridge and 42.8 for HGB. These are observed improvements on one validation period, not evidence of statistical significance. The test results are mixed: ridge improves, while HGB gets slightly worse.

Reproduce the untransformed table with `make all` and verify the suite with `make test`, after installing the pinned requirements into an activated virtual environment. The final suite has 19 tests. A clean checkout was used to compare regenerated metrics byte-for-byte. The original raw CSV's SHA-256 remains `a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc`.

`docs/SEEDED_FAULTS.md` preserves actual failures, hook stderr, repair-turn counts, and the Bash copy that bypassed an Edit/Write hook. Manual hook replays are identified explicitly. Final verification exposed a further gap: a renamed copy of the target passed the original suite. The added value checks now reject renamed target components and exact affine identities involving up to three input columns. These checks cover specific failure modes, not every possible leak.

The final self-audit in `reports/audit.jsonl` reports no target leakage; its numerical identity tool also returned `clean`. I reject parts of its explanation: positive persistence R² means it beats the test-period mean, not that it learns beyond persistence. Negative HGB R² alone does not establish a comparison with persistence; the table establishes that comparison. Several cited source lines do not exist, and the seven-day lag uses `shift(7)`, not `shift(1)`. The original JSON is retained unchanged. For the 16k local model, a launcher invoked the supplied `agent/audit.py` with project-only settings, only the Read built-in tool, the SDK identity tool, and structured output. It supplied a compact file of numbered source, metrics, and actual test output; the model read that file and called the identity tool. This was an adapted SDK run. Full pipeline reproduction was checked independently in a clean checkout.

# Headline finding

A perfect score is possible by predicting `casual + registered`, because their sum equals `cnt`; those same-day components are excluded from the actual predictors. Under the chronological split, the training-mean baseline reaches test R² −2.1441, showing the cost of applying the old demand level to a later period. After the feature addition, ridge reaches 0.6051 against persistence at 0.5099, but loses on MAE, 902.4 versus 840.1. HGB reaches R² −0.5080 and MAE 1986.5: it is worse than the test-period constant implicit in R², yet better than the deployable training-mean baseline. This is consistent with rising demand and the tree model's inability to extrapolate a smooth demand trend from lag values beyond its training experience. I kept `cnt_range_3` based on the recorded validation improvements, without changing the model settings in response to its mixed test results.

# Exercise 4: target transformation

Let `m(d)` be `cnt_roll_7`, the average count over the seven completed days before date `d`. Fit HGB to the residual `cnt(d) - m(d)`, then reconstruct the forecast as `predicted_residual(d) + m(d)`. The shifted seven-day mean is available for a daily forecast after the previous day's count is observed. It supplies a moving demand level while the tree predicts deviations from it.

| Model, with cnt_range_3 | Validation R² | Validation MAE | Test R² | Test MAE |
|---|---:|---:|---:|---:|
| Training mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| Persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Ridge | 0.6935 | 751.2 | 0.6051 | 902.4 |
| HGB, original target | 0.2645 | 1253.8 | -0.5080 | 1986.5 |
| HGB, seven-day residual | 0.7282 | 705.7 | 0.6390 | 811.2 |

The transformation was chosen on validation and recorded in `docs/DECISIONS.md` at commit `1d1c6e9` before its first test evaluation. It improved HGB's validation R² from 0.2645 to 0.7282 and MAE from 1253.8 to 705.7, beating ridge on both measures. Its first held-out evaluation then gave R² 0.6390 and MAE 811.2. The original pipeline had already printed baseline test metrics, and later fixed reproduction runs accessed test again; I therefore do not claim that the test data was executed against only once across the whole project. No further transformation or hyperparameter selection followed those test results.

The fixed experiment is saved in `src.train.score_residual_experiment`. Run `python -m src.train --residual valid` for validation and `python -m src.train --residual test` to reproduce the selected test comparison. Both print all comparison scores without overwriting the untransformed `reports/metrics.json`.

This transformation is defensible for sequential daily predictions because it uses observed past demand, not the current target or future counts. It would not be directly available for a fixed multi-day forecast without updating or forecasting the intervening counts. Another limitation is inherited from the starter: same-day recorded weather is used as input. These scores are conditional on having that weather information; an operational day-ahead forecast would need forecast-weather inputs and a new evaluation. The result supports the role of a changing demand level, not a general claim that residual HGB always wins.

# Exercise 5: ridge vs persistence

If daily absolute error is the deployment objective, I would choose persistence over the untransformed ridge model. Before the feature, ridge improves test R² from 0.5099 to 0.5833 but increases MAE from 840.1 to 947.1. After the feature, ridge's R² advantage grows to 0.0952, yet its MAE is still 62.3 rides worse, 902.4 versus 840.1. R² weights squared errors, whereas MAE measures average absolute error, so the different rankings are compatible. Without an explicit cost function that makes large misses disproportionately costly, these results do not justify ridge's extra complexity. Residual HGB has the best observed test MAE at 811.2, but that does not establish a stable deployment advantage without additional chronological evaluation. The MAE objective is an assumption for this argument, not a requirement supplied by an actual bike operator.

# Attribution

Models used: Claude Code with [Flint v1.0](https://openrouter.ai/recursive/flint-v1.0%3Afree) through OpenRouter (40B total parameters, about 2.5B active), then local `qwen3:4b-instruct` (4B, 16,384-token context, alias `bikeshare-faults-local`) after the hosted quota was exhausted; OpenAI Codex also assisted with workflow, code, verification, and this report (parameter count not available).

AI-generated or AI-assisted work:

- Claude Code implemented `cnt_range_3` and its date-specific test, assisted with fault seeding and repairs, and produced the peer-audit output preserved in `docs/AUDIT.md`.
- Codex supplied setup/debugging commands, the raw-column classification check, reproducible before/after metrics, the saved residual experiment, and the stronger numerical leakage tests. It also assembled and checked evidence, drafted the report and decision entries, and ran submission checks.
- The `capture-fault` skill and `CLAUDE.md` additions were AI-assisted. The original pipeline, `new-feature` skill, hook, and auditor originated in the course starter. The self-audit JSON is actual local-model output, not a manually authored verdict.

Decisions adopted by me with AI assistance, recorded in `docs/DECISIONS.md`:

- Retain the starter's count target, forbidden-column policy, chronological split, and both baselines.
- Keep `cnt_range_3` using only earlier counts, based on its validation improvement.
- Select the seven-day residual transformation on validation and keep untransformed metrics as the main comparison.
- Adopt the MAE-based persistence argument, strengthen checks after the renamed-leak failure, and document the feature and evidence-capture workflow.

The peer auditor incorrectly said the training module was missing; its output is preserved separately from the checked verdict. Small-model prose was treated as a claim to verify, not as execution evidence. The model switch was operational; no controlled comparison of model sizes is claimed.
