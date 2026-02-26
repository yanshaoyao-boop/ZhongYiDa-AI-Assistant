import os
import httpx
from dotenv import load_dotenv

load_dotenv()

DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY")
DOUBAO_EMBEDDING_ENDPOINT = os.getenv("DOUBAO_EMBEDDING_ENDPOINT")
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

def test_embedding():
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": DOUBAO_EMBEDDING_ENDPOINT,
        "input": [
            {
                "type": "text",
                "text": "你好，这是一个测试"
            }
        ]
    }
    print(f"Testing with Endpoint: {DOUBAO_EMBEDDING_ENDPOINT}")
    
    with httpx.Client() as client:
        response = client.post(f"{BASE_URL}/embeddings/multimodal", headers=headers, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_embedding()
