from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import asyncio
from datetime import datetime
import os
import re
import time
from dependencies import get_current_user, User
from fastapi import Depends

from services.llm_client import chat_completion_stream, get_embedding, DOUBAO_MODEL_ENDPOINT
from services.chat_intelligence import (
    build_document_search_query,
    build_intent_clarification_message,
    build_document_source_footer,
    infer_knowledge_category,
    rerank_similar_documents,
    summarize_document_sources,
)
from services.rag_service import search_similar_documents
from services.chat_document_service import (
    retrieve_document_context,
    search_documents_from_disk,
)
from services.quote_service import (
    build_deterministic_quote_response,
    get_quote_data_as_string,
    search_best_quotes,
)
from services.tracking_service import fetch_tracking_info
from services.chat_runtime_service import resolve_temperature
from database import SessionLocal
from models.user import SystemSetting

import time as _time

_config_cache = {}
_config_cache_ts = 0
_CONFIG_TTL = 60  # 缓存有效期 60 秒

def get_all_config() -> dict:
    """一次性读取所有配置，带 60 秒 TTL 缓存"""
    global _config_cache, _config_cache_ts
    now = _time.time()
    if _config_cache and (now - _config_cache_ts) < _CONFIG_TTL:
        return _config_cache
    db = SessionLocal()
    try:
        settings = db.query(SystemSetting).all()
        _config_cache = {s.key: s.value for s in settings}
        _config_cache_ts = now
        return _config_cache
    finally:
        db.close()

def get_config(key: str, default: str) -> str:
    return get_all_config().get(key, default)

def invalidate_config_cache():
    """清空配置缓存，供管理员修改配置后调用"""
    global _config_cache, _config_cache_ts
    _config_cache = {}
    _config_cache_ts = 0

# 定义全局正则模式，避免重复编译
WH_PATTERN = re.compile(r'[A-Z]{3,4}\d+[A-Z]?')
# 5位邮编正则
ZIP_PATTERN = re.compile(r'(?<!\d)\d{5}(?!\d)')
ADDRESS_SOURCE_KEYWORDS = [
    "\u6765\u6e90",
    "\u6750\u6599",
    "\u54ea\u4efd",
    "\u54ea\u4e2a\u8868",
    "\u54ea\u4e00\u4efd",
    "\u4f9d\u636e",
    "\u4ece\u54ea\u67e5",
    "\u67e5\u7684\u4ec0\u4e48",
    "\u6570\u636e\u6e90",
]
DOCUMENT_SOURCE_KEYWORDS = [
    "来源",
    "材料",
    "依据",
    "出自",
    "出处",
    "哪个文件",
    "哪份文件",
    "哪个材料",
    "哪份材料",
    "哪条规定",
]
TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
TABLE_ROW_PATTERN = re.compile(r"^\s*\|.*\|\s*$")
HTML_BR_PATTERN = re.compile(r"<br\s*/?>", re.IGNORECASE)
MARKDOWN_HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s*")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# 定义 DeepSeek 接入点
DEEPSEEK_ENDPOINT = os.getenv("DEEPSEEK_MODEL_ENDPOINT", DOUBAO_MODEL_ENDPOINT)

# 公司介绍关键词 (用于触发 RAG 补全或详尽输出模式)
COMPANY_INTRO_KEYWORDS = [
    "公司", "介绍", "简介", "概况", "你是谁", "你们是谁", "仲易达", "发展历程", "背景", 
    "能做哪些事", "怎么用", "正确的使用", "功能", "用法", "技巧", "操作说明", "业务"
]

# 报价查询关键词
QUOTE_KEYWORDS = ["报价", "价格", "多少钱", "费", "门点", "计费", "卖价", "舱位", "单价", "运费"]
QUOTE_ROUTE_KEYWORDS = [
    "线路",
    "航线",
    "国家",
    "地区",
    "覆盖",
    "覆盖范围",
    "走哪些",
    "能走哪",
    "主要做哪些",
]
QUOTE_TABLE_KEYWORDS = ["报价表", "价格表", "价表"]
QUOTE_VENDOR_HINTS = [
    "荣达",
    "星夜",
    "兴业",
    "星野",
    "RONGDA",
    "XINGYE",
    "XINGYEWULIU",
]
QUOTE_FOLLOWUP_HINTS = ["呢", "那", "还有", "怎么样", "啥情况", "可以吗", "有吗"]
QUOTE_ASSISTANT_HINTS = ["报价", "价格", "报价表", "价格表", "仓库代码", "重量", "体积", "计费重", "KG", "CBM"]
POLICY_ONLY_DOCUMENT_KEYWORDS = [
    "制度",
    "规定",
    "标准",
    "办法",
    "规范",
    "流程",
    "报销",
    "考勤",
    "请假",
    "人事",
    "人力",
    "薪酬",
    "工资",
    "绩效",
    "审批",
    "处罚",
]

POLICY_SUBDOMAIN_HINTS = [
    "迟到",
    "早退",
    "旷工",
    "打卡",
    "考勤",
    "请假",
    "报销",
    "审批",
    "薪酬",
    "工资",
    "绩效",
]

CAPABILITY_OVERVIEW_KEYWORDS = [
    "你能做什么",
    "你会做什么",
    "你能帮我做什么",
    "能做哪些事",
    "都有哪些功能",
    "小易能做什么",
    "介绍下你自己",
    "自我介绍",
]

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = Field(default_factory=list)
    mode: Optional[str] = "general"
    image_base64: Optional[str] = None
    image_upload_id: Optional[str] = None
    use_deepseek: Optional[bool] = False


def is_quote_route_query(text: str) -> bool:
    content = str(text or "")
    if not content:
        return False
    has_route = any(kw in content for kw in QUOTE_ROUTE_KEYWORDS)
    has_vendor = any(kw in content.upper() for kw in QUOTE_VENDOR_HINTS)
    has_table = any(kw in content for kw in QUOTE_TABLE_KEYWORDS)
    return (has_route and (has_vendor or has_table)) or (has_vendor and has_table)


def has_quote_context_hint(text: str) -> bool:
    content = str(text or "")
    if not content:
        return False
    return (
        bool(WH_PATTERN.search(content.upper()))
        or any(kw in content for kw in QUOTE_KEYWORDS)
        or is_quote_route_query(content)
        or any(kw in content for kw in QUOTE_ASSISTANT_HINTS)
    )


def is_image_analysis_failure(image_desc: str) -> bool:
    if not image_desc:
        return False

    lowered = image_desc.lower()
    failure_markers = [
        "request id",
        "image dimensions are too small",
        "api error",
        "system error",
        "describe image crash",
        "识别失败",
        "解析图片",
        "系统错误",
        "暂不可用",
    ]
    return any(marker in lowered for marker in failure_markers)


