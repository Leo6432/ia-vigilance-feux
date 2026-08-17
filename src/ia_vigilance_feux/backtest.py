from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, brier_score_loss, classification_report, confusion_matrix
from sklearn.preprocessing import label_binarize

from ia_vigilance_feux.modeling import ModelBundle, predict_frame, train_model


@dataclass(frozen=True)
class BacktestResult:
    predictions: pd.DataFrame
    metrics: dict[str, object]
    model: ModelBundle


def run_temporal_backtest(
    features: pd.DataFrame,
    train_end_year: int,
    test_year: int,
    version: str = "model_v001",
) -> BacktestResult:
    train_validation = features[features["target_date"].dt.year <= train_end_year].copy()
    test = features[features["target_date"].dt.year == test_year].copy()
    if train_validation.empty or test.empty:
        raise ValueError("Backtest impossible: periode d'entrainement ou de test vide")

    model = train_model(train_validation, version=version, validation_year=train_end_year)
    predictions = predict_frame(model, test)
    y_true = test["label_level"].astype(int).to_numpy()
    y_pred = predictions["level"].astype(int).to_numpy()
    y_prob = predictions[["prob_green", "prob_yellow", "prob_orange", "prob_red"]].to_numpy()
    y_bin = label_binarize(y_true, classes=[0, 1, 2, 3])

    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "classification_report": classification_report(y_true, y_pred, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3]).tolist(),
        "false_alert_rate_orange_red": _false_alert_rate(y_true, y_pred),
        "orange_detection_rate": _detection_rate(y_true, y_pred, level=2),
        "red_detection_rate": _detection_rate(y_true, y_pred, level=3),
        "brier_score_macro": float(
            sum(brier_score_loss(y_bin[:, idx], y_prob[:, idx]) for idx in range(4)) / 4.0
        ),
    }
    return BacktestResult(predictions=predictions, metrics=metrics, model=model)


def write_backtest_outputs(result: BacktestResult, output_dir: str | Path) -> None:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    result.predictions.to_csv(path / "predictions.csv", index=False)
    pd.Series(result.metrics, dtype="object").to_json(path / "metrics.json", indent=2)


def _false_alert_rate(y_true, y_pred) -> float:
    alerts = y_pred >= 2
    if alerts.sum() == 0:
        return 0.0
    false_alerts = alerts & (y_true < 2)
    return float(false_alerts.sum() / alerts.sum())


def _detection_rate(y_true, y_pred, level: int) -> float:
    actual = y_true == level
    if actual.sum() == 0:
        return 0.0
    detected = actual & (y_pred >= level)
    return float(detected.sum() / actual.sum())
