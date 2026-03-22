def serialize_public_settings(settings: dict[str, str]) -> dict[str, str]:
    payload = dict(settings)
    welcome_message = payload.get("ai_welcome_message") or payload.get("welcome_message") or ""
    if welcome_message:
        payload["welcome_message"] = welcome_message
        payload["ai_welcome_message"] = welcome_message
    return payload