def sanitize_markdown_text(text: str) -> str:
    """Normalize model output to plain readable text with one-item-per-line layout."""
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    output_lines: List[str] = []
    has_markdown_table = False

    for raw_line in normalized.split("\n"):
        line = raw_line

        stripped = line.strip()
        is_table_separator = bool(TABLE_SEPARATOR_PATTERN.match(line))
        is_table_row = (
            bool(TABLE_ROW_PATTERN.match(stripped))
            and stripped.startswith("|")
            and stripped.endswith("|")
            and "|" in stripped[1:-1]
        )
        if is_table_separator or is_table_row:
            has_markdown_table = True
            output_lines.append(stripped if stripped else line)
            continue

        line = HTML_BR_PATTERN.sub("\n", line)
        line = MARKDOWN_HEADING_PATTERN.sub("", line)
        line = line.replace("**", "").replace("__", "").replace("`", "")
        line = MARKDOWN_LINK_PATTERN.sub(r"\1 (\2)", line)
        output_lines.append(line)

    sanitized = "\n".join(output_lines)
    if has_markdown_table:
        return re.sub(r"\n{3,}", "\n\n", sanitized).strip()

    # Force inline list items into independent lines
    sanitized = re.sub(r"(?<=\S)\s+-\s+", "\n- ", sanitized)
    sanitized = re.sub(r"(?<=\S)\s+([A-Za-z]\.)\s+", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<=\S)\s+(\d+\.)\s+", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<=\S)\s+([一二三四五六七八九十]{1,3}、)\s*", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<=\S)\s+([（(]\d+[)）])\s*", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<=\S)\s+([①②③④⑤⑥⑦⑧⑨⑩])\s*", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<!\n)(?<=\S)([一二三四五六七八九十]{1,3}、)\s*", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<!\n)(?<=\S)([（(]\d+[)）])\s*", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<!\n)(?<=\S)([①②③④⑤⑥⑦⑧⑨⑩])\s*", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<=[。！？；])\s*-\s+", r"\n- ", sanitized)
    sanitized = re.sub(r"(?<=[。！？；])\s*(\d+\.)\s*", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<=[。！？；])\s*([A-Za-z]\.)\s*", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<=[。！？；：])\s*([一二三四五六七八九十]{1,3}、)\s*", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<=[。！？；：])\s*([（(]\d+[)）])\s*", r"\n\1 ", sanitized)
    sanitized = re.sub(r"(?<=[。！？；：])\s*([①②③④⑤⑥⑦⑧⑨⑩])\s*", r"\n\1 ", sanitized)
    # Deduplicate repeated ordered-list markers (e.g. "2. 2. xxx" -> "2. xxx")
    sanitized = re.sub(r"(^|\n)(\s*)(\d+\.)\s*\3\s+", r"\1\2\3 ", sanitized)
    sanitized = re.sub(r"(^|\n)(\s*)([A-Za-z]\.)\s*\3\s+", r"\1\2\3 ", sanitized)
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized).strip()
    return sanitized


def strip_think_blocks(text: str, *, in_think_block: bool) -> tuple[str, bool]:
    """Remove model thinking blocks wrapped by <think>...</think>."""
    source = str(text or "")
    if not source:
        return "", in_think_block

    out_parts: List[str] = []
    cursor = 0

    while cursor < len(source):
        if in_think_block:
            end_idx = source.find("</think>", cursor)
            if end_idx == -1:
                return "".join(out_parts), True
            cursor = end_idx + len("</think>")
            in_think_block = False
            continue

        start_idx = source.find("<think>", cursor)
        if start_idx == -1:
            out_parts.append(source[cursor:])
            cursor = len(source)
            continue

        out_parts.append(source[cursor:start_idx])
        cursor = start_idx + len("<think>")
        in_think_block = True

    return "".join(out_parts), in_think_block


def extract_address_targets_from_text(text: str) -> List[str]:
    if not text:
        return []
    wh_codes = WH_PATTERN.findall(text.upper())
    zips = ZIP_PATTERN.findall(text)
    # Keep order stable while de-duplicating
    return list(dict.fromkeys(wh_codes + zips))


extract_address_targets = extract_address_targets_from_text


def find_recent_address_targets(history: List[dict], limit: int = 3) -> List[str]:
    if not history:
        return []

    collected: List[str] = []
    for msg in reversed(history):
        if msg.get("role") not in {"user", "assistant"}:
            continue
        content = msg.get("content") or ""
        for target in extract_address_targets_from_text(content):
            if target not in collected:
                collected.append(target)
            if len(collected) >= limit:
                return collected
    return collected


def is_address_source_question(message: str) -> bool:
    return any(kw in message for kw in ADDRESS_SOURCE_KEYWORDS)


def is_document_source_question(message: str) -> bool:
    normalized = str(message or "")
    return any(kw in normalized for kw in DOCUMENT_SOURCE_KEYWORDS)


def is_capability_overview_query(message: str) -> bool:
    normalized = str(message or "")
    return any(keyword in normalized for keyword in CAPABILITY_OVERVIEW_KEYWORDS)


def build_safe_capability_overview_response() -> str:
    return """我能帮你做这 6 类事：

- 📊 **底价/卖价智能查询**：基于已上传并解析成功的内部报价表，按重量、体积、仓库/邮编给出可执行报价建议。
- 📍 **地址详情与偏远排雷**：识别 FBA 仓库/邮编，判断 UPS/FedEx 偏远等级并提醒附加费风险。
- 📚 **内部知识检索**：查询制度、流程、岗位职责、操作规范等内部文档。
- 🚚 **物流轨迹查询**：读取轨迹结果并翻译成清晰的业务结论与下一步建议。
- 🌐 **外部信息补充（非制度类）**：在需要时补充汇率/行业动态等实时信息。
- 🥊 **知识教练对练**：按场景进行询价/纠纷实战训练并给出复盘建议。

说明：
- 我只基于系统内“已上传且可检索”的资料回答，不会凭空编造渠道、制度或联系人。
- 如果你愿意，我可以马上按你的真实场景演示一轮：比如“改下单表找谁”或“100kg 去美西怎么报”。"""


def build_document_source_trace_response(similar_docs: List[dict], limit: int = 3) -> str:
    if not similar_docs:
        return (
            "这条信息目前没有检索到可核验的内部来源，我不能给你编造出处。\n"
            "请提供更具体的问题关键词，或补充对应制度文件名称后我再精准回溯。"
        )

    unique_sources: List[str] = []
    snippet_lines: List[str] = []
    for doc in similar_docs:
        metadata = doc.get("metadata") or {}
        source = str(metadata.get("source", "")).strip() or "未知文档"
        if source not in unique_sources:
            unique_sources.append(source)
        if len(snippet_lines) < limit:
            excerpt = re.sub(r"\s+", " ", str(doc.get("document", "")).strip())
            if len(excerpt) > 110:
                excerpt = excerpt[:110].rstrip() + "…"
            snippet_lines.append(f"- 《{source}》：{excerpt or '（该片段为空）'}")
        if len(unique_sources) >= limit and len(snippet_lines) >= limit:
            break

    lines = ["这条回答可核验的内部来源如下："]
    lines.extend([f"{idx}. 《{name}》" for idx, name in enumerate(unique_sources[:limit], start=1)])
    if snippet_lines:
        lines.append("")
        lines.append("命中片段（节选）：")
        lines.extend(snippet_lines)
    lines.append("")
    lines.append("如果你要，我可以继续给你定位到更细的原文段落。")
    return "\n".join(lines)


