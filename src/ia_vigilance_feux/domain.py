from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import IntEnum


class VigilanceLevel(IntEnum):
    GREEN = 0
    YELLOW = 1
    ORANGE = 2
    RED = 3

    @property
    def label(self) -> str:
        return {
            VigilanceLevel.GREEN: "Vert",
            VigilanceLevel.YELLOW: "Jaune",
            VigilanceLevel.ORANGE: "Orange",
            VigilanceLevel.RED: "Rouge",
        }[self]


DEFAULT_THRESHOLDS = (25.0, 50.0, 75.0)


def score_to_level(score: float, thresholds: tuple[float, float, float] = DEFAULT_THRESHOLDS) -> VigilanceLevel:
    yellow, orange, red = thresholds
    if score >= red:
        return VigilanceLevel.RED
    if score >= orange:
        return VigilanceLevel.ORANGE
    if score >= yellow:
        return VigilanceLevel.YELLOW
    return VigilanceLevel.GREEN


def probabilities_to_score(probabilities: dict[VigilanceLevel, float]) -> float:
    weighted = sum(level.value * probability for level, probability in probabilities.items())
    return round((weighted / 3.0) * 100.0, 2)


@dataclass(frozen=True)
class Prediction:
    department_code: str
    target_date: date
    horizon: int
    available_at: datetime
    score: float
    level: VigilanceLevel
    probabilities: dict[VigilanceLevel, float]
    confidence: float
    model_version: str
