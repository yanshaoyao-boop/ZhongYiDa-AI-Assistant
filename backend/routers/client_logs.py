import json
import os
from datetime import datetime, timezone
from typing import Any

import aiofiles
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/client-logs", tags=["client-logs"])

CLIENT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "logs")
CLIENT_LOG_FILE = os.path.join(CLIENT_LOG_DIR, "client-logs.jsonl")


class ClientLogEntry(BaseModel):
    level: str = "error"
    type: str = "app-error"
    message: str = Field(min_length=1)
    page: str | None = None
    context: dict[str, Any] | None = None
    timestamp: str | None = None


class ClientLogBatch(BaseModel):
    entries: list[ClientLogEntry]


def _normalize_entry(entry: ClientLogEntry):
    payload = entry.model_dump()
    payload["timestamp"] = payload["timestamp"] or datetime.now(timezone.utc).isoformat()
    return payload


@router.post("")
async def ingest_client_logs(batch: ClientLogBatch):
    if not batch.entries:
        raise HTTPException(status_code=400, detail="Log batch cannot be empty.")

    os.makedirs(CLIENT_LOG_DIR, exist_ok=True)

    async with aiofiles.open(CLIENT_LOG_FILE, "a", encoding="utf-8") as handle:
        for entry in batch.entries:
            await handle.write(json.dumps(_normalize_entry(entry), ensure_ascii=False) + "\n")

    return {"status": "ok", "accepted": len(batch.entries)}