def boost_policy_document_hits(message: str, docs: List[dict]) -> List[dict]:
    normalized_message = str(message or "")
    matched_hints = [hint for hint in POLICY_SUBDOMAIN_HINTS if hint in normalized_message]
    if not matched_hints or not docs:
        return docs

    def _score(doc: dict) -> tuple[int, float]:
        metadata = doc.get("metadata") or {}
        source = str(metadata.get("source", ""))
        content = str(doc.get("document", ""))
        text = f"{source}\n{content}"
        keyword_hits = sum(1 for hint in matched_hints if hint in text)
        distance = float(doc.get("distance", 1.0))
        return keyword_hits, -distance

    return sorted(docs, key=_score, reverse=True)
    
async def classify_intent(message: str, history: List[dict] = None) -> str:
    """Classify user intent to determine routing (simple heuristic or LLM based)"""
    msg_upper = message.upper()
    
    # ====== 前置：重量/体积自动提取（必须在所有 return 之前） ======
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:KG|公斤)', message, re.IGNORECASE)
    volume_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:CBM|方|立方)', message, re.IGNORECASE)
    if weight_match:
        message += f" [系统备注：用户关注重量为 {weight_match.group(1)}KG]"
    if volume_match:
        message += f" [系统备注：用户关注体积为 {volume_match.group(1)}CBM]"
    
    # 1. Remote address check (High Priority)
    remote_keywords = ["偏远", "加费", "超编", "极偏", "邮编", "地址库", "哪里", "远不远", "送吗", "偏吗", "超区"]
    internal_keywords = ["赚钱", "发展", "工资", "提成", "奖金", "制度", "晋升", "怎么赚", "搞钱"]
    
    has_remote_kw = any(kw in message for kw in remote_keywords)
    has_zip = ZIP_PATTERN.search(message)
    has_wh = WH_PATTERN.search(msg_upper)
    asks_source = is_address_source_question(message)
    quote_signal = bool(
        weight_match
        or volume_match
        or any(kw in message for kw in QUOTE_KEYWORDS)
        or is_quote_route_query(message)
    )
    
    if has_remote_kw and (has_zip or has_wh or len(message) > 8) and not quote_signal:
        return "address", message
    
    # 1.5 Tracking check (单号查询拦截)
    # 检测类似 FBA+数字, YT+数字, 或者纯长串数字(大于10位)
    track_pattern = re.compile(r'(?:FBA|YT|UJ|LP|AG|SF|TB|JD)\d+[A-Z0-9]*|\b\d{10,20}\b', re.IGNORECASE)
    if track_pattern.search(message) and not any(kw in message for kw in ["怎么算", "多少钱"]):
        return "tracking", message
    
    # 特殊情况：如果用户直接甩一个 5 位邮编过来，也极大概率是问偏远
    if re.match(r'^\d{5}$', message.strip()):
        return "address", message

    # 2. Quote / Address disambiguation for warehouse code
    if has_wh and quote_signal:
        return "quote", message
    if has_wh:
        return "address", message
    
    for kw in QUOTE_KEYWORDS:
        if kw in message:
            return "quote", message
    if is_quote_route_query(message):
        return "quote", message
            
    # 3. Knowledge Base / Capabilities check (High Priority for self-intro)
    kb_keywords = ["介绍", "你是谁", "你能做什么", "做哪些事", "你会干啥", "怎么用", "操作说明", "技巧", "什么事"]
    if any(kw in message for kw in kb_keywords):
        return "document", message

    # 4. Social/Chitchat check
    social_keywords = ["你好", "哈喽", "笑话", "讲个", "唱个", "调戏", "暖场", "开心", "好玩"]
    continuation_keywords = ["换一个", "再来", "继续", "下一个", "换个"]
    if any(kw in message for kw in social_keywords):
        return "social", message

    # 4. Contextual inheritance for short commands
    if len(message.strip()) <= 4 and any(kw in message for kw in continuation_keywords):
        if history and len(history) > 0:
            last_ai_msg = ""
            for msg in reversed(history):
                if msg.get("role") == "assistant":
                    last_ai_msg = msg.get("content", "")
                    break
            # 如果 AI 上一句话看起来像是在讲笑话或闲聊（简单启发式判断）
            if any(kw in last_ai_msg for kw in ["笑话", "哈", "有趣", "嘿嘿", "故事"]):
                return "social", message
            if has_quote_context_hint(last_ai_msg):
                return "quote", message

    # 4.5 Vendor short follow-up should inherit quote context (e.g. "星夜呢")
    short_message = message.strip()
    vendor_followup = (
        len(short_message) <= 8
        and any(kw in short_message.upper() for kw in QUOTE_VENDOR_HINTS)
        and any(kw in short_message for kw in QUOTE_FOLLOWUP_HINTS)
    )
    if vendor_followup and history:
        for old in reversed(history[-8:]):
            if has_quote_context_hint(old.get("content", "")):
                return "quote", message

    # 5. Internal specific keywords (Bonus for document search)
    if any(kw in message for kw in internal_keywords):
        return "document", message

    # 6. Source follow-up should inherit address context if recent turns include warehouse/zip
    if asks_source and history:
        for old_msg in reversed(history[-8:]):
            content = old_msg.get("content", "")
            if ZIP_PATTERN.search(content) or WH_PATTERN.search(content.upper()):
                return "address", message

    # 7. If it's a short message or followup, check recent history for context
    if history and len(history) > 0:
        recent_msgs = [m.get("content", "") for m in history[-4:] if m.get("role") == "user"]
        for old_msg in recent_msgs:
            if has_quote_context_hint(old_msg):
                return "quote", message
    return "document", message

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Stream chat response based on mode, RAG, and quote tables."""
    
    # Process image if present
    needs_realtime = False
    resolved_image_base64 = request.image_base64
    if request.image_upload_id and not resolved_image_base64:
        from routers.upload import get_chat_image_base64
        try:
            resolved_image_base64 = await asyncio.to_thread(get_chat_image_base64, request.image_upload_id)
        except FileNotFoundError:
            request.message = "[系统提示：用户上传的图片已失效，请提醒用户重新上传。] " + request.message
        except Exception as e:
            print(f"Uploaded image resolve error: {e}")
            request.message = "[系统提示：用户上传的图片暂时无法读取，请提醒用户稍后重试。] " + request.message
    if resolved_image_base64:
        from services.llm_client import describe_image
        try:
            image_desc = await describe_image(resolved_image_base64)
            if image_desc:
                if is_image_analysis_failure(image_desc):
                    img_context = "[系统提示：用户上传了一张图片，但系统暂未成功完成视觉解析。请先基于用户文字继续回答，并提醒用户可重新上传更清晰的图片。]\n\n"
                else:
                    img_context = f"[系统提示：用户上传了一张图片，大模型的视觉解析结果如下：\n{image_desc}]\n\n"
                request.message = img_context + request.message
        except Exception as e:
            print(f"Image processing error: {e}")
            request.message = f"[图片解析失败，请提醒用户重新上传] " + request.message

    system_prompt = ""
    prebuilt_response_text = ""
    document_source_footer = ""
    intent = "document" # 预设默认意图
    needs_realtime = False
    
    if request.mode == "coach":
        # 检测是否是启动挑战场景的指令 (从当前消息或历史消息中寻找最近的指令)
        case_context = ""
        challenge_msg = request.message
        if request.history:
            # 优先从当前消息找，找不到就从历史记录倒序找最近的一个启动指令
            if not re.search(r'我要挑战【(.*?)】场景', challenge_msg):
                for h in reversed(request.history):
                    if h.get("role") == "user" and "我要挑战【" in (h.get("content") or ""):
                        challenge_msg = h.get("content")
                        break
        
        match = re.search(r'我要挑战【(.*?)】场景', challenge_msg)
        if match:
            scene_name = match.group(1)
            # 加载剧本数据
            cases_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "coach_cases.json")
            if os.path.exists(cases_path):
                try:
                    with open(cases_path, "r", encoding="utf-8") as f:
                        cases = json.load(f)
                        for c in cases:
                            if c.get("name") == scene_name:
                                case_context = f"""
