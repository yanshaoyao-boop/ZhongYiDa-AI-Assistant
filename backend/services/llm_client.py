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
    """Generator for streaming Chat Completions"""
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": DOUBAO_MODEL_ENDPOINT,
        "messages": messages,
        "stream": True
    }
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", f"{BASE_URL}/chat/completions", headers=headers, json=payload) as response:
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
        "model": DOUBAO_MODEL_ENDPOINT,
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
        "max_tokens": 512
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=60.0)
        if response.status_code != 200:
            print(f"Vision API Error: {response.status_code} - {response.text}")
            return ""
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
