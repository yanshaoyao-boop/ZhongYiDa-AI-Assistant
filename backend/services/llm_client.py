import os
from dotenv import load_dotenv
import httpx
from pydantic import BaseModel
from typing import List, Optional

load_dotenv()

# We expect the user to have these in their environment or .env file
# DOUBAO_API_KEY=""
# DOUBAO_MODEL_ENDPOINT=""
# DOUBAO_EMBEDDING_ENDPOINT=""

DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
DOUBAO_MODEL_ENDPOINT = os.getenv("DOUBAO_MODEL_ENDPOINT", "")
DOUBAO_VISION_ENDPOINT = os.getenv("DOUBAO_VISION_ENDPOINT", DOUBAO_MODEL_ENDPOINT) # 优先使用视觉端点
DOUBAO_EMBEDDING_ENDPOINT = os.getenv("DOUBAO_EMBEDDING_ENDPOINT", "")
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

class ChatMessage(BaseModel):
    role: str
    content: str

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

async def chat_completion_stream(messages: List[dict]):
    """Generator for streaming Chat Completions (Using standard OpenAI compatible format)"""
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": DOUBAO_MODEL_ENDPOINT,
        "messages": messages,
        "stream": True
    }

    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, headers=headers, json=payload, timeout=60.0) as response:
            if response.status_code != 200:
                body = await response.aread()
                print(f"API Stream Error: {response.status_code} - {body.decode()}")
            response.raise_for_status()
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
    
    # Use standard Chat Completions endpoint for 1.5-vision series
    url = f"{BASE_URL}/chat/completions"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            if response.status_code != 200:
                error_body = response.text
                print(f"Vision API Error ({url}): {response.status_code} - {error_body}")
                return f"[识别失败：模型接入点({DOUBAO_VISION_ENDPOINT})返回了错误。请确认该接入点是否支持视觉问答。]"
            
            data = response.json()
            # Standard OpenAI compatible structure
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Describe image crash: {e}")
            return f"[解析图片时发生系统错误: {str(e)}]"