### 🚨 当前正在执行模拟实战剧本 🚨
你必须完全沉浸在以下【客户模拟】身份中：

【剧本名称】：{c.get('name')}
【客户身份】：{c.get('persona')}
【业务背景】：{c.get('background')}
【核心矛盾点】：{c.get('conflict')}
【开场白（必须由此开始）】：{c.get('prompt')}

**行动准则（优先级最高）**：
1. 你现在是该场景下的【客户】，用户是你的【业务员】。
2. 禁止出现“我是助手”、“我可以帮您演练”等自述语。
3. 请严格按照剧本要求的语气（如：愤怒、焦急、精明等）进行博弈。
4. 如果这是你（客户）说的第一句话，请务必【完全原样输出】剧本中的【开场白】内容；如果已经开始博弈，请根据剧本逻辑灵活刁难业务员。
"""
                                break
                except Exception as e:
                    print(f"Error loading coach cases: {e}")

        if request.message.startswith("【结束对练】"):
            # 获取历史对话用于检索报价
            history_text = " ".join([m.get("content", "") for m in request.history if m.get("content")])
            query_text = history_text[-500:] if len(history_text) > 500 else history_text
            
            # 复盘阶段：并发获取内部知识库与报价数据
            async def fetch_docs():
                emb = await get_embedding(request.message)
                return await asyncio.to_thread(search_similar_documents, emb, 5)
                
            async def fetch_quotes():
                return await asyncio.to_thread(get_quote_data_as_string, query_text)
                
            similar_docs, quote_data = await asyncio.gather(fetch_docs(), fetch_quotes())
            
            context_text = ""
            for i, doc in enumerate(similar_docs):
                context_text += f"---\n[参考来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
            
            system_prompt = f"""你当前处于【导师复盘与点评】阶段。
作为曾带出过无数销冠、性格幽默调皮且说话带点“损”的【王牌教练】，你需要对刚才的实战记录进行深度复盘。

【公司最新真实报价数据】（用于检查业务员是否报错价）：
{quote_data}

【内部培训知识库片断】（用于检查业务逻辑错误）：
{context_text}

【点评深度：硬核准度检查】：
1. **检查“询价四要素”完成度**：必须明确评价业务员是否问全了：**重量(W)、体积(V)、详细邮编/仓库(Zip)、品名(Type)**。缺一项都要扣大分！
2. **核对系统真实底价**：对比下方的【公司最新真实报价数据】，如果业务员报错了价格，请不要留情，用你的调皮毒舌狠劲儿指出“这单报完公司裤衩子都亏没了”。
3. **识别陷阱能力**：评价业务员是否识破了剧本中的“瞒报品名”或“计费重陷阱”（哪怕业务员没识破，你也要指出这个陷阱在哪）。

你的汇报必须是漂亮的 Markdown 格式：
## 🏆 战力评估：[给个带有游戏/武侠色彩的评价，如：‘菜鸟中的战斗机’或‘一代宗师’]
## 📊 询价功底(100分制)：[针对重量/尺寸/邮编/品名四个维度的扣分详情]
## 🌟 闪光点：[发现了哪些高情商的瞬间]
## 💣 踩坑警告：[精准指出漏报价、漏附加费或被客户带着走的“傻”地方]
## 💡 教练私房课：[用那种‘酒桌传密’的语气，给一段教科书级的修正话术]
## 📈 碎碎念小纸条：[针对心态和业务的下一步提升]
"""
        else:
            # 获取当前场景的背景和历史记录，作为查询条件获取最新的系统底价
            background_text = ""
            if case_context:
                match_bg = re.search(r'【业务背景】：(.*?)\n', case_context)
                if match_bg:
                    background_text = match_bg.group(1)
            
            history_text = " ".join([m.get("content", "") for m in request.history if m.get("content")])
            query_text = (background_text + " " + history_text)[-500:]
            
            # 只有当对话进行到一定程度（比如2轮以后）或者包含具体的询价词，才注入报价表，极致压缩 prefill 开销
            quote_data = ""
            if len(request.history) > 4 or any(kw in request.message for kw in ["多少钱", "运费", "报价", "价格", "单价"]):
                # 对练阶段不需要全量搜索向量库，只并发获取报价和汇率
                async def fetch_quotes():
                    return await asyncio.to_thread(get_quote_data_as_string, query_text, limit=10) # 进一步降到 10 条
                
                async def fetch_rate():
                    try:
                        from services.web_search import get_realtime_exchange_rate
                        return await asyncio.to_thread(get_realtime_exchange_rate)
                    except:
                        return ""
                
                quote_data, rate = await asyncio.gather(fetch_quotes(), fetch_rate())
            else:
                rate = ""

            # 注入实时变量
            market_context = ""
            if rate:
                market_context += f"- 当前美元汇率：{rate}\n"
            
            market_context += "- 市场动态：近期美线罢工风险上升，舱位极其紧张，查验率有所提高。\n"

            system_prompt = f"""你现在正在进行【物流实战陪练】。
你要扮演一个真实的外贸卖家（客户）。你【绝对不是】教练，也【绝对不要】好为人师地解答业务员的专业问题。
请你完全沉浸在买家的角色中，尽情“折磨”你的业务员。

【今日实战市场环境】：
{market_context}

{case_context}

【公司最新真实底价表（这是你的核心心理价位底牌，用于比价评判）】：
{quote_data}

【你的核心行动准则（绝对服从）】：
1. **完全沉浸**：你现在就是个真实的、有血有肉的客户。用户是向你推销的物流供应商（业务员）。禁止使用“我是AI”、“作为教练”、“我可以帮您演练”等出戏话术。
2. **底价压制（去品牌化）**：你会时刻参考上方的【真实底价表】。如果业务员给你的报价明显高于底价，请立刻嫌贵并疯狂压价！
   - ⚠️ **死命令**：绝对禁止说出底价表里的物流同行公司名字（如：禁止说“锦联报了10块”、“亿阳才多少钱”等任何具体品牌）。
   - 💰 **砍价话术模板**：“大哥，我现在手里接到的另一份报价才 [根据底价浮动编造出的具体数字] 钱，你这单价太高了，我没法跟老板交代啊！”（只喊数字，绝不提哪家公司给的）
