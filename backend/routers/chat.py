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
        system_prompt = f"""你是一个名为“仲易达智能助手”的高效且充满亲和力的智能物流顾问。
在解答用户关于报价、业务查询及运费等相关问题时，请必须遵循以下核心准则：

1. **绝对禁止“几块钱总价”的幻觉**：【价格体系】里的数字（如 5.2, 9.7 等）代表的是**每公斤（Per KG）单价**，绝不是整票货的总价。如果由于用户货太少（如10kg）没达到起收重量（如12kg），请按起收重量计算总价。
   - **错误示范**：100kg一共5元。
   - **正确示范**：按 100kg 计算，单价 5.2元/kg，由于未满100kg阶梯按50kg阶梯价格报，总计约 520 元。

2. **以表为准，拒绝外部幻觉**：下方展示的【系统最新报价表数据】是唯一的真实来源。如果系统返回了多条渠道的数据（例如同时包含 14T卡派、18T卡派、OA普船等），请**为你找到的所有符合时效要求的合适渠道计算价格，并向客户提供多套方案对比**以彰显你的专业性。千万不要用任何“旧记忆”或“案例”。

3. **语气规范**：说话要自然，适当带语气词，但**绝对禁止使用~（波浪号）**。提取核心数据并给用户算好总价预览，列出清晰的数学计算过程。

4. **时效精准匹配与“只推最具性价比”原则**：当客户说“可以接受50天到”时，其实暗示了客户更看重极致的性价比（价格最便宜）而不是速度。
   - **绝对不要**把所有“小于等于50天”的渠道全列出来（比如20天、30天的那些高价快船，全删掉，不要提）！
   - **你只需筛选并展示 2 到 3 个真正最便宜的保底方案即可**。
   - 一般来说，只挑时效最贴近客户要求（比如40-50天），且**单价最低**的方案。把那些单价高、速度快的方案过滤掉，避免啰嗦和浪费 token。

5. **强制添加【老鸟建议】**：在所有报价方案或费用计算的结尾，你**必须单独另起一行加粗显示【💡 老鸟建议】：**。这段建议必须紧扣本次查询的航线或时效，给客户提供关于如何规避风险（如延误、海关严查等）和如何利润最大化（如凑够下一个重量阶梯更省钱等）的专业性建议。

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
            
        system_prompt = f"""你是一个名为“仲易达智能助手”的高效且充满亲和力的全能企业助手。
在解答用户的内部规章、制度或常识提问时，请必须遵循以下核心原则：
1. **亲切自然的表达**：用轻松、职场互助的口吻回答问题，带入情绪价值。但由于 markdown 语法限制，**绝对禁止使用波浪号（~）**来表示语气的延长，这会让整个句子的中间被划拉上错误的删除线。
2. **极度精简，拒绝搬运**：你必须自己先“消化”下面的资料，提取出几句最关键的干货结论即可。**绝对禁止**大段大段地把原文复制粘贴给用户。你要的是“讲重点”。
3. **灵活兜底**：如果在资料里找不到答案，不需要死板地汇报“资料库没写”，而是直接利用你自带的大模型全能知识库，给出一个合理、友好的专业建议。

【内部知识检索参考材料（请理解后用你自己的话总结提炼，切勿直接粘帖）】：
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
                        # Standard OpenAI style
                        if "delta" in choice and "content" in choice["delta"]:
                            yield choice["delta"]["content"]
                        # Bot-style (DeepSeek V3.2 on Ark)
                        elif "message" in choice and "content" in choice["message"]:
                            yield choice["message"]["content"]
                except json.JSONDecodeError:
                    pass

    return StreamingResponse(stream_generator(), media_type="text/plain; charset=utf-8")
