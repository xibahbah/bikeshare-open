# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.
- 2026-11-24: Added `cnt_range_3` (max − min of `cnt` over the three completed calendar days before the prediction date, via `shift(1)` before the rolling window). Availability holds: only strictly earlier counts are used. Validation: ridge R^2 0.6475 -> 0.6935 (delta +0.046, MAE 832.9 -> 751.2, delta -81.7); hgb R^2 0.2185 -> 0.2645 (delta +0.046, MAE 1296.6 -> 1253.8, delta -42.8). Kept.
- 2026-11-25 — Exercise 4. Trained HGB to predict `cnt - cnt_roll_7` and added `cnt_roll_7` back to each forecast. The seven-day mean uses only completed days, so it is available at prediction time and can track recent demand levels. On validation, HGB improved from R² 0.2645 and MAE 1253.8 to R² 0.7282 and MAE 705.7, beating ridge at R² 0.6935 and MAE 751.2. I chose this transformation for the final test evaluation and kept the main pipeline's target unchanged.
- 2026-11-25 — Updated `CLAUDE.md` to record the `cnt_range_3` availability rule and `/capture-fault` workflow. The skill captures each fault's diff, hook stderr, and test output before repair.
- 2026-11-25 — Final verification found that a derived copy of `cnt` named `demand_proxy` passed all 17 existing tests. Added checks on actual feature values for renamed target components and affine reconstructions of `cnt` from up to three features. This strengthens verification without changing predictors or scores.
- 2026-11-25 — Saved the already selected Exercise 4 calculation in `src.train.score_residual_experiment`, invoked with `--residual valid` or `--residual test`. These commands print both baselines and all comparison models without overwriting `reports/metrics.json`; documented this rule in `CLAUDE.md`. Reproduction runs verify the fixed experiment, not a new round of test-set selection.
- 2026-11-25 — Exercise 5. Under an explicitly assumed MAE objective for daily ride counts, prefer persistence to untransformed ridge: test MAE 840.1 versus 902.4, despite ridge's higher R² (0.6051 versus 0.5099). This is an AI-assisted deployment argument, not a claim that a real operator supplied a loss function or that deployment was performed.