3. **专业挖坑**：面对询价，你作为客户会故意隐瞒货物属性（如带电带磁不直说、不报具体箱规尺寸），或者给个模糊范围，看业务员能不能专业地审出来。
4. **拉锯战**：你的任务是磨练业务员的逼单和谈判能力。不要轻易妥协，试着极限拉扯利润空间、时效赔偿或免仓期条款。
"""
    elif request.mode == "expert":
        # 专家模式：极简原则，强制换行
        request.use_deepseek = False
        assistant_replies = [m for m in request.history if m.get("role") == "assistant"]
        reply_round = len(assistant_replies) + 1
        intent = "expert"
        
        system_prompt = f"""你是一个专业的【诊断专家小易】。禁止废话，结论先行，必须换行。

**当前：第 {reply_round} 轮**

【协议】：
- 第 1-2 轮：给出初步判断，然后**追问用户**选择情况（必须提供 3-4 个选项）。
- 第 3 轮起：根据前两轮信息，直接给出最终建议和话术，停止追问。

【排版死命令】：
每个选项必须独占一行，且与下一选项之间必须空一行。严禁用横线或空格连在同一行！

格式范例：
初步判断：[一句话诊断]

请选择：

1. 情况一

2. 情况二

3. 情况三
"""

    else:
        try:
            intent, request.message = await classify_intent(request.message, request.history)
        except Exception as e:
            print(f'Intent Error: {e}')
            intent = 'document'
        clarification_message = build_intent_clarification_message(
            intent,
            request.message,
            request.history,
        )
        if clarification_message:
            prebuilt_response_text = clarification_message
        elif intent == "quote":
            # Handle Quote Query
            search_query = request.message
            if request.history:
                search_query += " " + " ".join([m.get("content", "") for m in request.history[-2:] if m.get("role") == "user"])
            quote_data = await asyncio.to_thread(get_quote_data_as_string, search_query)
            
            # --- 【新增】主动地址/偏远识别逻辑 ---
            address_probe_context = ""
            wh_codes = WH_PATTERN.findall(request.message.upper())
            zips = ZIP_PATTERN.findall(request.message)
            targets = list(set(wh_codes + zips))
            
            if targets:
                from services.address_service import address_service
                for t in targets:
                    res = await asyncio.to_thread(address_service.query, t)
                    if res["is_remote"]:
                        address_probe_context += f"- 📍 目标地址【{t}】识别为**偏远地址**！偏远级别：**{res['level']}**\n"
                    elif res["zip"] or res["address"]:
                        address_probe_context += f"- ✅ 目标地址【{t}】识别为非偏远区（正常区域）。\n"

            quote_records = await asyncio.to_thread(search_best_quotes, search_query, 10)
            deterministic_quote = await asyncio.to_thread(
                build_deterministic_quote_response,
                request.message,
                quote_records,
                address_probe_context,
                3,
            )
            if deterministic_quote:
                prebuilt_response_text = deterministic_quote
            
            system_prompt = f"""你是一个名为“小易”的【金牌物流合伙人】。
**你的使用者是公司的业务同事（也是你最铁的战友）。**

【你的灵魂设定】：
1. **幽默与共情**：你的回复要带点职业冷幽默，充满人情味。
2. **绝对严谨**：在报价、附加费和偏远费上，你的准确度必须是“航母级别”的。
3. **禁止尊称**：严禁称呼用户为“老板”或“客户”，你应该像个老练、靠谱且有趣的部门经理/老鸟搭档。

【你的主动排雷任务（本次重点）】：
*   ⚠️ **偏远主动提醒**：如果下方的【主动识别的地址风险分析】中有数据，你**必须**在回复报价的显著位置（通常是回复的第一句或表格下方）大字号/加粗提醒同事。
*   💰 **计费重警示**：如果发现体积重远大于实重（泡货），要幽默地提醒同事别报亏了。

【报价展示核心规则】：
* **必须使用完整表格**：展示报价时，必须使用 Markdown 表格，且**必须展示所有重量阶梯的价格**（以便同事对比），禁止随意删除表格行。
* **精准锁定（高亮）**：如果用户提到了具体重量（如 200kg），请在完整表格中【高亮】或【加粗】显示最匹配的那个阶梯单价。
* **渠道推荐**：默认【必须优先】展示咱自家的“明日之星”系列。
* **仓位智能选择**：
    - **双重展示**：如果用户仅询问价格而未说明货在何处，你【必须同时】报出“明日之星”的**华东仓**和**华南仓**的价格。
    - **智能判断**：如果用户明确了位置，则优先并重点展示对应仓库报价。
    - **区分来源**：请通过数据中的 `_source` 字段来辨别仓位并在表格中明确标出“出发仓”。

【主动识别的地址风险分析（必读并提醒）】：
{address_probe_context if address_probe_context else "（本次消息中未识别到明确的仓库或邮编，请按常规报价回复）"}

【对话引导】：
* **在结尾，你【必须】附上一句引导**，提示同事补充箱规、重/方、具体品类。

【💡 老鸟碎碎念】：
结合具体行情，给同事1-2句成交心理学、规避海关风险或拉高利润的干货。

【系统实时同步的报价表数据】：
{quote_data}
"""

        elif intent == "address":
            from services.address_service import address_service
            targets = extract_address_targets_from_text(request.message)
            if not targets:
                targets = find_recent_address_targets(request.history, limit=3)
            
            query_results = []
            for t in targets:
                res = await asyncio.to_thread(address_service.query, t)
                query_results.append(res)

            if is_address_source_question(request.message):
                source_name_map = {
                    "primary": "\u539f\u4ed3\u5e93\u4fe1\u606f\uff08\u504f\u8fdc\u5730\u5740/\u4e9a\u9a6c\u900a\u4ed3\u5e93\u540d\u5355.xlsx\uff09",
                    "yiyang": "\u4ebf\u9633\u4ed3\u5e93\uff08\u504f\u8fdc\u5730\u5740/\u4ebf\u9633\u4ed3\u5e93.xlsx\uff09",
                    "web": "\u8054\u7f51\u67e5\u8be2\uff08\u672c\u5730\u4ed3\u5e93\u672a\u547d\u4e2d\u540e\u89e6\u53d1\uff09",
                    "input": "\u7528\u6237\u8f93\u5165\u90ae\u7f16\uff08\u672c\u5730\u504f\u8fdc\u89c4\u5219\u6821\u9a8c\uff09",
                }
                if not query_results:
                    prebuilt_response_text = "\u8fd9\u6b21\u6d88\u606f\u91cc\u6ca1\u6709\u8bc6\u522b\u5230\u4ed3\u5e93\u4ee3\u7801\u6216\u90ae\u7f16\u3002\u8bf7\u76f4\u63a5\u53d1\u4ed3\u5e93\u4ee3\u7801\uff08\u5982 MCC1\uff09\u62165\u4f4d\u90ae\u7f16\uff0c\u6211\u9a6c\u4e0a\u544a\u8bc9\u4f60\u5177\u4f53\u6765\u6e90\u3002"
                else:
                    lines = ["\u672c\u6b21\u4ed3\u5e93/\u90ae\u7f16\u67e5\u8be2\u7684\u6765\u6e90\u5982\u4e0b\uff1a"]
                    for row in query_results:
                        source_label = source_name_map.get(row.get("source"), "\u672a\u547d\u4e2d\u672c\u5730\u4ed3\u5e93\uff0c\u4e5f\u672a\u8054\u7f51\u547d\u4e2d")
                        lines.append(f"{row['target']}\uff1a{source_label}")
                    prebuilt_response_text = "\n".join(lines)

            address_context = ""
            for res in query_results:
                addr_str = f"【{res['target']}】地址详情："
                if res["address"]:
                    addr_str += f"\n- 详细地址: {res['address']}\n- 城市: {res['city']}\n- 州: {res['state']}"
                
                if res["is_remote"]:
                    address_context += f"{addr_str}\n- 偏远状态: 【属于偏远】等级: {res['level']} (邮编: {res['zip']})\n\n"
                else:
                    status = "非偏远地址" if res["zip"] else "系统库中暂未查到该地址的详细偏远信息"
                    address_context += f"{addr_str}\n- 偏远状态: {status} (邮编: {res['zip'] or 'N/A'})\n\n"
            
            system_prompt = f"""你是一个智能货代地址专家。
