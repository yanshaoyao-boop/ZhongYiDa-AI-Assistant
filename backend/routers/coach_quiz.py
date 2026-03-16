import asyncio
import io
import json
import os
import random
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from dependencies import User, get_current_user, has_permission

router = APIRouter(prefix="/coach-quiz", tags=["coach-quiz"])

QUIZ_BANK_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "coach_quiz_bank.json",
)

_quiz_bank_lock = asyncio.Lock()

HEADER_ALIASES = {
    "question": "question",
    "题目": "question",
    "题干": "question",
    "optiona": "option_a",
    "选项a": "option_a",
    "a": "option_a",
    "optionb": "option_b",
    "选项b": "option_b",
    "b": "option_b",
    "optionc": "option_c",
    "选项c": "option_c",
    "c": "option_c",
    "optiond": "option_d",
    "选项d": "option_d",
    "d": "option_d",
    "answer": "answer",
    "答案": "answer",
    "正确答案": "answer",
    "explanation": "explanation",
    "解析": "explanation",
    "category": "category",
    "分类": "category",
    "科目": "category",
}

REQUIRED_COLUMNS = ["question", "option_a", "option_b", "option_c", "option_d", "answer"]


def _normalize_header(value):
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _canonicalize_columns(columns):
    mapping = {}
    for column in columns:
        normalized = _normalize_header(column)
        mapping[column] = HEADER_ALIASES.get(normalized, normalized)
    return mapping


def _ensure_quiz_bank_dir():
    os.makedirs(os.path.dirname(QUIZ_BANK_FILE), exist_ok=True)


def _load_quiz_bank():
    if not os.path.exists(QUIZ_BANK_FILE):
        return []
    with open(QUIZ_BANK_FILE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_quiz_bank(questions):
    _ensure_quiz_bank_dir()
    with open(QUIZ_BANK_FILE, "w", encoding="utf-8") as handle:
        json.dump(questions, handle, ensure_ascii=False, indent=2)


def _normalize_answer(answer):
    raw = str(answer or "").strip().upper()
    if raw in {"A", "B", "C", "D"}:
        return raw
    aliases = {
        "OPTION_A": "A",
        "OPTION_B": "B",
        "OPTION_C": "C",
        "OPTION_D": "D",
        "选项A": "A",
        "选项B": "B",
        "选项C": "C",
        "选项D": "D",
    }
    return aliases.get(raw, raw)


def _read_dataframe(filename, content):
    lower_name = (filename or "").lower()
    buffer = io.BytesIO(content)
    if lower_name.endswith(".csv"):
        return pd.read_csv(buffer)
    if lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
        return pd.read_excel(buffer)
    raise HTTPException(status_code=400, detail="Only csv/xls/xlsx quiz banks are supported")


def _parse_questions(filename, content):
    frame = _read_dataframe(filename, content)
    if frame.empty:
        raise HTTPException(status_code=400, detail="Quiz bank file is empty")

    frame = frame.rename(columns=_canonicalize_columns(frame.columns))
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing)}")

    questions = []
    for _, row in frame.fillna("").iterrows():
        question = str(row.get("question", "")).strip()
        if not question:
            continue

        answer = _normalize_answer(row.get("answer", ""))
        if answer not in {"A", "B", "C", "D"}:
            raise HTTPException(status_code=400, detail=f"Invalid answer for question: {question}")

        questions.append(
            {
                "id": uuid.uuid4().hex[:10],
                "question": question,
                "options": [
                    {"key": "A", "text": str(row.get("option_a", "")).strip()},
                    {"key": "B", "text": str(row.get("option_b", "")).strip()},
                    {"key": "C", "text": str(row.get("option_c", "")).strip()},
                    {"key": "D", "text": str(row.get("option_d", "")).strip()},
                ],
                "answer": answer,
                "explanation": str(row.get("explanation", "")).strip(),
                "category": str(row.get("category", "")).strip(),
            }
        )

    if not questions:
        raise HTTPException(status_code=400, detail="No valid questions found in quiz bank file")

    return questions


@router.post("/bank")
async def upload_quiz_bank(
    file: UploadFile = File(...),
    admin: User = Depends(has_permission("edit_cases")),
):
    del admin
    content = await file.read()
    questions = _parse_questions(file.filename, content)

    async with _quiz_bank_lock:
        existing = _load_quiz_bank()
        merged = questions + existing
        _save_quiz_bank(merged)

    return {
        "status": "success",
        "imported_count": len(questions),
        "total_questions": len(merged),
        "filename": file.filename,
    }


@router.get("/bank")
async def list_quiz_bank(admin: User = Depends(has_permission("edit_cases"))):
    del admin
    questions = _load_quiz_bank()
    return {"questions": questions, "total_questions": len(questions)}


@router.delete("/bank/{question_id}")
async def delete_quiz_question(
    question_id: str,
    admin: User = Depends(has_permission("edit_cases")),
):
    del admin
    async with _quiz_bank_lock:
        questions = _load_quiz_bank()
        updated = [item for item in questions if item.get("id") != question_id]
        _save_quiz_bank(updated)

    return {"status": "success", "total_questions": len(updated)}


@router.get("/session")
async def get_quiz_session(
    count: int = Query(5, ge=1, le=20),
    user: User = Depends(get_current_user),
):
    del user
    questions = _load_quiz_bank()
    if not questions:
        return {"questions": [], "question_count": 0}

    sample_size = min(count, len(questions))
    sampled = random.sample(questions, sample_size)
    return {"questions": sampled, "question_count": len(sampled)}
