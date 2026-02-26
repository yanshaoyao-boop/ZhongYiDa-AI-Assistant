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
        system_prompt = f"""你是一个名为“仲易达智能助手”的高级物流报价与业务问答AI。
请根据以下提供的最新报价表数据回答用户关于航班、时效、价格等问题。如果报价表里没有，请如实回答“暂未查到相关报价”。

以下是系统里当前生效的报价表数据参考：
{quote_data}
"""
    else:
        # Handle RAG Document Query
        query_embedding = await get_embedding(request.message)
        similar_docs = search_similar_documents(query_embedding, n_results=5)
        
        context_text = ""
        for i, doc in enumerate(similar_docs):
            context_text += f"---\n[参考来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
            
        system_prompt = f"""你是一个名为“仲易达智能助手”的高级企业客服与业务规章咨询AI。
请严格根据以下公司内部资料检索结果回答用户问题。不要捏造资料库以外的业务信息。
如果通过检索到的资料无法回答用户的问题，请友善地告知用户当前知识库尚未收录该信息。

【内部知识检索结果如下】：
{context_text}
"""

    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append history (limited to last 6 for context length)
    if request.history:
        messages.extend(request.history[-6:])
        
    messages.append({"role": "user", "content": request.message})

    async def stream_generator():
        # Just yield data format suitable for SSE or basic streaming string chunks
        async for chunk in chat_completion_stream(messages):
            # Parse OpenAI format JSON chunks provided by Doubao
            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                except json.JSONDecodeError:
                    pass

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