用户正在向你查询仓库或邮编的详细地址及偏远情况。

【系统查询到的核心真实数据（不可篡改）】：
{address_context}

请严格基于上述数据回复用户：
1. **绝对禁止修改偏远等级**：如果系统显示为“UPS极偏远”或“超偏远”，严禁简化为“偏远”。这是一个非常关键的成本节点！
2. 首先报出该查询对象的详细地址详情。
3. 明确告知其【偏远状态】。如果是极偏远，请用加粗、感叹号等方式极力提醒。
4. 友情提醒战友务必在报价中核算这部分高昂的附加费成本。语气要像经验丰富的老鸟，专业且严谨。
"""

            if not prebuilt_response_text and not query_results:
                prebuilt_response_text = "\u8bf7\u63d0\u4f9b\u4ed3\u5e93\u4ee3\u7801\uff08\u5982 MCC1\uff09\u62165\u4f4d\u90ae\u7f16\uff0c\u6211\u518d\u7ed9\u4f60\u67e5\u8be6\u7ec6\u5730\u5740\u3001\u90ae\u7f16\u548c\u504f\u8fdc\u72b6\u6001\u3002"

        elif intent == "tracking":
            track_match = re.search(r'(?:FBA|YT|UJ|LP|AG|SF|TB|JD)\d+[A-Z0-9]*|\b\d{10,20}\b', request.message.upper())
            track_num = track_match.group(0) if track_match else request.message.strip()
            
            # 调用刚刚写好的查件黑科技
            track_result = await fetch_tracking_info(track_num)
            
            if track_result.get("status") == "success":
                tracking_data = track_result.get("data", "")
            else:
                tracking_data = track_result.get("message", "轨迹查询遇到网络错误或验证码阻拦。")

            system_prompt = f"""你是一个名为“小易”的【贴心物流管家】。
用户发来了一个物流单号：{track_num}，要求查询轨迹。

我（后台系统）已经派爬虫前往速递管家网站尝试抓取了该单号的数据，以下是原汁原味的查询结果（由于有反爬虫验证，结果可能是一些杂音或是正确的轨迹信息）：
【后台系统返回结果】：
{tracking_data}

你的任务：
1. **解构并润色**：像一位专业客服一样把上述后台结果翻译成“人话”告诉用户。
2. **处理报错**：如果后台返回了“验证码错误,请重试”或其它报错，坦白告诉用户。
3. **如果是正常轨迹**：梳理出最新的时间线和进度。
"""

        else:
            # Handle RAG Document Query 
            search_query = build_document_search_query(
                request.message,
                request.history,
                COMPANY_INTRO_KEYWORDS,
            )
            if not prebuilt_response_text and is_capability_overview_query(request.message):
                needs_realtime = False
                prebuilt_response_text = build_safe_capability_overview_response()
            
            # 执行检索：由后台设置决定是否开启 RAG
            context_text = ""
            best_distance = 1.0
            similar_docs = []
            source_summary = ""
            search_category = infer_knowledge_category(search_query)
            
            enable_rag = get_config("ai_enable_rag", "true").lower() == "true"
            try:
                raw_top_k = int(get_config("ai_search_top_k", "6"))
            except ValueError:
                raw_top_k = 6
            top_k = max(3, min(raw_top_k, 20))
            if len(request.message.strip()) <= 12:
                top_k = min(top_k + 2, 20)

            is_policy_document_query = any(
                keyword in request.message for keyword in POLICY_ONLY_DOCUMENT_KEYWORDS
            )
            if is_policy_document_query:
                top_k = min(top_k + 3, 20)

            retrieval_result = await retrieve_document_context(
                search_query=search_query,
                search_category=search_category or "",
                enable_rag=enable_rag,
                top_k=top_k,
                get_embedding=get_embedding if enable_rag else None,
                search_documents=search_similar_documents if enable_rag else None,
                rerank_documents=rerank_similar_documents if enable_rag else None,
                summarize_sources=summarize_document_sources,
                build_source_footer=build_document_source_footer,
                fallback_search_documents=search_documents_from_disk,
            )

            context_text = retrieval_result["context_text"]
            best_distance = retrieval_result["best_distance"]
            similar_docs = retrieval_result["similar_docs"]
            source_summary = retrieval_result["source_summary"]
            document_source_footer = retrieval_result["document_source_footer"]
            needs_realtime = retrieval_result["needs_realtime"]
            
            if is_policy_document_query and similar_docs:
                similar_docs = boost_policy_document_hits(request.message, similar_docs)
                best_distance = float(similar_docs[0].get("distance", 1.0))
                source_summary = summarize_document_sources(similar_docs)
                document_source_footer = build_document_source_footer(similar_docs)
                context_text = "".join(
                    f"---\n[内部资料片段 {i+1} | 来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
                    for i, doc in enumerate(similar_docs)
                )
            
            if similar_docs:
                print(f">> RAG Hit! Best distance: {best_distance:.4f}, Chunks: {len(similar_docs)}")

            # 标记 RAG 结果是否较差。制度类阈值更宽松，降低“命中但误判为无依据”的情况。
            distance_threshold = 0.88 if is_policy_document_query else 0.75
            if not similar_docs or best_distance > distance_threshold:
                if is_policy_document_query:
                    needs_realtime = False
                    prebuilt_response_text = (
                        "我先不乱猜：当前未在公司已上传材料中检索到该制度问题的有效依据。\n"
                        "请上传对应制度文件，或告诉我更具体的关键词（如文件名、条款名、部门场景），我继续帮你定位。"
                    )
                else:
                    needs_realtime = True
                if best_distance > distance_threshold:
                    # 弱命中不允许作为“内部依据”，避免模型拿低相关片段强行输出确定结论。
                    similar_docs = []
                    context_text = ""
                    source_summary = ""
                    document_source_footer = ""

            if not prebuilt_response_text and is_document_source_question(request.message):
                needs_realtime = False
                prebuilt_response_text = build_document_source_trace_response(similar_docs)

            source_instruction = (
                "3. **区分来源**：仅可引用【内部资料来源提示】中列出的文件作为依据，不得凭空新增文件名。"
                if source_summary
                else "3. **区分来源**：本轮未命中内部资料来源，严禁使用“根据公司内部资料”口吻，必须明确说明“未检索到可核验依据”。"
            )
             
            system_prompt = f"""你是一个名为“小易”的企业级高级助理，现在的身份是【仲易达内部专家顾问】。
