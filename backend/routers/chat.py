from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json

from services.llm_client import chat_completion_stream, get_embedding, DOUBAO_MODEL_ENDPOINT
from services.rag_service import search_similar_documents
from services.quote_service import get_quote_data_as_string

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    mode: Optional[str] = "general"
    
async def classify_intent(message: str, history: List[dict] = None) -> str:
    """Classify user intent to determine routing (simple heuristic or LLM based)"""
    import re
    # 1. Regex check for warehouse codes (e.g. ONT8, PHX5) in current message
    wh_pattern = re.compile(r'[A-Z]{3,4}\d+[A-Z]?')
    if wh_pattern.search(message.upper()):
        return "quote"
        
    # 2. Keyward check in current message
    quote_keywords = ["报价", "价格", "运费", "多少钱", "航线", "时效", "价目", "单价", "仓位"]
    for kw in quote_keywords:
        if kw in message:
            return "quote"
            
    # 3. If it's a short message or followup, check recent history for context
    if history and len(history) > 0:
        recent_msgs = [m.get("content", "") for m in history[-4:] if m.get("role") == "user"]
        for old_msg in recent_msgs:
            if wh_pattern.search(old_msg.upper()) or any(kw in old_msg for kw in quote_keywords):
                return "quote"
                
    return "document"

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response based on mode, RAG, and quote tables."""
    
    system_prompt = ""
    
    if request.mode == "coach":
        query_embedding = await get_embedding(request.message)
        similar_docs = search_similar_documents(query_embedding, n_results=5)
        
        context_text = ""
        for i, doc in enumerate(similar_docs):
            context_text += f"---\n[参考来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
            
        system_prompt = f"""你是一个名为“小易”的【物流知识教练】与【资深外贸客户模拟器】。
你的使用者是你们公司的物流业务员或客服。你具备双重身份，请根据对方的发言自动切换：

身份一（知识教练）：当业务员向你请教专业知识、名词解释或业务流程时，你可以参考下方的【内部培训知识库】，也可以发挥你自身的【通用外贸/物流大模型知识库】，用大白话和举例子的方式耐心培训他们。不要完全死板地依赖文档，结合行业常识给出最佳回答。如果有需要，你可以直接为他们提供最新的外部行业经验。
身份二（客户模拟）：当业务员邀请你模拟、跟你练习推销渠道、或是把你当客户沟通时，你可以变身“要求严格、关心时效与价格、偶尔会杀价”的真实客户。提出真实外贸人或跨境电商卖家会问的问题（如查验率、赔偿条款、晚开船怎么处理），锻炼业务员的销售谈判与应变能力。利用你对真实北美、欧洲电商物流的理解进行对抗演练。

无论是哪种角色，都请沉浸其中，尽量避免AI机器感。客户模拟时要循序渐进地追问，不要一口气罗列一堆问题；教练答疑时则要条理分明，便于记忆。

【内部培训知识库片断】：
{context_text}
"""
    else:
        intent = await classify_intent(request.message, request.history)
        if intent == "quote":
            # Handle Quote Query
            search_query = request.message
            if request.history:
                search_query += " " + " ".join([m.get("content", "") for m in request.history[-2:] if m.get("role") == "user"])
            quote_data = get_quote_data_as_string(search_query)
            system_prompt = f"""你是一个名为“小易”的高效物流专家。
**你的使用者是公司的业务同事（销售/客服）。** 请遵循以下职场协同准则：

1. **情绪价值与合伙人语气**：你是同事最可靠的搭档。回答要**专业、暖心、言简意赅**。开头或结尾可以自然地带一句鼓励，如“这票货时效很稳，放心推”、“帮你对比好了，选这个利润更高”等。**严禁称呼用户为“老板”或“客户”**。

2. **核心数据优先**：去掉所有客套废话。直接列出单价、时效、成本对比。

3. **价格单位警示**：【价格体系】里的数字代表**每公斤（Per KG）单价**。

4. **以表为准**：下方展示的【报价表数据】是唯一来源。

5. **老鸟策略建议**：在结尾用 **【💡 老鸟建议】** 给出1-2句关于规避风险或成交技巧的干货，拒绝波浪号。

【系统生效率报价表数据】：
{quote_data}
"""

        else:
            # Handle RAG Document Query
            query_embedding = await get_embedding(request.message)
            similar_docs = search_similar_documents(query_embedding, n_results=5)
            
            context_text = ""
            for i, doc in enumerate(similar_docs):
                context_text += f"---\n[参考来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
                
            system_prompt = f"""你是一个名为“小易”的高效全能企业助手。
**你的使用者是内部同事。** 请遵循以下原则：
1. **暖心协同语气**：像真正懂行的老干将一样交流。**拒绝“老板/客户”称谓**，多用“辛苦了”、“给你找好了”这种体贴的话。
2. **极简主义**：**绝对禁止**大段复制原文。只给最关键的 1, 2, 3 点结论。
3. **格式禁忌**：严禁使用波浪号（~）。

【内部知识检索参考材料】：
{context_text}
"""

    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append history (limited to last 20 for context length)
    if request.history:
        messages.extend(request.history[-20:])
        
    messages.append({"role": "user", "content": request.message})

    async def stream_generator():
        """
        流式输出修复版：使用行缓冲区逐行解析 SSE 数据，
        避免因 chunk 边界截断导致 JSON 解析破碎（如 2000 变成 20）
        """
        line_buffer = ""
        async for raw_chunk in chat_completion_stream(messages):
            line_buffer += raw_chunk
            # 按换行符分割，只处理完整的行
            while "\n" in line_buffer:
                line, line_buffer = line_buffer.split("\n", 1)
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    return
                try:
                    data = json.loads(data_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        choice = data["choices"][0]
                        if "delta" in choice and "content" in choice["delta"]:
                            yield choice["delta"]["content"]
                except json.JSONDecodeError:
                    pass

    return StreamingResponse(stream_generator(), media_type="text/plain; charset=utf-8")
