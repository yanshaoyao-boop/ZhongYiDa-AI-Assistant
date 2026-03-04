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

async def analyze_coach_case(raw_text: str, hint: str = "") -> dict:
    """Analyze raw chat logs to generate a structured coach case."""
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    hint_prompt = ""
    if hint:
        hint_prompt = f"【归类建议】：这段内容来自文本文件 '{hint}'，请在生成 'category' 字段时，严格优先从 [报价拉锯战, 异常纠纷处理, 业务挖坑排雷, 逼单客情维护] 中选择最符合文件名意图的标签。\n"

    prompt = f"""你是一个名为“仲易达首席剧本架构师”的资深分析模型。
你需要把下面这段聊天记录，将其“参数化”并“深度重塑”为一个具有高度博弈价值的【实战对练剧本】。

{hint_prompt}
【原始材料】：
{raw_text}

【重塑要求】：
1. **去特定人名化**：
   - ⚠️ **核心指令**：禁止在输出内容中出现“老沈”、“小王”、“老张”等具体姓名。
   - 客户在开口时，如果是为了投诉或质问，应直接切入正题，或者称呼对方为“小老弟”、“你们家经理”、“你家”。
   
2. **参数化货物（Hidden Cargo Details）**：
   - 你必须为本场景“脑补”一套极其精确的货物参数。包含：品名、件数(CTNS)、单件实重(KG)、单件尺寸(CM, L*W*H)。
   - **设计逻辑陷阱**：例如品名属于“敏感货”但表面伪装成“普货”、或者“体积重大于实重”的泡货、或者地址属于“极偏远库房”。

3. **核心业务考点（Learning Focus）**：
   - 明确本关考察业务员的什么能力。

JSON 字段定义：
- "name": 剧本标题
- "difficulty": 难度等级 [Easy, Medium, Hard]
- "category": 航线 · 人设 · 科目。
  - **航线**：必须从 [美国线, 欧洲线] 中选一。
  - **人设**：必须从 [行业小白, 江湖老手] 中选一。
  - **科目**：必须从 [报价拉锯战, 异常纠纷处理, 业务挖坑排雷, 逼单客情维护] 中选一。
  - **示例**：美国线 · 行业小白 · 报价拉锯战
- "emoji": 代表该场景的 Emoji
- "persona": 详细人设描绘（性格、沟通雷点）。
  ⚠️ **语气差异指令**：
  - **行业小白**：礼貌、犹豫、爱问为什么、对缩写词（如CBM, DDP）感到困惑、容易被专业话术唬住但也容易因为听不懂而流失。
  - **江湖老手**：语气简练、强势、满嘴专业黑话、随时拿别家低价压你、非常计较查验费/偏远费等细节、会钓鱼执法。
- "background": 对话背景（禁止出现人称错乱，描述当前场景）
- "cargo_details": {{"item": "品名", "qty": "件数", "gw_kg": "单件重量", "size_cm": "L*W*H", "destination": "目的仓库/邮编", "hidden_issue": "预测陷阱"}}
- "success_criteria": 业务员必须做到的 3 件事。
- "prompt": 【开场白】小易（买家）的第一句台词。要求：严格符合上述【语气差异指令】。江湖老手直接甩货盘问价格，小白先问能不能发货。
"""

    payload = {
        "model": DOUBAO_MODEL_ENDPOINT,
        "messages": [
            {"role": "system", "content": "你是一个只输出 JSON 数据、深谙货代江湖的分析师。请确保输出是一个合法的 JSON 对象。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }
    
    url = f"{BASE_URL}/chat/completions"
    
    client = get_client()
    try:
        response = await client.post(url, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        
        # 提取 JSON 部分
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        else:
            # 如果没找到 {}，尝试清理 markdown 标记
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"!! LLM Parsing Error: {str(e)}")
        print(f"!! Raw Content: {content if 'content' in locals() else 'None'}")
        raise e
