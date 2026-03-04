import os
import json
from dotenv import load_dotenv
import httpx
from pydantic import BaseModel
from typing import List, Optional
import asyncio

load_dotenv()

# We expect the user to have these in their environment or .env file
# DOUBAO_API_KEY=""
# DOUBAO_MODEL_ENDPOINT=""
# DOUBAO_EMBEDDING_ENDPOINT=""

DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
DOUBAO_MODEL_ENDPOINT = os.getenv("DOUBAO_MODEL_ENDPOINT", "")
DOUBAO_BOT_ID = os.getenv("DOUBAO_BOT_ID", "")
DOUBAO_VISION_ENDPOINT = os.getenv("DOUBAO_VISION_ENDPOINT", DOUBAO_MODEL_ENDPOINT)
DOUBAO_EMBEDDING_ENDPOINT = os.getenv("DOUBAO_EMBEDDING_ENDPOINT", "")
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# 全局复用 HTTP 客户端平衡连接池 (Task 2)
_http_client = httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0))

def get_client():
    return _http_client

class ChatMessage(BaseModel):
    role: str
    content: str

async def get_web_search(query: str) -> str:
    """Fallback search using DuckDuckGo directly"""
    try:
        from ddgs import DDGS
        def run_search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=3))
        results = await asyncio.to_thread(run_search)
        if not results:
            return "无相关信息。"
            
        compiled = ""
        for i, res in enumerate(results, 1):
            compiled += f"{i}. {res.get('title')}: {res.get('body')}\n"
        return compiled
    except Exception as e:
        print(f"DDG Search error: {e}")
        return ""

async def get_embedding(text: str) -> List[float]:
    """Get embedding from Doubao Multimodal API"""
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    # Using multimodal_embeddings endpoint as vision models require it
    url = f"{BASE_URL}/embeddings/multimodal"
    payload = {
        "model": DOUBAO_EMBEDDING_ENDPOINT,
        "input": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    
    # Improved: Just use the global client directly for better performance
    client = get_client()
    response = await client.post(url, headers=headers, json=payload, timeout=30.0)
    if response.status_code != 200:
        print(f"Embedding API Error: {response.status_code} - {response.text}")
    response.raise_for_status()
    data = response.json()
    # Multimodal response structure returns {"data": {"embedding": [...]}, ...} instead of a list inside "data"
    if isinstance(data.get("data"), list):
        return data["data"][0]["embedding"]
    else:
        return data["data"]["embedding"]


async def chat_completion_stream(messages: List[dict], use_bot: bool = False, use_search: bool = False, model_endpoint: str = None):
    """Generator for streaming Chat Completions (Using standard OpenAI compatible format or Responses API)"""
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    current_model = model_endpoint or DOUBAO_MODEL_ENDPOINT
    
    if use_search:
        # Use Responses API with full conversation history
        url = f"{BASE_URL}/responses"
        # Corrected: Responses API uses 'input' instead of 'messages'
        payload = {
            "model": current_model,
            "input": messages, 
            "tools": [{"type": "web_search"}],
            "stream": True
        }
    elif use_bot and DOUBAO_BOT_ID:
        url = f"{BASE_URL}/bots/chat/completions"
        model = DOUBAO_BOT_ID
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True}
        }
    else:
        url = f"{BASE_URL}/chat/completions"
        payload = {
            "model": current_model,
            "messages": messages,
            "stream": True
        }

    # Clean None values in payload
    payload = {k: v for k, v in payload.items() if v is not None}

    client = get_client()
    async with client.stream("POST", url, headers=headers, json=payload, timeout=90.0) as response:
        if response.status_code != 200:
            body = await response.aread()
            error_text = body.decode()
            print(f"API Stream Error ({url}): {response.status_code} - {error_text}")
            
            # Try to parse as JSON to get a cleaner message
            try:
                err_json = json.loads(error_text)
                detail = err_json.get("error", {}).get("message", error_text)
            except:
                detail = error_text
                
            yield f"data: {json.dumps({'error': {'message': f'API Error {response.status_code}: {detail}'}})}\n\n"
            return

        async for chunk in response.aiter_text():
            yield chunk

