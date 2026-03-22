import json


def format_sse_content_event(content: str) -> str:
    payload = json.dumps({"content": content}, ensure_ascii=False, separators=(",", ":"))
    return f"data: {payload}\n\n"


def format_sse_done_event() -> str:
    return "data: [DONE]\n\n"
