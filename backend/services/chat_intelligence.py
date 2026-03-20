import re
from typing import Iterable


COMPANY_INTRO_EXPANSION = "公司简介 发展历程 核心业务 企业文化 优势特色"
AMBIGUOUS_FOLLOW_UPS = {
    "这个",
    "这个呢",
    "那个",
    "那个呢",
    "还有呢",
    "然后呢",
    "展开下",
    "细说",
    "细说下",
    "继续",
}

SIGNAL_KEYWORDS = (
    "报价",
    "价格",
    "偏远",
    "轨迹",
    "单号",
    "仓库",
    "公司",
    "介绍",
    "简介",
    "制度",
    "流程",
    "考勤",
    "请假",
    "迟到",
    "SOP",
)
QUOTE_HINT_KEYWORDS = ("报价", "价格", "多少钱", "费用", "卖价", "单价", "运费")
ADDRESS_HINT_KEYWORDS = ("偏远", "地址", "邮编", "仓库", "送吗", "哪里")
REGION_KEYWORDS = ("美东", "美中", "美西", "欧洲", "英国", "加拿大", "澳洲", "华东", "华南")
WH_CODE_PATTERN = re.compile(r"[A-Z]{3,4}\d+[A-Z]?", re.IGNORECASE)
ZIP_CODE_PATTERN = re.compile(r"(?<!\d)\d{5}(?!\d)")
WEIGHT_VOLUME_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*(?:kg|公斤|cbm|方|立方)", re.IGNORECASE)
ADMIN_KNOWLEDGE_KEYWORDS = (
    "考勤",
    "请假",
    "报销",
    "工资",
    "绩效",
    "人事",
    "制度",
    "晋升",
    "调休",
)
BUSINESS_KNOWLEDGE_KEYWORDS = (
    "物流",
    "报价",
    "仓库",
    "SOP",
    "话术",
    "渠道",
    "轨迹",
    "偏远",
    "操作流程",
)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _recent_user_messages(history: list[dict] | None, limit: int = 2) -> list[str]:
    messages = []
    for item in reversed(history or []):
        if item.get("role") != "user":
            continue
        content = _normalize_text(item.get("content", ""))
        if not content:
            continue
        messages.append(content)
        if len(messages) == limit:
            break
    return messages


def _has_quote_core_fields(text: str) -> bool:
    normalized = _normalize_text(text)
    return bool(
        WH_CODE_PATTERN.search(normalized)
        or WEIGHT_VOLUME_PATTERN.search(normalized)
        or any(keyword in normalized for keyword in REGION_KEYWORDS)
    )


def _has_address_target(text: str) -> bool:
    normalized = _normalize_text(text)
    return bool(
        WH_CODE_PATTERN.search(normalized)
        or ZIP_CODE_PATTERN.search(normalized)
        or len(normalized) >= 10
    )


def infer_knowledge_category(message: str) -> str | None:
    normalized = _normalize_text(message)
    admin_score = sum(1 for keyword in ADMIN_KNOWLEDGE_KEYWORDS if keyword in normalized)
    biz_score = sum(1 for keyword in BUSINESS_KNOWLEDGE_KEYWORDS if keyword.lower() in normalized.lower())

    if admin_score == 0 and biz_score == 0:
        return None
    if admin_score > biz_score:
        return "admin"
    if biz_score > admin_score:
        return "biz"
    return None


def build_document_search_query(
    message: str,
    history: list[dict] | None,
    company_intro_keywords: list[str] | tuple[str, ...],
) -> str:
    current_message = _normalize_text(message)
    recent_user_context = []

    if len(current_message) <= 18 and history:
        for item in reversed(history):
            if item.get("role") != "user":
                continue
            content = _normalize_text(item.get("content", ""))
            if not content or content == current_message:
                continue
            recent_user_context.append(content)
            if len(recent_user_context) == 2:
                break

    recent_user_context.reverse()
    segments = _dedupe_keep_order(recent_user_context + [current_message])
    search_query = " ".join(segments)

    if len(current_message) < 15 and any(keyword in current_message for keyword in company_intro_keywords):
        search_query = f"{search_query} {COMPANY_INTRO_EXPANSION}".strip()

    return search_query


