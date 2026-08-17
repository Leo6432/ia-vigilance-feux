from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ia_vigilance_feux.departments import DEPARTMENTS

app = FastAPI(
    title="IA Vigilance Feux",
    version="0.2.0",
    description="API de predictions IA de vigilance feux de foret. Les resultats ne sont pas une vigilance officielle.",
)

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_INDEX = ROOT_DIR / "frontend" / "index.html"
PREDICTIONS_FILE = ROOT_DIR / "data" / "predictions" / "latest.csv"
PERFORMANCE_FILE = ROOT_DIR / "data" / "model_registry" / "current_metrics.json"
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in {"1", "true", "yes", "on"}
LEVEL_LABELS = {0: "Vert", 1: "Jaune", 2: "Orange", 3: "Rouge"}


class TrainingRequest(BaseModel):
    features_path: str = "data/processed/features.csv"
    train_end_year: int
    test_year: int
    version: str = "model_v001"


TRAINING_STATUS: dict[str, Any] = {
    "state": "idle",
    "message": "Aucun entrainement lance",
    "demo_mode": DEMO_MODE,
}


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=404, detail="Interface frontend introuvable")
    return FileResponse(FRONTEND_INDEX)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "demo_mode": DEMO_MODE, "departments": len(DEPARTMENTS)}


@app.get("/departments")
def departments() -> list[dict[str, str]]:
    return DEPARTMENTS


@app.get("/forecast")
def forecast(target_date: date | None = Query(default=None)) -> list[dict[str, Any]]:
    df = _load_predictions()
    if target_date is not None:
        df = df[pd.to_datetime(df["target_date"]).dt.date == target_date]
    return df.to_dict(orient="records")


@app.get("/forecast/{department_code}")
def forecast_department(department_code: str) -> list[dict[str, Any]]:
    df = _load_predictions()
    result = df[df["department_code"].astype(str) == department_code]
    if result.empty:
        raise HTTPException(status_code=404, detail="Aucune prediction IA disponible pour ce departement")
    return result.to_dict(orient="records")


@app.get("/history/{department_code}")
def history_department(department_code: str) -> list[dict[str, Any]]:
    path = ROOT_DIR / "data" / "history" / f"{department_code}.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Historique absent: importer des donnees reelles d'abord")
    return pd.read_csv(path).to_dict(orient="records")


@app.get("/model/performance")
def model_performance() -> dict[str, Any]:
    if not PERFORMANCE_FILE.exists():
        return {
            "status": "demo" if DEMO_MODE else "not_trained",
            "message": "Aucun modele entraine. Les predictions affichees sont deterministes et uniquement destinees a la demonstration."
            if DEMO_MODE
            else "Aucune metrique de modele disponible",
            "official": False,
        }
    return pd.read_json(PERFORMANCE_FILE, typ="series").to_dict()


@app.post("/training/start")
def training_start(request: TrainingRequest) -> dict[str, Any]:
    TRAINING_STATUS.update(
        {
            "state": "queued",
            "message": "Lancement manuel requis via CLI pour eviter un entrainement long dans le worker API",
            "request": request.model_dump(),
        }
    )
    return TRAINING_STATUS


@app.get("/training/status")
def training_status() -> dict[str, Any]:
    return TRAINING_STATUS


@app.get("/training/results")
def training_results() -> dict[str, Any]:
    return model_performance()


def _load_predictions() -> pd.DataFrame:
    if PREDICTIONS_FILE.exists():
        return pd.read_csv(PREDICTIONS_FILE)
    if DEMO_MODE:
        return _demo_predictions()
    raise HTTPException(
        status_code=404,
        detail="Aucune prediction IA disponible: executer le pipeline avec des donnees reelles",
    )


def _demo_predictions() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    today = date.today()
    for index, department in enumerate(DEPARTMENTS):
        code = str(department["code"])
        numeric_code = sum(ord(char) for char in code)
        for horizon in range(8):
            wave = (numeric_code * 7 + horizon * 13 + index * 3) % 101
            score = round(min(99, max(4, 18 + wave * 0.72 + horizon * 1.8)), 1)
            if score >= 76:
                level = 3
            elif score >= 54:
                level = 2
            elif score >= 30:
                level = 1
            else:
                level = 0
            raw = {
                0: max(0.03, 1.0 - score / 100),
                1: max(0.03, (score - 8) / 180),
                2: max(0.02, (score - 25) / 150),
                3: max(0.01, (score - 55) / 130),
            }
            total = sum(raw.values())
            probabilities = {level_key: round(value / total, 4) for level_key, value in raw.items()}
            probabilities[level] = max(probabilities[level], 0.42)
            probability_total = sum(probabilities.values())
            probabilities = {key: round(value / probability_total, 4) for key, value in probabilities.items()}
            rows.append(
                {
                    "department_code": code,
                    "target_date": (today + timedelta(days=horizon)).isoformat(),
                    "horizon": horizon,
                    "level": level,
                    "level_label": LEVEL_LABELS[level],
                    "score": score,
                    "confidence": round(max(probabilities.values()) * 100, 1),
                    "prob_green": probabilities[0],
                    "prob_yellow": probabilities[1],
                    "prob_orange": probabilities[2],
                    "prob_red": probabilities[3],
                    "model_version": "demo-v0",
                    "demo": True,
                    "source": "donnees deterministes de demonstration",
                }
            )
    return pd.DataFrame(rows)
