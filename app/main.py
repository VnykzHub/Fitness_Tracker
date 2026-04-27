from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .db import get_conn, init_db
from .schemas import DailyLogRequest, MealLogRequest, ThoughtRequest
from .services import export_zip, generate_montage, get_today_summary, milestone_report

app = FastAPI(title="Phone-First Fat Loss Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path("data/photos").mkdir(parents=True, exist_ok=True)
init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/log/today")
def log_today(payload: DailyLogRequest) -> dict[str, str]:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO daily_logs(date, weight, calories, protein, workout_done, consistency_score, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
            weight = excluded.weight,
            calories = excluded.calories,
            protein = excluded.protein,
            workout_done = excluded.workout_done,
            consistency_score = excluded.consistency_score,
            notes = excluded.notes
            """,
            (
                payload.date.isoformat(),
                payload.weight,
                payload.calories,
                payload.protein,
                int(payload.workout_done),
                payload.consistency_score,
                payload.notes,
            ),
        )
    return {"message": "daily log saved"}


@app.post("/api/log/meal")
def log_meal(payload: MealLogRequest) -> dict[str, str]:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO meals(date, meal_name, calories, protein, source) VALUES (?, ?, ?, ?, ?)",
            (
                payload.date.isoformat(),
                payload.meal_name,
                payload.calories,
                payload.protein,
                payload.source,
            ),
        )
    return {"message": "meal logged"}


@app.post("/api/log/thought")
def log_thought(payload: ThoughtRequest) -> dict[str, str]:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO thoughts(date, text) VALUES (?, ?)",
            (payload.date.isoformat(), payload.text),
        )
    return {"message": "thought saved"}


@app.post("/api/log/photo")
async def log_photo(
    date_value: date = Form(...),
    caption: str | None = Form(default=None),
    photo: UploadFile = File(...),
) -> dict[str, str]:
    suffix = Path(photo.filename).suffix or ".jpg"
    file_path = Path("data/photos") / f"{date_value.isoformat()}_{uuid4().hex}{suffix}"
    content = await photo.read()
    file_path.write_bytes(content)

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO photos(date, file_path, caption) VALUES (?, ?, ?)",
            (date_value.isoformat(), str(file_path), caption),
        )

    return {"message": "photo logged", "path": str(file_path)}


@app.get("/api/summary/today")
def summary_today(day: date | None = None) -> dict:
    lookup = (day or date.today()).isoformat()
    return get_today_summary(lookup)


@app.get("/api/milestone")
def milestone(days: int = 30) -> dict:
    return milestone_report(days=days)


@app.get("/api/montage")
def montage(days: int = 30) -> Response:
    image_bytes = generate_montage(days)
    return Response(content=image_bytes, media_type="image/jpeg")


@app.get("/api/export")
def export_all() -> Response:
    payload = export_zip()
    headers = {"Content-Disposition": "attachment; filename=fatloss_export.zip"}
    return Response(content=payload, media_type="application/zip", headers=headers)


app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/dashboard")
def dashboard() -> FileResponse:
    return FileResponse("static/index.html")