你拥有以下 **6 大核心能力**，能够全方位支持业务同事：
1. **【全自动底价/卖价查询】**：实时同步公司最新 Excel 报价表，支持阶梯价查询、双仓对比报价。
2. **【地址详情与偏远排雷】**：智能识别 FBA 仓库、邮编，秒查 UPS/FedEx 偏远等级与极偏远提醒。
3. **【内部知识库精准检索】**：涵盖公司制度、操作流程、标准话术、岗位职责。
4. **【物流轨迹黑科技查询】**：直接抓取第三方网站最新路由，翻译成易懂的客服语言。
5. **【对外信息速览（非制度类）】**：仅在非制度类问题且确有需要时补充实时外部信息。
6. **【模拟实战训练（知识教练）】**：支持场景化对练，帮同事磨练谈单技巧。

### 核心执行指令：
1. **内部资料优先**：下方【内部知识检索参考材料】是当前最可信依据，优先基于它回答。
2. **组合能力**：当用户问及“你能做什么”时，完整展示上述 6 项能力，并结合参考材料给出具体例子。
{source_instruction}
4. **歧义拦截**：遇到多义词先追问确认。
5. **制度类问题仅基于内部资料**：涉及制度、报销、考勤、人事、审批、处罚、薪酬时，不联网、不用外部常识补齐。
6. **缺资料就明确说明**：如未检索到内部材料，直接说明“未在公司已上传材料中找到依据”，不要编造。
7. **适度情绪价值**：在不影响准确性的前提下，可先用 1 句自然共情开场（如“我来帮你快速定位这个问题”），语气像靠谱同事，不要生硬说教。

【北京时间】：{datetime.now().strftime('%Y年%m月%d日')}

【内部知识检索权威材料（必读）】：
{context_text if context_text else '（内部文档库中暂无匹配内容）'}

【内部资料来源提示】：
{source_summary if source_summary else '（本轮暂无明确来源文件）'}

【回复风格】：干练、专业、有理有据，同时自然、有同理心。
"""
        if request.mode != "coach":
            red_list_keywords = [
                "价格", "底价", "卖价", "成本", "报价", "涨价", "优惠", "折扣",
                "赔偿", "理赔", "丢件", "破损", "扣货", "没收", "罚款", "索赔",
                "偏远费", "超重费", "带电费", "附加费", "明日之星", "明日", "锦联", "亿阳",
                "工资", "绩效", "薪水", "薪酬", "提成", "奖金", "扣款", "考勤",
                "请假", "找谁", "问谁", "联系谁", "哪个部门", "领导", "考核", "主管",
                "赚钱", "发展", "搞钱", "晋升", "怎么赚", "分钱"
            ]
            search_keywords = ["汇率", "新闻", "动态", "今天", "现在", "最新的", "最新", "实时", "美元", "天气", "发生", "现状", "大涨", "暴跌"]
            is_policy_document_query = intent == "document" and any(
                kw in request.message for kw in POLICY_ONLY_DOCUMENT_KEYWORDS
            )
            
            if intent == "social":
                needs_realtime = False
                request.use_deepseek = False
                print(">> Social intent detected, using Doubao (Chit-chat).")
            elif is_policy_document_query:
                needs_realtime = False
                request.use_deepseek = True
                print(">> Policy document query detected, forcing internal-only answer (no web search).")
            elif any(kw in request.message for kw in red_list_keywords):
                needs_realtime = False
                request.use_deepseek = True # 红线问题用理性的 DeepSeek
                print(">> Intercepted by RED LIST, disabling network search, forcing DeepSeek.")
            elif any(kw in request.message for kw in search_keywords) or (intent == "document" and needs_realtime):
                needs_realtime = True
                request.use_deepseek = True # 联网搜索强制使用 DeepSeek
                print(">> Enabling network search, forcing DeepSeek for query.")
            
            # 报价、地址和轨迹查询默认用 DeepSeek 理性的头脑去分析
            if intent in ["quote", "address", "tracking"]:
                request.use_deepseek = True

    # 注入全局输出格式规范
    if request.mode == "expert":
        system_prompt += "\n\n【排版提示】：为了移动端可读性，选项请使用 Markdown 无序列表（- A. ..., - B. ...），并保持每个选项独立成行。"

    # 注入全局输出格式规范
    detail_keywords = ["详细", "具体", "完整", "展开", "多说点", "细说", "列表", "全部"]
    # 如果用户明确要求详细，或者是在询问功能说明、报价相关内容，则开启详尽模式
    wants_detail = any(kw in request.message for kw in detail_keywords) or \
                   any(kw in request.message for kw in COMPANY_INTRO_KEYWORDS) or \
                   any(kw in request.message for kw in QUOTE_KEYWORDS)
    
    if wants_detail:
        global_style_prompt = """

【全局输出表达规范】：
1. **详尽解答**：用户要求详细说明，请提供完整、详尽的内容，可以分点细致展开，确保逻辑连贯、完整。不可遗漏重要细节。
2. **关键标粗**：务必使用 Markdown 语法对【价格/金额】、【重量/尺寸/体积】、【关键地址/邮编】、【单号/最新状态】、【行动建议】等核心信息进行加粗（如：**核心结论**）。
3. **结构清晰**：请使用 Markdown 的分段和列表（-），确保排版专业、易读，重点突出。
4. **专有名词理解**：当资料或用户对话中提到“明日”时，极大概率指的是公司的特色物流渠道“明日之星”。请结合语境优先将其理解为该渠道。
5. **语气自然**：先给结论，再补细节；可用 1 句简短共情或支持性表达，避免机械客服腔。
"""
    else:
        global_style_prompt = """

【全局输出表达规范】：
1. **极致精简**：拒绝长篇大论、无意义的寒暄与废话，用最精准、直白、易读的短句迅速作答。
2. **结构清晰**：使用换行和分段保证结构清晰。第一行直给结论，后续用短句和项目列表（-）呈现重点。
3. **关键标粗**：务必使用 Markdown 语法对【价格/金额】、【重量/尺寸/体积】、【关键地址/邮编】、【单号/最新状态】、【行动建议】等核心信息进行加粗（如：**核心结论**）。
4. **专有名词理解**：优先将“明日”理解为公司渠道“明日之星”。
5. **语气自然**：像专业同事沟通，允许简短情绪价值表达，但不要影响事实准确性。
"""
    # 专家模式和对练阶段排除通用风格注入，避免指令冲突，保持其独立的高强度追问/对练逻辑
    if request.mode not in ["coach", "expert"] or (request.mode == "coach" and request.message.startswith("【结束对练】")):
        system_prompt += global_style_prompt

    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]
    if request.mode not in {"coach", "expert"}:
        messages[0]["content"] += """

