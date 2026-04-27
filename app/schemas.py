from __future__ import annotations

from datetime import date
from pydantic import BaseModel, Field


class DailyLogRequest(BaseModel):
    date: date
    weight: float | None = None
    calories: int = 0
    protein: int = 0
    workout_done: bool = False
    consistency_score: float = Field(default=0.0, ge=0.0, le=100.0)
    notes: str | None = None


class MealLogRequest(BaseModel):
    date: date
    meal_name: str
    calories: int = 0
    protein: int = 0
    source: str = "manual"


class ThoughtRequest(BaseModel):
    date: date
    text: str
