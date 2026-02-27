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
    """Stream chat response based on RAG and quote tables."""
    
    intent = await classify_intent(request.message, request.history)
    system_prompt = ""
    
    if intent == "quote":
        # Handle Quote Query
        # Pass the concatenated content of recent user messages to assist the search algorithm
        search_query = request.message
        if request.history:
            search_query += " " + " ".join([m.get("content", "") for m in request.history[-2:] if m.get("role") == "user"])
        quote_data = get_quote_data_as_string(search_query)
        system_prompt = f"""你是一个名为“小易”的高效物流专家。
**你的使用者是公司的业务同事（销售/客服）而非外部客户。** 请必须遵循以下职场协同准则：

1. **平等专业的同事语气**：说话要干练、专业且亲切。**绝对禁止称呼用户为“老板”或“客户”**，应以“同事”、“伙伴”相称或直接进入正题。像是在公司内部群里回复同事询价一样。

2. **绝对禁止“几块钱总价”的幻觉**：【价格体系】里的数字（如 5.2, 9.7 等）代表的是**每公斤（Per KG）单价**。如果未达起收重量，请按起收重量计算总价。

3. **以表为准，拒绝外部幻觉**：下方展示的【系统最新报价表数据】是唯一的真实来源。请**为你找到的所有符合时效要求的渠道计算价格并对比**，帮同事做好辅助决策。

4. **时效精准匹配与“只推最具性价比”原则**：当同事说“可以接受50天到”时，说明这票货追求极致低价。**绝对不要**推那些 20 天、30 天的高价快船，只需筛选 2-3 个单价最低的普船方案即可。

5. **强制添加【老鸟建议】**：在结尾加粗显示 **【💡 老鸟建议】：**。作为资深前辈，给业务同事提供关于如何规避风险、如何引导客户凑重以利润最大化的专业建议。

6. **格式禁忌**：严禁使用波浪号（~）。

【系统最新生效率报价表数据】：
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
**你的使用者是公司内部同事。** 请遵循以下内部协同原则：
1. **职场协同语气**：用轻松、专业的同事对练/互助口吻回答。**严禁使用“老板”、“客户”等尊称。**
2. **极度精简，拒绝搬运**：提取关键干货结论即可。**绝对禁止**大段复制原文。你要的是“讲重点”。
3. **灵活兜底**：如果在资料里找不到答案，直接利用你自带的大模型全能知识库给同事一个合理的专业建议。
4. **格式禁忌**：严禁使用波浪号（~）。

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
