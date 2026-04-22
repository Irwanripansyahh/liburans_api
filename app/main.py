from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from .storage import load_holidays_payload

app = FastAPI(title="Hari Libur API", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}


def _get_year_payload(year: int) -> dict[str, Any]:
    try:
        return load_holidays_payload(year)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Data tahun {year} belum tersedia")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/holidays")
def get_holidays(year: int = Query(..., ge=1900, le=2100)) -> dict[str, Any]:
    return _get_year_payload(year)


@app.get("/holidays/{year}")
def get_holidays_by_path(year: int) -> dict[str, Any]:
    return get_holidays(year=year)
