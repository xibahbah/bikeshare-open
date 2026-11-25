# Seeded faults

## Fault 1 — Forbidden `casual` feature

Temporary change: appended `casual` to the list returned by `feature_columns`.

### Hook stderr (replay with the fault still present)

```text
Leakage tests failed after editing /Users/keith/Desktop/DSC 180A/bikeshare-open/src/features.py:
feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7 cnt_range_3
0   2011-01-10     10.0  WINTER  ...     1349...30.142857      1754.0
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571      1754.0

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_range_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 7 passed in 0.61s
```

### Failing test output

```text
python -m pytest tests/ -q
.....F.........                                                          [100%]
=================================== FAILURES ===================================
__________________________ test_no_forbidden_features __________________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7 cnt_range_3
0   2011-01-10     10.0  WINTER  ...     1349...30.142857      1754.0
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571      1754.0

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_range_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 14 passed in 1.55s
make: *** [test] Error 1
```

### Repair

Claude Code removed the temporary `casual` entry in 1 repair turn. `make test` reported `15 passed in 1.17s`, and `git --no-pager diff -- src/features.py` produced no output.
