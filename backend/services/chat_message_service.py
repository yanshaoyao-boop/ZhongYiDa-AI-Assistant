import re
from typing import Iterable, List, Optional


DETAIL_KEYWORDS = ["详细", "具体", "完整", "展开", "多说点", "细说", "列表", "全部"]

DETAIL_STYLE_PROMPT = """
⚠️【全局输出表达规范】（最高级别的核心指令）：
1. **先给结论**：第一句先直接回答用户问题，先说结论、判断或最终建议，再补充原因和细节。
2. **详细解答，但不绕**：用户要求详细说明时，可以展开，但只展开与问题直接相关的内容，不要写长篇铺垫、客套和自我介绍。
3. **无法精确时也先说人话**：如果信息不足、制度未知或资料不完整，第一句先明确“目前无法精确判断/无法精确计算”，然后立刻给出 **2-3 种最常见情况** 或影响结果的关键条件。
4. **结构清晰**：优先用短段落、编号或列表，确保业务同事一眼能抓到重点。
5. **关键标粗**：对价格、金额、重量、尺寸、体积、地址、邮编、单号、状态、行动建议等关键信息使用 Markdown 加粗。
6. **专有名词理解**：当资料或对话中提到“明日”时，优先按公司渠道“明日之星”理解。
7. **称呼约束**：严禁称呼用户为“老板”或“客户”，统一用自然、内部协作式说法。
"""

COMPACT_STYLE_PROMPT = """
⚠️【全局输出表达规范】（最高级别的核心指令）：
1. **先给结论**：第一句直接给结论，不要先写“好的”“根据你提供的情况”“我来帮你分析一下”这类铺垫。
2. **极致精简**：拒绝长篇寒暄和废话，优先用短句，能一两句说清就不要写成大段。
3. **无法精确也要给判断框架**：如果暂时无法精确回答，第一句先明确“目前无法精确判断/计算”，下一行直接列出 **常见情况** 或 **关键变量**，不要把问题原样踢回给用户。
4. **结构清晰**：优先使用短句和项目列表，方便业务同事快速扫读。
5. **关键标粗**：对价格、金额、重量、尺寸、体积、地址、邮编、单号、状态、行动建议等关键信息使用 Markdown 加粗。
6. **专有名词理解**：当资料或对话中提到“明日”时，优先按公司渠道“明日之星”理解。
7. **称呼约束**：严禁称呼用户为“老板”或“客户”，统一用自然、内部协作式说法。
"""

OUTPUT_PREFERENCE_PATTERN = re.compile(r"^\[输出偏好:(极致精简|详尽展开)\]\s*")


def extract_output_preference(message: str) -> tuple[str, str | None]:
    normalized_message = str(message or "")
    match = OUTPUT_PREFERENCE_PATTERN.match(normalized_message)
    if not match:
        return normalized_message, None

    preference = "long" if match.group(1) == "详尽展开" else "short"
    cleaned_message = normalized_message[match.end() :].strip()
    return cleaned_message, preference


def wants_detailed_answer(
    message: str,
    company_intro_keywords: Iterable[str],
    quote_keywords: Iterable[str],
    explicit_preference: str | None = None,
) -> bool:
    if explicit_preference == "long":
        return True
    if explicit_preference == "short":
        return False
    return (
        any(keyword in message for keyword in DETAIL_KEYWORDS)
        or any(keyword in message for keyword in company_intro_keywords)
        or any(keyword in message for keyword in quote_keywords)
    )


def build_global_style_prompt(wants_detail: bool) -> str:
    return DETAIL_STYLE_PROMPT if wants_detail else COMPACT_STYLE_PROMPT


def build_model_messages(
    system_prompt: str,
    request_message: str,
    history: Optional[List[dict]],
    max_history: int,
    resolved_image_base64: Optional[str],
    needs_realtime: bool,
    exchange_rate_text: str,
) -> List[dict]:
    messages = [{"role": "system", "content": system_prompt}]

    if resolved_image_base64 and "[系统提示]" in request_message:
        messages[0]["content"] += "\n\n**重要指令**：用户上传了图片，请结合图片内容一起理解并回答。"

    if needs_realtime and exchange_rate_text:
        messages[0]["content"] += f"\n\n【系统提示：当前实时汇率：{exchange_rate_text}】"

    allowed_roles = {"user", "assistant"}
    if history:
        safe_history = [
            item
            for item in history
            if item.get("role") in allowed_roles and isinstance(item.get("content"), str)
        ][-max_history:]
        messages.extend(safe_history)

    messages.append({"role": "user", "content": request_message})
    return messages
