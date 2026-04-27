from __future__ import annotations

import io
import json
import math
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps, ImageDraw

from .db import get_conn


def get_today_summary(day: str) -> dict[str, Any]:
    with get_conn() as conn:
        daily = conn.execute("SELECT * FROM daily_logs WHERE date = ?", (day,)).fetchone()
        meals = conn.execute("SELECT * FROM meals WHERE date = ?", (day,)).fetchall()
        thoughts = conn.execute("SELECT * FROM thoughts WHERE date = ?", (day,)).fetchall()
        photos = conn.execute("SELECT * FROM photos WHERE date = ?", (day,)).fetchall()

    return {
        "daily": dict(daily) if daily else None,
        "meals": [dict(row) for row in meals],
        "thoughts": [dict(row) for row in thoughts],
        "photos": [dict(row) for row in photos],
    }


def _range_dates(days: int) -> tuple[str, str]:
    end = datetime.utcnow().date()
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def milestone_report(days: int = 30) -> dict[str, Any]:
    start, end = _range_dates(days)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM daily_logs WHERE date BETWEEN ? AND ? ORDER BY date ASC", (start, end)
        ).fetchall()

    logs = [dict(r) for r in rows]
    if not logs:
        return {"days": days, "start": start, "end": end, "entries": 0}

    weights = [r["weight"] for r in logs if r["weight"] is not None]
    consistency = [r["consistency_score"] or 0 for r in logs]
    workouts = sum(int(r["workout_done"] or 0) for r in logs)

    prediction = None
    if len(weights) >= 4:
        x = np.arange(len(weights))
        y = np.array(weights, dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        future_x = len(weights) + 7
        prediction = float(slope * future_x + intercept)

    plateau = False
    if len(weights) >= 14:
        tail = weights[-14:]
        plateau = max(tail) - min(tail) < 0.4

    return {
        "days": days,
        "start": start,
        "end": end,
        "entries": len(logs),
        "logged_ratio": round((len(logs) / days) * 100, 2),
        "weight_change": round(weights[0] - weights[-1], 2) if len(weights) >= 2 else None,
        "avg_consistency": round(sum(consistency) / len(consistency), 2),
        "workout_days": workouts,
        "plateau_detected": plateau,
        "predicted_weight_7d": round(prediction, 2) if prediction else None,
    }


def generate_montage(days: int = 30) -> bytes:
    start, end = _range_dates(days)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT file_path, date FROM photos WHERE date BETWEEN ? AND ? ORDER BY date ASC", (start, end)
        ).fetchall()

    paths = [Path(r["file_path"]) for r in rows if Path(r["file_path"]).exists()]
    if not paths:
        blank = Image.new("RGB", (1000, 400), color=(22, 22, 22))
        draw = ImageDraw.Draw(blank)
        draw.text((30, 180), "No photos yet - start logging daily selfies", fill=(255, 255, 255))
        buf = io.BytesIO()
        blank.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    thumb_w = 220
    thumb_h = 220
    cols = 4
    rows_count = math.ceil(len(paths) / cols)
    canvas = Image.new("RGB", (cols * (thumb_w + 20) + 20, rows_count * (thumb_h + 40) + 20), (15, 15, 15))

    for idx, (photo_path, row) in enumerate(zip(paths, rows)):
        img = Image.open(photo_path).convert("RGB")
        img = ImageOps.fit(img, (thumb_w, thumb_h), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, thumb_h - 24, thumb_w, thumb_h), fill=(0, 0, 0, 180))
        draw.text((6, thumb_h - 20), row["date"], fill=(255, 255, 255))
        c = idx % cols
        r = idx // cols
        x = 20 + c * (thumb_w + 20)
        y = 20 + r * (thumb_h + 40)
        canvas.paste(img, (x, y))

    out = io.BytesIO()
    canvas.save(out, format="JPEG", quality=90)
    return out.getvalue()


def export_zip() -> bytes:
    with get_conn() as conn:
        daily = [dict(r) for r in conn.execute("SELECT * FROM daily_logs ORDER BY date ASC")]
        meals = [dict(r) for r in conn.execute("SELECT * FROM meals ORDER BY date ASC")]
        thoughts = [dict(r) for r in conn.execute("SELECT * FROM thoughts ORDER BY date ASC")]
        photos = [dict(r) for r in conn.execute("SELECT * FROM photos ORDER BY date ASC")]

    payload = {
        "meta": {
            "schema_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat(),
        },
        "daily_logs": daily,
        "meals": meals,
        "thoughts": thoughts,
        "photos": photos,
    }

    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data.json", json.dumps(payload, indent=2))
        for p in photos:
            fp = Path(p["file_path"])
            if fp.exists():
                zf.write(fp, arcname=f"photos/{fp.name}")

    return zip_bytes.getvalue()