async def describe_image(image_base64: str) -> str:
    """Use Doubao Vision model to describe an image for better OCR/understanding"""
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": DOUBAO_VISION_ENDPOINT,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请简要描述这张图片中的内容，包含文字、图表或重要信息，以便作为文本搜索的参考。直接输出描述内容即可。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1024
    }
    
    url = f"{BASE_URL}/chat/completions"
    
    client = get_client()
    try:
        response = await client.post(url, headers=headers, json=payload, timeout=60.0)
        if response.status_code != 200:
            error_body = response.text
            print(f"Vision API Error ({url}): {response.status_code} - {error_body}")
            return f"[识别失败：模型接入点({DOUBAO_VISION_ENDPOINT})返回了错误。请确认该接入点是否支持视觉问答。]"
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Describe image crash: {e}")
        return f"[解析图片时发生系统错误: {str(e)}]"

async def analyze_coach_case(raw_text: str) -> dict:
    """Analyze raw chat logs to generate a structured coach case.
    Strictly classified into: [美国线, 欧洲线] AND [精明比价派, 强势大货主, 麻烦纠纷型].
    Deeply 'washes' (expands) the content to add hidden professional details and market variables.
    """
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""你是一个名为“老沈”的资深货代江湖分析师，眼光毒辣，深谙利润背后的算计。
你需要把下面这段聊天记录，将其“深度重塑”为一个高难度的专业对练剧本。

【原始材料】：
{raw_text}

【深度重塑要求（核心指令）】：
1. **强制注入“硬核货盘”**：
   - 即使原记录没提，你也必须为本场景“脑补”出一套精准的货物参数：件数、单箱尺寸(cm)、单箱重量(kg)、货物品名（带点“坑”的品名，如：平衡车、纯电池、仿牌等）。
   - 设计一个**计费重陷阱**：例如体积重刚好比实重大 30%，考察业务员是否发现并按体积计费。

2. **强制注入“报价雷区”**：
   - 如果是美国线/欧洲线，必须设定一个具体的**亚马逊仓库（如 ONT8/LGB8/TEB9）**或一个 5 位邮编。
   - 设定这个地址是否为“偏远”或“极偏远”，考察业务员是否去查地址库。

3. **设定客户性格与博弈深度**：
   - 你的性格可以多变，但你的目的必须是：**套出底价、隐瞒货物属性、或者对计费重计算表示质疑**。
   - 严禁做只有情绪的“泼妇”，要做懂行的、会压价的、甚至会拿别家虚假低价来诈你的“职业买手”。

4. **输出格式**：JSON。

JSON 字段定义：
- "name": 剧本标题（如：带磁平衡车的体积重罗生门）
- "category": 线别 · 人设（如：美国线 · 精明比价派）
- "emoji": 代表该场景的 Emoji
- "persona": 详细的人设（含性格地雷、其真实的隐藏货盘、拒绝配合的借口）
- "background": 深度业务背景（含具体的 Piece/Weight/Dim 参数、目的地详细地址）
- "conflict": 核心矛盾（本题的‘考点’：是要他加附加费？还是要他算体积重？还是发现瞒报？）
- "success_criteria": 业务员必须问出的 3 个核心要素才算及格。
- "prompt": 系统初始 Prompt（你以此身份直接开口，第一句必须带着模糊的货盘信息发起突袭，例如：‘老板，我这有 20 块滑板车，发美国 ONT8，给个数？’）
"""

    payload = {
        "model": DOUBAO_MODEL_ENDPOINT,
        "messages": [
            {"role": "system", "content": "你是一个只输出 JSON 数据、深谙货代江湖的分析师。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }
    
    url = f"{BASE_URL}/chat/completions"
    
    client = get_client()
    response = await client.post(url, headers=headers, json=payload, timeout=60.0)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    return json.loads(content)
