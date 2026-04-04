import re


RED_LIST_KEYWORDS = [
    "价格",
    "底价",
    "卖价",
    "成本",
    "报价",
    "涨价",
    "优惠",
    "折扣",
    "赔付",
    "理赔",
    "罚款",
    "偏远费",
    "超重费",
    "带电费",
    "附加费",
    "明日之星",
    "工资",
    "人事",
    "人力",
    "绩效",
    "薪水",
    "薪酬",
    "薪酬管理",
    "提成",
    "奖金",
    "考勤",
    "请假",
    "领导",
    "考核",
    "主管",
    "赚钱",
    "发展",
    "搞钱",
    "晋升",
]

SEARCH_KEYWORDS = [
    "汇率",
    "新闻",
    "动态",
    "今天",
    "现在",
    "最新的",
    "最新",
    "实时",
    "美元",
    "天气",
    "发生",
    "现状",
    "大涨",
    "暴跌",
]

INTERNAL_ONLY_DOCUMENT_KEYWORDS = [
    "公司",
    "介绍",
    "简介",
    "仲易达",
    "制度",
    "流程",
    "考勤",
    "请假",
    "话术",
    "操作说明",
    "SOP",
    "人事",
    "人力",
    "薪酬",
    "报销",
    "审批",
    "处罚",
    "规定",
    "标准",
    "办法",
    "规范",
]

POLICY_ONLY_KEYWORDS = [
    "制度",
    "报销",
    "考勤",
    "请假",
    "人事",
    "人力",
    "薪酬",
    "绩效",
    "审批",
    "处罚",
    "规定",
    "标准",
    "办法",
    "规范",
]

CALCULATION_KEYWORDS = [
    "算一个",
    "算一算",
    "计算",
    "核算",
    "测算",
    "计费重",
    "体积重",
    "实重",
    "抛重",
    "材积",
    "方数",
    "立方",
    "毛重",
    "净重",
]

CALCULATION_SIGNAL_PATTERN = re.compile(
    r"\d+(?:\.\d+)?\s*(?:kg|公斤|cbm|方|立方|cm|m|箱|件)",
    re.IGNORECASE,
)


def should_force_deepseek_for_calculation(message: str) -> bool:
    normalized_message = str(message or "")
    if any(keyword in normalized_message for keyword in CALCULATION_KEYWORDS):
        return True

    has_quantity_signal = bool(CALCULATION_SIGNAL_PATTERN.search(normalized_message))
    has_calc_context = any(
        keyword in normalized_message for keyword in ("重量", "体积", "计费", "报价", "费用", "单价")
    )
    return has_quantity_signal and has_calc_context


def resolve_model_endpoint(
    *,
    prefer_deepseek: bool,
    doubao_endpoint: str,
    deepseek_endpoint: str,
    document_endpoint: str = "",
    intent: str = "",
    needs_realtime: bool = False,
    allow_primary_endpoint_as_deepseek: bool = True,
) -> tuple[str, bool]:
    normalized_doubao = str(doubao_endpoint or "").strip()
    normalized_deepseek = str(deepseek_endpoint or "").strip()
    normalized_document = str(document_endpoint or "").strip()

    if intent == "document" and not needs_realtime:
        return (normalized_document or normalized_doubao), False

    if prefer_deepseek:
        if normalized_deepseek:
            return normalized_deepseek, False
        if allow_primary_endpoint_as_deepseek and normalized_doubao:
            return normalized_doubao, False
        return normalized_doubao, True

    return normalized_doubao, False


def resolve_runtime_strategy(
    mode: str,
    intent: str,
    message: str,
    needs_realtime: bool,
    current_use_deepseek: bool,
) -> tuple[bool, bool]:
    if mode == "coach":
        return needs_realtime, current_use_deepseek

    if intent == "social":
        return False, False

    normalized_message = str(message or "")
    has_search_keyword = any(keyword in normalized_message for keyword in SEARCH_KEYWORDS)
    has_red_list_keyword = any(keyword in normalized_message for keyword in RED_LIST_KEYWORDS)
    has_policy_keyword = any(keyword in normalized_message for keyword in POLICY_ONLY_KEYWORDS)

    resolved_realtime = needs_realtime
    use_deepseek = current_use_deepseek

    if intent == "document" and has_policy_keyword:
        return False, True

    if has_search_keyword:
        resolved_realtime = True
        use_deepseek = True

    if has_red_list_keyword:
        use_deepseek = True
        if not has_search_keyword:
            resolved_realtime = False

    if should_force_deepseek_for_calculation(normalized_message):
        use_deepseek = True
        if not has_search_keyword:
            resolved_realtime = False

    if intent == "document" and resolved_realtime and any(
        keyword in normalized_message for keyword in INTERNAL_ONLY_DOCUMENT_KEYWORDS
    ):
        resolved_realtime = False
        use_deepseek = True

    if intent == "document" and resolved_realtime:
        return True, True

    if intent in ["quote", "address", "tracking"]:
        return resolved_realtime, True

    return resolved_realtime, use_deepseek


def resolve_temperature(
    *,
    base_temperature: float,
    mode: str,
    intent: str,
    needs_realtime: bool,
) -> float:
    """Return a conservative temperature based on runtime risk profile."""
    temp = max(0.0, float(base_temperature))

    if mode == "expert":
        return min(temp, 0.1)

    if intent in {"quote", "address", "tracking"}:
        return min(temp, 0.1)

    if intent == "document" and not needs_realtime:
        return min(temp, 0.2)

    return temp