def _extract_query_terms(query: str) -> list[str]:
    normalized = _normalize_text(query)
    ascii_terms = re.findall(r"[A-Za-z0-9_]+", normalized.lower())
    chinese_terms = [
        token
        for token in re.split(r"[\s,.;:!?/\\|]+", normalized)
        if token and any("\u4e00" <= ch <= "\u9fff" for ch in token)
    ]
    chinese_ngrams = []
    for token in chinese_terms:
        condensed = "".join(ch for ch in token if "\u4e00" <= ch <= "\u9fff")
        if len(condensed) >= 2:
            chinese_ngrams.extend(condensed[i : i + 2] for i in range(len(condensed) - 1))
    return _dedupe_keep_order(ascii_terms + chinese_terms + chinese_ngrams)


def rerank_similar_documents(query: str, documents: list[dict] | None) -> list[dict]:
    docs = list(documents or [])
    query_terms = _extract_query_terms(query)

    def score(doc: dict, index: int) -> tuple[float, float, int]:
        metadata = doc.get("metadata") or {}
        source = str(metadata.get("source", ""))
        category = str(metadata.get("category", ""))
        content = f"{doc.get('document', '')} {source} {category}".lower()
        keyword_hits = sum(1 for term in query_terms if term.lower() in content)
        distance = float(doc.get("distance", 1.0))
        return (keyword_hits, -distance, -index)

    ranked = sorted(docs, key=lambda doc_with_index: score(doc_with_index, docs.index(doc_with_index)), reverse=True)
    return ranked


def summarize_document_sources(documents: list[dict] | None, limit: int = 3) -> str:
    sources = []
    for doc in documents or []:
        metadata = doc.get("metadata") or {}
        source = _normalize_text(str(metadata.get("source", ""))) or "未知文档"
        sources.append(source)
    unique_sources = _dedupe_keep_order(sources)
    return "、".join(unique_sources[:limit])


def build_document_source_footer(documents: list[dict] | None, limit: int = 3) -> str:
    source_summary = summarize_document_sources(documents, limit=limit)
    if not source_summary:
        return ""
    return f"\n\n参考来源：{source_summary}"


def build_document_clarification_message() -> str:
    return "我还不能准确判断你要查哪类内部资料。请补充一下你想查的主题，比如考勤制度、请假流程、报价表或仓库流程。"


def should_ask_quote_clarification(message: str, history: list[dict] | None) -> bool:
    current_message = _normalize_text(message)
    if not current_message:
        return False
    if _has_quote_core_fields(current_message):
        return False
    if any(_has_quote_core_fields(item) for item in _recent_user_messages(history)):
        return False
    if current_message in AMBIGUOUS_FOLLOW_UPS:
        return True
    return any(keyword in current_message for keyword in QUOTE_HINT_KEYWORDS) and len(current_message) <= 20


def should_ask_address_clarification(message: str, history: list[dict] | None) -> bool:
    current_message = _normalize_text(message)
    if not current_message:
        return False
    if _has_address_target(current_message):
        return False
    if any(_has_address_target(item) for item in _recent_user_messages(history)):
        return False
    if current_message in AMBIGUOUS_FOLLOW_UPS:
        return True
    return any(keyword in current_message for keyword in ADDRESS_HINT_KEYWORDS) and len(current_message) <= 12


def build_intent_clarification_message(intent: str, message: str, history: list[dict] | None) -> str:
    if intent == "document" and should_ask_document_clarification(message, history):
        return build_document_clarification_message()
    if intent == "quote" and should_ask_quote_clarification(message, history):
        return "为了给你报准一点，请补充一下仓库代码或区域，以及货物重量/体积。我拿到这些关键信息后再给你报价。"
    if intent == "address" and should_ask_address_clarification(message, history):
        return "我先帮你查，但还需要你补充一个明确目标：邮编、仓库代码，或完整地址三选一发我就行。"
    return ""


def should_ask_document_clarification(message: str, history: list[dict] | None) -> bool:
    current_message = _normalize_text(message)
    if not current_message or len(current_message) > 8:
        return False

    if current_message not in AMBIGUOUS_FOLLOW_UPS:
        return False

    recent_user_messages = []
    for item in reversed(history or []):
        if item.get("role") != "user":
            continue
        content = _normalize_text(item.get("content", ""))
        if not content or content == current_message:
            continue
        recent_user_messages.append(content)
        if len(recent_user_messages) == 2:
            break

    if not recent_user_messages:
        return True

    return not any(any(keyword in content for keyword in SIGNAL_KEYWORDS) for content in recent_user_messages)
