import re
from typing import Iterable


COMPANY_INTRO_EXPANSION = "公司简介 发展历程 核心业务 企业文化 优势特色"
COMPANY_CULTURE_EXPANSION = "完整企业文化 当前生效 企业文化 公司文化 文化理念 使命 愿景 价值观"
ASSISTANT_CAPABILITY_QUERY_MARKERS = (
    "你能做什么",
    "你会什么",
    "你能帮我做什么",
    "怎么用",
    "如何使用",
    "正确的使用",
    "用法",
    "功能",
    "操作说明",
    "使用指南",
    "自我介绍",
)
ASSISTANT_CAPABILITY_EXPANSION = "小易 使用指南 操作说明 自我介绍 功能说明 核心能力 助手赋能 白皮书"
AMBIGUOUS_FOLLOW_UPS = {
    "这个",
    "这个吗",
    "那个",
    "那个吗",
    "还有吗",
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
ADMIN_ROLE_LOOKUP_KEYWORDS = (
    "职位",
    "职务",
    "岗位",
    "找谁",
    "对接",
    "负责人",
    "谁负责",
    "电话",
    "微信",
    "联系方式",
    "负责什么",
)
ADMIN_ROLE_DIRECTORY_EXPANSION = "行政部门 岗位职责 对接人 负责人 职位 职务 联系方式"
ADMIN_ATTENDANCE_EXPANSION = "考勤制度 迟到 早退 漏打卡 未打卡 扣款 满勤 旷工 请假 薪酬 管理制度"
ADMIN_REIMBURSEMENT_EXPANSION = "费用报销 报销制度 报销标准 报销流程 发票 审批 时效"
ADMIN_FINANCE_INFO_EXPANSION = "银行账号 账户号码 开户银行 开户行 开票信息 联行号 统一信用代码 信用代码"
ADMIN_WAREHOUSE_ADDRESS_EXPANSION = "仓库地址 仓库位置 收货地址 海外仓地址 义乌仓 泉州仓 厦门仓 东莞凤岗仓 福永仓 美西海外仓 美东海外仓"
ORDER_SHEET_ROUTING_EXPANSION = "下单表 修改 下单表内容变更 对接人 客服主管 行政部门 岗位职责 联系方式"
EXECUTIVE_PROFILE_EXPANSION = "集团简介 组织架构 高管 董事长 法人 核心管理层"
COMPANY_CULTURE_KEYWORDS = (
    "企业文化",
    "公司文化",
    "文化理念",
    "使命",
    "愿景",
    "价值观",
)
QUOTE_HINT_KEYWORDS = ("报价", "价格", "多少钱", "费用", "卖价", "单价", "运费")
ADDRESS_HINT_KEYWORDS = ("偏远", "地址", "邮编", "仓库", "送吗", "哪里")
REGION_KEYWORDS = ("美东", "美中", "美西", "欧洲", "英国", "加拿大", "澳洲", "华东", "华南")
WH_CODE_PATTERN = re.compile(r"[A-Z]{3,4}\d+[A-Z]?", re.IGNORECASE)
ZIP_CODE_PATTERN = re.compile(r"(?<!\d)\d{5}(?!\d)")
WEIGHT_VOLUME_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*(?:kg|公斤|cbm|方|立方)", re.IGNORECASE)
TYPO_CANONICAL_MAP = {
    "婚嫁": "婚假",
    "婚价": "婚假",
}
ADMIN_KNOWLEDGE_KEYWORDS = (
    "考勤",
    "迟到",
    "早退",
    "未打卡",
    "漏打卡",
    "扣款",
    "满勤",
    "旷工",
    "请假",
    "报销",
    "工资",
    "薪资",
    "薪酬",
    "绩效",
    "人事",
    "制度",
    "晋升",
    "调休",
    "银行",
    "银行账号",
    "账号",
    "账户",
    "账户号码",
    "开户行",
    "开户银行",
    "开票",
    "开票信息",
    "联行号",
    "统一信用代码",
    "信用代码",
    "仓库地址",
    "仓库位置",
    "收货地址",
    "海外仓地址",
    *COMPANY_CULTURE_KEYWORDS,
    *ADMIN_ROLE_LOOKUP_KEYWORDS,
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
ADMIN_ATTENDANCE_KEYWORDS = (
    "考勤",
    "迟到",
    "早退",
    "未打卡",
    "漏打卡",
    "满勤",
    "旷工",
    "请假",
    "婚假",
    "调休",
)
ADMIN_REIMBURSEMENT_KEYWORDS = (
    "报销",
    "费用",
    "发票",
    "审批",
)
ADMIN_FINANCE_INFO_KEYWORDS = (
    "银行",
    "银行账号",
    "账号",
    "账户",
    "账户号码",
    "开户行",
    "开户银行",
    "开票",
    "开票信息",
    "联行号",
    "统一信用代码",
    "信用代码",
)
ADMIN_WAREHOUSE_ADDRESS_KEYWORDS = (
    "仓库地址",
    "仓库位置",
    "收货地址",
    "海外仓地址",
)
ORDER_SHEET_ROUTING_KEYWORDS = (
    "下单表",
    "改下单表",
    "改单",
    "改单表",
    "账单",
    "改账单",
    "修改账单",
    "修改下单",
    "改单找谁",
    "改下单找谁",
)
EXECUTIVE_PROFILE_KEYWORDS = (
    "董事长",
    "法人",
    "高管",
    "老板是谁",
    "公司谁负责",
    "集团负责人",
)


def _normalize_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    for typo, canonical in TYPO_CANONICAL_MAP.items():
        normalized = normalized.replace(typo, canonical)
    return normalized


def _is_chinese_fragment(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _distance_lte_one(a: str, b: str) -> bool:
    """Fast check for edit distance <= 1 (substitute/insert/delete)."""
    if a == b:
        return True
    la = len(a)
    lb = len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        mismatches = 0
        for ca, cb in zip(a, b):
            if ca != cb:
                mismatches += 1
                if mismatches > 1:
                    return False
        return mismatches == 1

    if la > lb:
        a, b = b, a
        la, lb = lb, la

    i = 0
    j = 0
    mismatch_used = False
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1
            j += 1
            continue
        if mismatch_used:
            return False
        mismatch_used = True
        j += 1
    return True


def _fuzzy_term_keyword_match(term: str, keyword: str) -> bool:
    if term == keyword:
        return True
    if len(term) < 2 or len(keyword) < 2:
        return False
    if max(len(term), len(keyword)) > 4:
        return False
    # Fuzzy mode is only for short Chinese fragments (e.g. ?? -> ??).
    if not _is_chinese_fragment(term) or not _is_chinese_fragment(keyword):
        return False
    return _distance_lte_one(term, keyword)


def _keyword_in_text(text: str, keyword: str, query_terms: list[str]) -> bool:
    if keyword in text:
        return True
    return any(_fuzzy_term_keyword_match(term, keyword) for term in query_terms)


def _count_keyword_matches(text: str, keywords: tuple[str, ...]) -> int:
    query_terms = _extract_query_terms(text)
    return sum(1 for keyword in keywords if _keyword_in_text(text, keyword, query_terms))


def _count_direct_keyword_matches(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


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
    if _count_keyword_matches(normalized, COMPANY_CULTURE_KEYWORDS) > 0:
        return "admin"

    if _count_keyword_matches(normalized, ADMIN_ROLE_LOOKUP_KEYWORDS) > 0:
        return "admin"

    admin_score = _count_keyword_matches(normalized, ADMIN_KNOWLEDGE_KEYWORDS)
    biz_score = _count_keyword_matches(normalized, BUSINESS_KNOWLEDGE_KEYWORDS)
    if _count_keyword_matches(normalized, ADMIN_FINANCE_INFO_KEYWORDS) > 0:
        admin_score += 3
    if (
        _count_keyword_matches(normalized, ADMIN_WAREHOUSE_ADDRESS_KEYWORDS) > 0
        or ("仓库" in normalized and "地址" in normalized)
    ):
        admin_score += 2

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

    if _count_keyword_matches(current_message, COMPANY_CULTURE_KEYWORDS) > 0:
        search_query = f"{search_query} {COMPANY_CULTURE_EXPANSION}".strip()

    if any(keyword in current_message for keyword in ASSISTANT_CAPABILITY_QUERY_MARKERS):
        search_query = f"{search_query} {ASSISTANT_CAPABILITY_EXPANSION}".strip()

    if _count_keyword_matches(current_message, ADMIN_ROLE_LOOKUP_KEYWORDS) > 0:
        search_query = f"{search_query} {ADMIN_ROLE_DIRECTORY_EXPANSION}".strip()

    if _count_keyword_matches(current_message, ADMIN_REIMBURSEMENT_KEYWORDS) > 0:
        search_query = f"{search_query} {ADMIN_REIMBURSEMENT_EXPANSION}".strip()
    elif _count_keyword_matches(current_message, ADMIN_ATTENDANCE_KEYWORDS) > 0:
        search_query = f"{search_query} {ADMIN_ATTENDANCE_EXPANSION}".strip()

    if _count_keyword_matches(current_message, ADMIN_FINANCE_INFO_KEYWORDS) > 0:
        search_query = f"{search_query} {ADMIN_FINANCE_INFO_EXPANSION}".strip()

    if (
        _count_keyword_matches(current_message, ADMIN_WAREHOUSE_ADDRESS_KEYWORDS) > 0
        or ("仓库" in current_message and "地址" in current_message)
    ):
        search_query = f"{search_query} {ADMIN_WAREHOUSE_ADDRESS_EXPANSION}".strip()

    # Order-sheet routing should only trigger on explicit mentions.
    if _count_direct_keyword_matches(current_message, ORDER_SHEET_ROUTING_KEYWORDS) > 0:
        search_query = f"{search_query} {ORDER_SHEET_ROUTING_EXPANSION}".strip()

    if _count_keyword_matches(current_message, EXECUTIVE_PROFILE_KEYWORDS) > 0:
        search_query = f"{search_query} {EXECUTIVE_PROFILE_EXPANSION}".strip()

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

    return sorted(docs, key=lambda doc_with_index: score(doc_with_index, docs.index(doc_with_index)), reverse=True)


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

    if not any(marker in current_message for marker in AMBIGUOUS_FOLLOW_UPS):
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
