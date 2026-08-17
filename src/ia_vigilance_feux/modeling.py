from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import TimeSeriesSplit

from ia_vigilance_feux.domain import VigilanceLevel, probabilities_to_score, score_to_level

REQUIRED_COLUMNS = {"department_code", "target_date", "horizon", "available_at", "label_level"}


@dataclass(frozen=True)
class ModelBundle:
    version: str
    feature_columns: list[str]
    thresholds: tuple[float, float, float]
    estimator: CalibratedClassifierCV
    metrics: dict[str, object]


def load_feature_table(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["target_date", "available_at"])
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Colonnes obligatoires manquantes: {sorted(missing)}")
    if (df["available_at"].dt.date > df["target_date"].dt.date).any():
        raise ValueError("Data leakage: available_at ne peut pas etre posterieur a target_date")
    return df.sort_values(["target_date", "department_code", "horizon"]).reset_index(drop=True)


def feature_columns(df: pd.DataFrame) -> list[str]:
    excluded = REQUIRED_COLUMNS | {"source", "model_version"}
    columns = [column for column in df.columns if column not in excluded]
    numeric = [column for column in columns if pd.api.types.is_numeric_dtype(df[column])]
    if not numeric:
        raise ValueError("Aucune feature numerique disponible pour l'entrainement")
    return numeric


def temporal_split(df: pd.DataFrame, validation_year: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    years = df["target_date"].dt.year
    if validation_year is None:
        validation_year = int(years.max())
    train = df[years < validation_year]
    validation = df[years == validation_year]
    if train.empty or validation.empty:
        raise ValueError("Split temporel invalide: train et validation doivent contenir des lignes")
    return train, validation


def train_model(df: pd.DataFrame, version: str = "model_v001", validation_year: int | None = None) -> ModelBundle:
    train, validation = temporal_split(df, validation_year)
    cols = feature_columns(df)
    base = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, random_state=42)
    estimator = CalibratedClassifierCV(base, method="isotonic", cv=TimeSeriesSplit(n_splits=3))
    estimator.fit(train[cols], train["label_level"].astype(int))

    probabilities = estimator.predict_proba(validation[cols])
    predictions = np.argmax(probabilities, axis=1)
    metrics = {
        "balanced_accuracy": balanced_accuracy_score(validation["label_level"], predictions),
        "classification_report": classification_report(
            validation["label_level"], predictions, output_dict=True, zero_division=0
        ),
        "confusion_matrix": confusion_matrix(validation["label_level"], predictions).tolist(),
    }
    return ModelBundle(version=version, feature_columns=cols, thresholds=(25.0, 50.0, 75.0), estimator=estimator, metrics=metrics)


def predict_frame(bundle: ModelBundle, df: pd.DataFrame) -> pd.DataFrame:
    probabilities = bundle.estimator.predict_proba(df[bundle.feature_columns])
    classes = [VigilanceLevel(int(value)) for value in bundle.estimator.classes_]
    rows = []
    for idx, probs in enumerate(probabilities):
        probability_map = {level: float(prob) for level, prob in zip(classes, probs, strict=True)}
        for level in VigilanceLevel:
            probability_map.setdefault(level, 0.0)
        score = probabilities_to_score(probability_map)
        level = score_to_level(score, bundle.thresholds)
        confidence = round(max(probability_map.values()) * 100.0, 2)
        rows.append(
            {
                "department_code": df.iloc[idx]["department_code"],
                "target_date": df.iloc[idx]["target_date"],
                "horizon": int(df.iloc[idx]["horizon"]),
                "score": score,
                "level": int(level),
                "confidence": confidence,
                "prob_green": probability_map[VigilanceLevel.GREEN],
                "prob_yellow": probability_map[VigilanceLevel.YELLOW],
                "prob_orange": probability_map[VigilanceLevel.ORANGE],
                "prob_red": probability_map[VigilanceLevel.RED],
                "model_version": bundle.version,
            }
        )
    return pd.DataFrame(rows)


def save_bundle(bundle: ModelBundle, model_dir: str | Path) -> Path:
    path = Path(model_dir)
    path.mkdir(parents=True, exist_ok=True)
    output = path / f"{bundle.version}.joblib"
    joblib.dump(bundle, output)
    return output
