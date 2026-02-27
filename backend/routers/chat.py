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
    
async def classify_intent(message: str) -> str:
    """Classify user intent to determine routing (simple heuristic or LLM based)"""
    # Simply check keywords to decide routing
    quote_keywords = ["报价", "价格", "运费", "多少钱", "航线", "时效", "价目"]
    for kw in quote_keywords:
        if kw in message:
            return "quote"
    return "document"

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response based on RAG and quote tables."""
    
    intent = await classify_intent(request.message)
    system_prompt = ""
    
    if intent == "quote":
        # Handle Quote Query
        quote_data = get_quote_data_as_string()
        system_prompt = f"""你是一个名为“仲易达智能助手”的高效且充满亲和力的智能全能助手。
在解答用户关于报价、业务查询及运费等相关问题时，请遵循以下原则：
1. **表达方式与情绪价值**：说话要轻松、自然、有温度，可以适当带点语气词（如“呢”、“啦”、“哦”）。但**绝对禁止使用波浪号（~）**来表达情绪的延长，否则您的回答在前端会变成错误的删除线格式。
2. **言简意赅，拒绝长篇大论**：绝对**不要**把原表的长段内容直接复制粘贴过来。你要做的是提取核心数据，然后用一两句话直接告诉用户最终结果。
3. **查阅与延伸**：优先详细查阅下面提供的“系统最新报价表数据”。如果表内能查到，帮用户算好、总结好再发出来；如果查不到，或者用户在问通用外贸/物流知识，请直接动用你的广博知识大方解答，绝不生硬拒绝。

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
    
    # Append history (limited to last 6 for context length)
    if request.history:
        messages.extend(request.history[-6:])
        
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
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                except json.JSONDecodeError:
                    pass

    return StreamingResponse(stream_generator(), media_type="text/plain; charset=utf-8")
