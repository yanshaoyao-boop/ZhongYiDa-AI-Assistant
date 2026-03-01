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


async def chat_completion_stream(messages: List[dict], use_bot: bool = False, use_search: bool = False):
    """Generator for streaming Chat Completions (Using standard OpenAI compatible format or Responses API)"""
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    if use_search:
        # Use Responses API as suggested by Volcengine support for models that have grayed out search in UI
        url = f"{BASE_URL}/responses"
        # For Responses API, we use 'model', 'input', and 'tools'
        # Responses API usually takes the last user message as 'input'
        user_input = messages[-1]["content"] if messages else ""
        payload = {
            "model": DOUBAO_MODEL_ENDPOINT,
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
        model = DOUBAO_MODEL_ENDPOINT
        payload = {
            "model": model,
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
