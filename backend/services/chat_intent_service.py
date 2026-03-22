import re
from typing import List, Optional, Tuple

from services.parser_utils import SEARCHABLE_WAREHOUSE_CODE_QUERY_PATTERN

WH_PATTERN = SEARCHABLE_WAREHOUSE_CODE_QUERY_PATTERN
ZIP_PATTERN = re.compile(r"(?<!\d)\d{5}(?!\d)")
TRACK_PATTERN = re.compile(r"(?:FBA|YT|UJ|LP|AG|SF|TB|JD)\d+[A-Z0-9]*|\b\d{10,20}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")

COMPANY_INTRO_KEYWORDS = [
    "公司",
    "介绍",
    "简介",
    "概况",
    "你是谁",
    "你们是谁",
    "仲易达",
    "发展历程",
    "背景",
    "能做哪些事",
    "怎么用",
    "正确的使用",
    "功能",
    "用法",
    "技巧",
    "操作说明",
    "业务",
]

QUOTE_KEYWORDS = ["报价", "价格", "多少钱", "费", "网点", "计费", "卖价", "舱位", "单价", "运费"]
REMOTE_KEYWORDS = ["偏远", "加费", "超编", "极偏", "邮编", "地址库", "哪里", "远不远", "送吗", "偏吗", "超区"]
INTERNAL_KEYWORDS = ["赚钱", "发展", "工资", "提成", "奖金", "制度", "晋升", "怎么赚", "搞钱"]
ADMIN_DOCUMENT_KEYWORDS = [
    "考勤",
    "迟到",
    "早退",
    "漏打卡",
    "未打卡",
    "扣款",
    "满勤",
    "旷工",
    "请假",
    "人事",
    "人力",
    "工资",
    "薪资",
    "薪酬",
    "绩效",
    "报销",
]
SOCIAL_KEYWORDS = ["你好", "哈哈", "笑话", "讲个", "唱个", "调戏", "暖场", "开心", "好玩"]
CONTINUATION_KEYWORDS = ["换一个", "再来", "继续", "下一个", "换个"]
TRACKING_HINT_KEYWORDS = ["查单", "查件", "轨迹", "运单", "物流单", "面单", "快递单", "tracking"]
KB_KEYWORDS = ["介绍", "你是谁", "你能做什么", "做哪些事", "你会干啥", "怎么用", "操作说明", "技巧", "什么事"]
ASSISTANT_QUOTE_MARKERS = ("报价明细", "预估总价", "仓别", "渠道", "ONT", "LAX", "JFK")
ASSISTANT_ADDRESS_MARKERS = ("偏远区域", "邮编", "详细地址", "仓库代码")
ASSISTANT_TRACKING_MARKERS = ("轨迹", "签收", "清关", "提取", "运输中")


def _contains_any(text: str, keywords: List[str] | tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _normalize_message(message: str) -> str:
    return str(message or "").strip()


def _enrich_message_with_metrics(raw_message: str) -> str:
    enriched_message = raw_message
    weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:KG|公斤)", raw_message, re.IGNORECASE)
    volume_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:CBM|方|立方)", raw_message, re.IGNORECASE)
    if weight_match:
        enriched_message += f" [系统备注：用户关注重量为 {weight_match.group(1)}KG]"
    if volume_match:
        enriched_message += f" [系统备注：用户关注体积为 {volume_match.group(1)}CBM]"
    return enriched_message


def _detect_explicit_intent(message: str) -> str | None:
    if not message:
        return None

    message_upper = message.upper()
    has_remote_keyword = _contains_any(message, REMOTE_KEYWORDS)
    has_zip = ZIP_PATTERN.search(message)
    has_wh = WH_PATTERN.search(message_upper)

    if has_remote_keyword and (has_zip or has_wh or len(message) > 8):
        return "address"

    track_match = TRACK_PATTERN.search(message)
    if track_match and not _contains_any(message, ["怎么算", "多少钱"]):
        track_token = track_match.group(0)
        if not PHONE_PATTERN.fullmatch(track_token) or _contains_any(message.lower(), [item.lower() for item in TRACKING_HINT_KEYWORDS]):
            return "tracking"

    if re.match(r"^\d{5}$", message):
        return "address"

    if _contains_any(message, ADMIN_DOCUMENT_KEYWORDS) or _contains_any(message, INTERNAL_KEYWORDS):
        return "document"

    if has_wh:
        return "quote"

    if _contains_any(message, QUOTE_KEYWORDS):
        return "quote"

    if _contains_any(message, KB_KEYWORDS):
        return "document"

    if _contains_any(message, SOCIAL_KEYWORDS):
        return "social"

    return None


def _infer_intent_from_assistant_message(message: str) -> str | None:
    normalized = _normalize_message(message)
    if not normalized:
        return None

    normalized_upper = normalized.upper()
    if WH_PATTERN.search(normalized_upper) or _contains_any(normalized, ASSISTANT_QUOTE_MARKERS):
        return "quote"
    if TRACK_PATTERN.search(normalized) or _contains_any(normalized, ASSISTANT_TRACKING_MARKERS):
        return "tracking"
    if ZIP_PATTERN.search(normalized) or (
        (WH_PATTERN.search(normalized_upper) or "识别为" in normalized) and _contains_any(normalized, ASSISTANT_ADDRESS_MARKERS)
    ):
        return "address"
    return None


def _infer_history_intent(history: Optional[List[dict]]) -> str | None:
    for item in reversed(history or []):
        role = item.get("role")
        content = _normalize_message(item.get("content", ""))
        if not content:
            continue
        if role == "user":
            explicit_intent = _detect_explicit_intent(content)
            if explicit_intent:
                return explicit_intent
        elif role == "assistant":
            explicit_intent = _infer_intent_from_assistant_message(content)
            if explicit_intent:
                return explicit_intent
    return None


async def classify_intent(message: str, history: Optional[List[dict]] = None) -> Tuple[str, str]:
    raw_message = _normalize_message(message)
    enriched_message = _enrich_message_with_metrics(raw_message)

    explicit_intent = _detect_explicit_intent(raw_message)
    if explicit_intent:
        return explicit_intent, enriched_message

    if any(keyword in raw_message.lower() for keyword in [item.lower() for item in TRACKING_HINT_KEYWORDS]):
        if "[系统提示" in raw_message or "[图片解析失败" in raw_message:
            return "tracking", enriched_message

    if len(raw_message) <= 4 and _contains_any(raw_message, CONTINUATION_KEYWORDS):
        inherited_intent = _infer_history_intent(history)
        if inherited_intent:
            return inherited_intent, enriched_message

    return "document", enriched_message
