"""Stage 3: temporal split, fit, evaluate, write metrics.

Two baselines and two models, on purpose.

  baseline_mean         predict the 2011 average for every day
  baseline_persistence  predict yesterday's count (cnt_lag_1)
  ridge                 standardised linear model on the audited features
  hgb                   gradient-boosted trees on the same features

The mean baseline shows what "the distribution moved" costs. Persistence
is the baseline that actually matters: ridge's features are dominated by
lagged demand, so if it cannot beat "yesterday again" it has learned
nothing worth reporting. The booster is there because it fails, and the
reason it fails is the headline result.

Run: python -m src.train
"""
import argparse
import json

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import METRICS, PROCESSED, TARGET, TRAIN_END, VALID_END
from src.features import feature_columns


class PersistenceBaseline(BaseEstimator, RegressorMixin):
    """Predict a single lagged column unchanged. Nothing is fit."""

    def __init__(self, column: str = "cnt_lag_1"):
        self.column = column

    def fit(self, X, y=None):
        if self.column not in X.columns:
            raise ValueError(f"persistence baseline needs column {self.column!r}")
        return self

    def predict(self, X):
        return X[self.column].to_numpy(dtype=float)


MODELS = {
    "baseline_mean": DummyRegressor(strategy="mean"),
    "baseline_persistence": PersistenceBaseline("cnt_lag_1"),
    "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    "hgb": HistGradientBoostingRegressor(random_state=0, max_iter=300),
}


def temporal_split(df: pd.DataFrame):
    """Split by date, never at random. A random split on a time series
    puts tomorrow in train and today in test."""
    train = df[df.dteday <= TRAIN_END]
    valid = df[(df.dteday > TRAIN_END) & (df.dteday <= VALID_END)]
    test = df[df.dteday > VALID_END]
    return train, valid, test


def fit_and_score(exclude_feature: str | None = None) -> dict:
    df = pd.read_parquet(PROCESSED)
    cols = feature_columns(df)
    if exclude_feature is not None:
        cols.remove(exclude_feature)
    train, valid, test = temporal_split(df)

    results = {
        "n_features": len(cols),
        "features": cols,
        "n_train": len(train),
        "n_valid": len(valid),
        "n_test": len(test),
    }
    for name, model in MODELS.items():
        model.fit(train[cols], train[TARGET])
        results[name] = {
            split: {
                "r2": round(float(r2_score(part[TARGET], model.predict(part[cols]))), 4),
                "mae": round(float(mean_absolute_error(part[TARGET], model.predict(part[cols]))), 1),
            }
            for split, part in [("valid", valid), ("test", test)]
        }
    return results


def score_residual_experiment(split: str) -> dict:
    """Reproduce Exercise 4 without overwriting the untransformed metrics."""
    if split not in {"valid", "test"}:
        raise ValueError("split must be 'valid' or 'test'")
    df = pd.read_parquet(PROCESSED)
    columns = feature_columns(df)
    train, valid, test = temporal_split(df)
    evaluation = valid if split == "valid" else test
    predictions = {}
    for name, estimator in MODELS.items():
        model = clone(estimator).fit(train[columns], train[TARGET])
        predictions[name] = model.predict(evaluation[columns])
    residual = clone(MODELS["hgb"]).fit(
        train[columns], train[TARGET] - train["cnt_roll_7"]
    )
    predictions["hgb_residual"] = (
        residual.predict(evaluation[columns]) + evaluation["cnt_roll_7"].to_numpy()
    )
    return {
        "split": split,
        "n_train": len(train),
        "n_evaluation": len(evaluation),
        "scores": {
            name: {
                "r2": round(float(r2_score(evaluation[TARGET], prediction)), 4),
                "mae": round(float(mean_absolute_error(evaluation[TARGET], prediction)), 1),
            }
            for name, prediction in predictions.items()
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--residual", choices=["valid", "test"],
        help="run the fixed Exercise 4 experiment on this split; print scores only",
    )
    args = parser.parse_args()
    if args.residual:
        print(json.dumps(score_residual_experiment(args.residual), indent=2))
    else:
        res = fit_and_score()
        res["before_feature"] = fit_and_score(exclude_feature="cnt_range_3")
        METRICS.parent.mkdir(parents=True, exist_ok=True)
        METRICS.write_text(json.dumps(res, indent=2))
        print(json.dumps({k: v for k, v in res.items() if k != "features"}, indent=2))
