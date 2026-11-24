# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.
- 2026-11-24: Added `cnt_range_3` (max − min of `cnt` over the three completed calendar days before the prediction date, via `shift(1)` before the rolling window). Availability holds: only strictly earlier counts are used. Validation: ridge R^2 0.6475 -> 0.6935 (delta +0.046, MAE 832.9 -> 751.2, delta -81.7); hgb R^2 0.2185 -> 0.2645 (delta +0.046, MAE 1296.6 -> 1253.8, delta -42.8). Kept.
