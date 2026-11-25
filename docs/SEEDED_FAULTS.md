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

## Fault 2 — Rolling mean includes today

```diff
diff --git a/src/features.py b/src/features.py
index 342ac56..84f218c 100644
--- a/src/features.py
+++ b/src/features.py
@@ -73,7 +73,7 @@ def build_features(df: pd.DataFrame) -> pd.DataFrame:
     # If you add a longer lag, raise LAG_WARMUP in src/config.py.
     out["cnt_lag_1"] = out[TARGET].shift(1)
     out["cnt_lag_7"] = out[TARGET].shift(LAG_WARMUP)
-    out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
+    out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
 
     # --- Range of prior demand: max minus min over the three calendar days
     # before the prediction date. shift(1) moves cnt off today before the
```

### Hook stderr (replay with fault present)

```text
Leakage tests failed after editing /Users/keith/Desktop/DSC 180A/bikeshare-open/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 7 passed in 0.59s
```

### Failing test output

```text
python -m pytest tests/ -q
........F......                                                          [100%]
=================================== FAILURES ===================================
_______________________ test_rolling_mean_excludes_today _______________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7 cnt_range_3
0   2011-01-10     10.0  WINTER  ...     1349...31.428571      1754.0
713 2012-12-31    731.0  WINTER  ...      920.0  1789.857143      1754.0

[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 14 passed in 1.60s
make: *** [test] Error 1
```

### Repair

Claude Code restored `.shift(1)` before the rolling mean in 1 repair turn. `make test` reported `15 passed in 1.58s`. The diff for `src/features.py` was empty after repair.

## Exercise 1 — Failing feature test before implementation

```text
python -m pytest tests/ -q
.........F.....                                                          [100%]
=================================== FAILURES ===================================
_______________________________ test_cnt_range_3 _______________________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_cnt_range_3(feats):
        """cnt_range_3 for 2011-02-01 is the max minus the min of cnt over the
        three calendar days before it.
    
        Hand-computed from strictly earlier dates: Jan 29 = 1098, Jan 30 = 1096,
        Jan 31 = 1501, so cnt_range_3 = max - min = 1501 - 1096 = 405.
        """
        date = pd.Timestamp("2011-02-01")
>       assert feats.set_index("dteday").cnt_range_3[date] == pytest.approx(405)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_leakage.py:68: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self =             instant  season      yr  ... cnt_lag_1 cnt_lag_7   cnt_roll_7
dteday                               ...    ... 1787.0  1530.142857
2012-12-31    731.0  WINTER  2012.0  ...    1796.0     920.0  1531.428571

[714 rows x 27 columns]
name = 'cnt_range_3'

    @final
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        # Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        if (
            name not in self._internal_names_set
            and name not in self._metadata
            and name not in self._accessors
            and self._info_axis._can_hold_identifiers_and_holds_name(name)
        ):
            return self[name]
>       return object.__getattribute__(self, name)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'DataFrame' object has no attribute 'cnt_range_3'

.venv/lib/python3.13/site-packages/pandas/core/generic.py:6194: AttributeError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_cnt_range_3 - AttributeError: 'DataFrame' ...
1 failed, 14 passed in 1.76s
make: *** [test] Error 1

```

## Fault 3 — Unknown weather label no longer raises

Claude Code's Edit calls failed, so I seeded the one-line fault in Terminal and replayed the hook manually.

```diff
diff --git a/src/features.py b/src/features.py
index 342ac56..5d2e86a 100644
--- a/src/features.py
+++ b/src/features.py
@@ -27,7 +27,7 @@ def encode_weather(series: pd.Series) -> pd.Series:
     known = series.dropna()
     unknown = set(known.unique()) - set(WEATHER_ORDER)
     if unknown:
-        raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
+        pass
     return series.map(WEATHER_ORDER).astype(float)
```

### Hook stderr (manual replay)

```text
Leakage tests failed after editing /Users/keith/Desktop/DSC 180A/bikeshare-open/src/features.py:
......F..                                                                [100%]
=================================== FAILURES ===================================
__________________ test_encode_weather_rejects_unknown_label ___________________

    def test_encode_weather_rejects_unknown_label():
        """encode_weather must fail loudly on an unmapped weather label."""
        from src.features import encode_weather
    
>       with pytest.raises(ValueError, match="UNMAPPED"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:75: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_encode_weather_rejects_unknown_label - Fai...
1 failed, 8 passed in 0.61s
```

### Failing test output

```text
python -m pytest tests/ -q
...........F.....                                                        [100%]
=================================== FAILURES ===================================
__________________ test_encode_weather_rejects_unknown_label ___________________

    def test_encode_weather_rejects_unknown_label():
        """encode_weather must fail loudly on an unmapped weather label."""
        from src.features import encode_weather
    
>       with pytest.raises(ValueError, match="UNMAPPED"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:75: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_encode_weather_rejects_unknown_label - Fai...
1 failed, 16 passed in 1.52s
make: *** [test] Error 1
```

### Repair

Claude Code restored the weather encoder guard with `git restore --worktree -- src/features.py` in one repair turn. `make test` reported `17 passed in 1.91s`. A Git diff confirmed that the source matched HEAD after the repair.
