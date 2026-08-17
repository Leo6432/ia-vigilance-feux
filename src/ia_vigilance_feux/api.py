from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ia_vigilance_feux.departments import DEPARTMENTS

app = FastAPI(
    title="IA Vigilance Feux",
    version="0.1.0",
    description="API de predictions IA de vigilance feux de foret. Les resultats ne sont pas une vigilance officielle.",
)

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_INDEX = ROOT_DIR / "frontend" / "index.html"
PREDICTIONS_FILE = Path("data/predictions/latest.csv")
PERFORMANCE_FILE = Path("data/model_registry/current_metrics.json")


class TrainingRequest(BaseModel):
    features_path: str = "data/processed/features.csv"
    train_end_year: int
    test_year: int
    version: str = "model_v001"


TRAINING_STATUS: dict[str, Any] = {"state": "idle", "message": "Aucun entrainement lance"}


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=404, detail="Interface frontend introuvable")
    return FileResponse(FRONTEND_INDEX)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
    path = Path(f"data/history/{department_code}.csv")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Historique absent: importer des donnees reelles d'abord")
    return pd.read_csv(path).to_dict(orient="records")


@app.get("/model/performance")
def model_performance() -> dict[str, Any]:
    if not PERFORMANCE_FILE.exists():
        raise HTTPException(status_code=404, detail="Aucune metrique de modele disponible")
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
    if not PREDICTIONS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Aucune prediction IA disponible: executer le pipeline avec des donnees reelles",
        )
    return pd.read_csv(PREDICTIONS_FILE)
