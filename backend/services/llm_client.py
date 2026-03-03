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
    async with httpx.AsyncClient() as client:
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
        # Use Responses API as suggested by Volcengine support for models that have grayed out search in UI
        url = f"{BASE_URL}/responses"
        # For Responses API, we use 'model', 'input', and 'tools'
        # Responses API usually takes the last user message as 'input'
        user_input = messages[-1]["content"] if messages else ""
        payload = {
            "model": current_model,
            "input": user_input,
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

    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, headers=headers, json=payload, timeout=90.0) as response:
            if response.status_code != 200:
                body = await response.aread()
                print(f"API Stream Error ({url}): {response.status_code} - {body.decode()}")
                yield f"data: {json.dumps({'error': 'API call failed'})}\n\n"
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
    
    async with httpx.AsyncClient() as client:
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
    
    prompt = f"""你是一个名为“老沈”的资深货代江湖分析师，性格辛辣、眼光毒辣。
你需要把下面这段干巴巴的对练记录，将其“深度清洗”并“暴力扩充”为一个真实的实战剧本。

【原始材料】：
{raw_text}

【深度重塑要求】：
1. **严格分类**：
   - 航线：必须判定为 [美国线] 或 [欧洲线] 之一。
   - 客户人设：必须从以下三类中选一：
     * 【精明比价派】：核心冲突是价格、杂费、利润点。
     * 【强势大货主】：核心冲突是舱位保证、时效赔偿、月结账期。
     * 【麻烦纠纷型】：核心冲突是计费重争议、查验费分摊、小白客户的理解障碍。

2. **补完逻辑**：脑补出背后完整的业务逻辑：航线、品名、具体的市场实时变数（如LA罢工、红海绕寄等）。
3. **输出格式**：JSON 格式。

JSON 字段定义：
- "name": 剧本标题（如：加派费纠纷、带磁瞒报、体积重罗生门）
- "category": 格式必须为“线别 · 客户人设”（如：美国线 · 精明比价派）
- "emoji": 代表该场景的 Emoji
- "persona": 详细的人设描述（基于分类特征，描述其性格、沟通地雷、隐藏动机）
- "background": 深度业务背景（详细模拟：航线、季节、具体的货盘信息）
- "conflict": 核心矛盾点（陷阱所在，考察业务员的什么能力，给出的江湖策略）
- "success_criteria": 成功/避坑标准
- "prompt": 系统初始 Prompt（要求AI以此身份开始对话，第一句话直接开战，不要废话）
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
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return json.loads(content)
