import re


SEARCHABLE_WAREHOUSE_CODE_TOKEN = r"(?:[A-Z]{2,5}\d+[A-Z]?|IU[A-Z]{2}|VANE)"
SEARCHABLE_WAREHOUSE_CODE_PATTERN = re.compile(rf"^{SEARCHABLE_WAREHOUSE_CODE_TOKEN}$")
SEARCHABLE_WAREHOUSE_CODE_FINDER = re.compile(SEARCHABLE_WAREHOUSE_CODE_TOKEN)
SEARCHABLE_WAREHOUSE_CODE_QUERY_PATTERN = re.compile(
    rf"(?<![A-Z0-9]){SEARCHABLE_WAREHOUSE_CODE_TOKEN}(?![A-Z0-9])",
    re.IGNORECASE,
)


def extract_searchable_warehouse_codes(raw_value: str | None) -> list[str]:
    raw_text = str(raw_value or "").upper()
    if not raw_text:
        return []

    codes: list[str] = []
    seen: set[str] = set()
    for part in re.split(r"[/,\s\u3001\uFF0C]+", raw_text):
        token = part.strip()
        if not token:
            continue
        token = re.sub(r"[\(\uff08].*?[\)\uff09]", "", token).strip()
        if not token:
            continue

        if SEARCHABLE_WAREHOUSE_CODE_PATTERN.match(token):
            if token not in seen:
                seen.add(token)
                codes.append(token)
            continue

        for match in SEARCHABLE_WAREHOUSE_CODE_FINDER.findall(token):
            if match not in seen:
                seen.add(match)
                codes.append(match)

    return codes