【事实约束（必须遵守）】
1. 没有证据就不要下结论，不允许编造价格、政策、地址、轨迹、时间点。
2. 若内部资料未命中或证据不足，明确写“未检索到可核验依据”，并给出需要补充的信息。
3. 涉及数字（金额、重量、时效、汇率）时，只能使用本轮可验证数据；无法确认时先澄清再回答。
4. 禁止把“推测”写成“事实”；若是经验判断，必须显式标注“经验判断”。
"""
    if resolved_image_base64 and "[系统提示" in request.message:
        messages[0]["content"] += "\n\n**重要指令**：用户上传了图片，请根据解析内容理解。"

    # Inject manual search context only if needed (for specific currency rates if preferred)
    if needs_realtime and "汇率" in request.message:
        try:
            from services.web_search import get_realtime_exchange_rate
            rate = get_realtime_exchange_rate()
            messages[0]["content"] += f"\n\n【系统提示：当前实时汇率：{rate}】"
        except:
            pass

    # 安全过滤：只允许 user / assistant 角色进入上下文，防止 Prompt Injection
    _ALLOWED_ROLES = {"user", "assistant"}
    # 动态上下文窗口：从设置中读取 (默认提高到 40 条对话记录，支持长对话连贯性)
    max_history = int(get_config("ai_max_history", "40"))
    if request.history:
        safe_history = [
            m for m in request.history[-max_history:]
            if m.get("role") in _ALLOWED_ROLES and isinstance(m.get("content"), str)
        ]
        messages.extend(safe_history)

    messages.append({"role": "user", "content": request.message})

    async def stream_generator():
        """
        流式输出：根据任务属性选择最优模型发动机。
        """
        async def emit_text_stream(text: str, chunk_size: int = 24):
            content = str(text or "")
            if not content:
                return
            for idx in range(0, len(content), chunk_size):
                yield content[idx : idx + chunk_size]
                # 主动让出事件循环，提升前端感知的“流式刷新”连续性
                await asyncio.sleep(0)

        line_buffer = ""
        full_response = ""
        raw_full_response = ""
        plain_emitted = ""
        stream_had_error = False
        in_think_block = False
        start_time = time.time()
        if prebuilt_response_text:
            full_response = sanitize_markdown_text(prebuilt_response_text)
            async for piece in emit_text_stream(full_response):
                yield piece
            return
        
        def append_and_diff(raw_delta: str) -> str:
            nonlocal raw_full_response, plain_emitted, full_response
            raw_full_response += raw_delta
            plain_now = sanitize_markdown_text(raw_full_response)
            common_len = 0
            for old_char, new_char in zip(plain_emitted, plain_now):
                if old_char != new_char:
                    break
                common_len += 1
            delta_text = plain_now[common_len:]
            plain_emitted = plain_now
            full_response = plain_now
            return delta_text
        # 确定最终使用的模型接入点
        # 如果 request.use_deepseek 为 True，则强行使用理性的推理接入点
        final_endpoint = DEEPSEEK_ENDPOINT if request.use_deepseek else DOUBAO_MODEL_ENDPOINT
        
        # 专家模式使用低采样温度（0.1）保证排版稳定性
        temp = resolve_temperature(
            base_temperature=float(get_config("ai_temperature", "0.3")),
            mode=request.mode or "general",
            intent=intent or "document",
            needs_realtime=bool(needs_realtime),
        )
            
        try:
            async for raw_chunk in chat_completion_stream(
                messages, 
                use_bot=False, 
                use_search=needs_realtime,
                model_endpoint=final_endpoint,
                temperature=temp
            ):
                line_buffer += raw_chunk
                while "\n" in line_buffer:
                    line, line_buffer = line_buffer.split("\n", 1)
                    line = line.strip()
                    
                    if not line: continue
                    if line == "data:[DONE]": 
                        break
                    if not line.startswith("data:"): continue
                    
                    data_str = line[5:].strip()
                    try:
                        data = json.loads(data_str)
                        if not isinstance(data, dict): continue

                        # Handle potential API error in the stream data itself
                        if "error" in data:
                            err_obj = data["error"]
                            error_msg = err_obj.get("message", "API Error") if isinstance(err_obj, dict) else str(err_obj)
                            error_res = f"\n[模型服务错误：{error_msg}]"
                            delta_text = append_and_diff(error_res)
                            stream_had_error = True
                            if delta_text:
                                async for piece in emit_text_stream(delta_text):
                                    yield piece
                            break
                        
                        # Standard OpenAI compatible
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                filtered_content, in_think_block = strip_think_blocks(
                                    content,
                                    in_think_block=in_think_block,
                                )
                                if not filtered_content:
                                    continue
                                delta_text = append_and_diff(filtered_content)
                                if delta_text:
                                    async for piece in emit_text_stream(delta_text):
                                        yield piece
                        # Volcengine Responses API Streaming
                        elif "type" in data and data["type"] == "response.output_text.delta":
                            content = data.get("delta", "")
                            if content:
                                filtered_content, in_think_block = strip_think_blocks(
                                    content,
                                    in_think_block=in_think_block,
                                )
                                if not filtered_content:
                                    continue
                                delta_text = append_and_diff(filtered_content)
                                if delta_text:
                                    async for piece in emit_text_stream(delta_text):
                                        yield piece
                        # Volcengine Responses API Error or Other types
                        elif "type" in data and data["type"] == "error":
                            err_info = data.get("error", {})
                            error_msg = err_info.get("message", "Unknown error") if isinstance(err_info, dict) else str(err_info)
                            error_res = f"\n[实时搜索服务错误：{error_msg}]"
                            delta_text = append_and_diff(error_res)
                            stream_had_error = True
                            if delta_text:
                                async for piece in emit_text_stream(delta_text):
                                    yield piece
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_res = f"\n[系统提示：后端处理发生异常 {str(e)}]"
            delta_text = append_and_diff(error_res)
            if delta_text:
                async for piece in emit_text_stream(delta_text):
                    yield piece
        finally:
            # 默认不自动追加“参考来源”尾注，避免影响阅读体验。
            # 若用户明确追问来源，会走 is_document_source_question 分支单独返回出处信息。
            # Save history to DB
            processing_time = time.time() - start_time
            db = SessionLocal()
            try:
                from models.chat_history import ChatHistory
                user_id = current_user.id if current_user else None
                # Omit image_base64 from logged message if too large, simply note it
                msg_to_store = request.message
                if request.image_base64 or request.image_upload_id:
                    msg_to_store = f"[附带图片] {msg_to_store}"

                history_record = ChatHistory(
                    user_id=user_id,
                    user_message=msg_to_store,
                    ai_response=full_response,
                    processing_time=processing_time,
                    mode=request.mode
                )
                db.add(history_record)
                db.commit()
            except Exception as db_e:
                print(f"Error saving chat history: {db_e}")
            finally:
                db.close()

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
