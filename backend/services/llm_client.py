import os
import json
from dotenv import load_dotenv
import httpx
from pydantic import BaseModel
from typing import List, Optional
import asyncio

load_dotenv()

# --- 豆包配置 (由于 RAG 和 Vision 继续使用豆包，保留原配置) ---
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
DOUBAO_MODEL_ENDPOINT = os.getenv("DOUBAO_MODEL_ENDPOINT", "")
DOUBAO_BOT_ID = os.getenv("DOUBAO_BOT_ID", "")
DOUBAO_VISION_ENDPOINT = os.getenv("DOUBAO_VISION_ENDPOINT", DOUBAO_MODEL_ENDPOINT)
DOUBAO_EMBEDDING_ENDPOINT = os.getenv("DOUBAO_EMBEDDING_ENDPOINT", "")
DOUBAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# --- MiniMax 配置 (用于主大脑，解决幻觉和指令执行差的问题) ---
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = "https://api.minimaxi.com/v1"
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")

# --- 配置自检提示 ---
if not DOUBAO_API_KEY:
    print("⚠️  [警告] 系统未发现 DOUBAO_API_KEY，Embedding 和 Vision 功能将失效！")
if not MINIMAX_API_KEY:
    print("⚠️  [警告] 系统未发现 MINIMAX_API_KEY，主对话功能将失效！请检查 .env 文件。")

# 按事件循环复用 HTTP 客户端，避免跨 loop 复用导致 "Event loop is closed"
_http_clients: dict[int, httpx.AsyncClient] = {}


def resolve_llm_provider(
    *,
    use_bot: bool,
    use_search: bool,
    minimax_api_key: Optional[str] = None,
) -> str:
    """Resolve provider for current request."""
    key = MINIMAX_API_KEY if minimax_api_key is None else str(minimax_api_key)
    has_minimax_key = bool(key.strip())
    if use_bot or use_search or not has_minimax_key:
        return "doubao"
    return "minimax"

def get_client():
    loop = asyncio.get_running_loop()
    loop_key = id(loop)
    client = _http_clients.get(loop_key)
    if client is None or client.is_closed:
        client = httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0))
        _http_clients[loop_key] = client
    return client

async def close_client():
    """优雅关闭当前进程持有的 AsyncClient 连接池"""
    for loop_key, client in list(_http_clients.items()):
        try:
            if not client.is_closed:
                await client.aclose()
        except RuntimeError as exc:
            if "Event loop is closed" not in str(exc):
                raise
        finally:
            _http_clients.pop(loop_key, None)

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
    """Get embedding from Doubao API (RAG 保持原样以维持索引兼容)"""
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{DOUBAO_BASE_URL}/embeddings/multimodal"
    payload = {
        "model": DOUBAO_EMBEDDING_ENDPOINT,
        "input": [{"type": "text", "text": text}]
    }
    
    client = get_client()
    response = await client.post(url, headers=headers, json=payload, timeout=30.0)
    if response.status_code != 200:
        print(f"Embedding API Error: {response.status_code} - {response.text}")
    response.raise_for_status()
    data = response.json()
    if isinstance(data.get("data"), list):
        return data["data"][0]["embedding"]
    else:
        return data["data"]["embedding"]


async def chat_completion_stream(
    messages: List[dict], 
    use_bot: bool = False, 
    use_search: bool = False, 
    model_endpoint: str = None,
    temperature: float = 0.7
):
    """主脑流式对话处理：根据需求选择 MiniMax 或 豆包"""
    # 如果指定了 bot、搜索或者没有 MiniMax Key，则降级使用豆包
    provider = resolve_llm_provider(use_bot=use_bot, use_search=use_search)
    use_doubao = provider == "doubao"
    
    if use_doubao:
        headers = {
            "Authorization": f"Bearer {DOUBAO_API_KEY}",
            "Content-Type": "application/json"
        }
        current_model = model_endpoint or DOUBAO_MODEL_ENDPOINT
        
        if use_search:
            url = f"{DOUBAO_BASE_URL}/responses"
            payload = {
                "model": current_model,
                "input": messages, 
                "tools": [{"type": "web_search"}],
                "stream": True,
                "temperature": temperature
            }
        elif use_bot and DOUBAO_BOT_ID:
            url = f"{DOUBAO_BASE_URL}/bots/chat/completions"
            model = DOUBAO_BOT_ID
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
                "stream_options": {"include_usage": True},
                "temperature": temperature
            }
        else:
            url = f"{DOUBAO_BASE_URL}/chat/completions"
            payload = {
                "model": current_model,
                "messages": messages,
                "stream": True,
                "temperature": temperature
            }
    else:
        # 使用 MiniMax 进行通用对话，解决豆包的幻觉和指令执行弱的问题
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }
        url = f"{MINIMAX_BASE_URL}/chat/completions"
        payload = {
            "model": MINIMAX_MODEL,
            "messages": messages,
            "stream": True,
            "temperature": temperature
        }

    payload = {k: v for k, v in payload.items() if v is not None}

    client = get_client()
    async with client.stream("POST", url, headers=headers, json=payload, timeout=90.0) as response:
        if response.status_code != 200:
            body = await response.aread()
            error_text = body.decode()
            print(f"API Stream Error ({url}): {response.status_code} - {error_text}")
            
            try:
                err_json = json.loads(error_text)
                detail = err_json.get("error", {}).get("message", error_text)
            except:
                detail = error_text
                
            yield f"data: {json.dumps({'error': {'message': f'API Error {response.status_code}: {detail}'}})}\n\n"
            return

        async for line in response.aiter_lines():
            if line:
                yield line + "\n"

async def describe_image(image_base64: str) -> str:
    """视觉识别目前仍保留使用豆包模型（集成度高）"""
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
    
    url = f"{DOUBAO_BASE_URL}/chat/completions"
    
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
    """生成对练剧本（对逻辑和指令执行要求极高，默认优先切换 MiniMax）"""
    hint_prompt = ""
    if hint:
        hint_prompt = (
            f"【归类建议】：这段内容来自文本文件 '{hint}'，请在生成 'category' 字段时，"
            "严格优先输出“航线 · 情景”格式，其中航线从 [美国, 欧洲, 一件代发] 选择，"
            "情景从 [询价, 纠纷] 选择。\n"
        )

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
- "category": 航线 · 情景。
  - **航线**：必须从 [美国, 欧洲, 一件代发] 中选一。
  - **情景**：必须从 [询价, 纠纷] 中选一。
  - **示例**：美国 · 询价
- "emoji": 代表该场景的 Emoji
- "persona": 详细客户画像（性格、沟通雷点），可自由发挥，不再限制为固定人设标签。
- "background": 对话背景（禁止出现人称错乱，描述当前场景）
- "cargo_details": {{"item": "品名", "qty": "件数", "gw_kg": "单件重量", "size_cm": "L*W*H", "destination": "目的仓库/邮编", "hidden_issue": "预测陷阱"}}
- "success_criteria": 业务员必须做到的 3 件事。
- "prompt": 【开场白】小易（买家）的第一句台词。若是“询价”情景，直接围绕价格/时效/附加费发问；若是“纠纷”情景，直接围绕异常/投诉/赔付切入。
"""

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY if MINIMAX_API_KEY else DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{MINIMAX_BASE_URL}/chat/completions" if MINIMAX_API_KEY else f"{DOUBAO_BASE_URL}/chat/completions"
    
    payload = {
        "model": MINIMAX_MODEL if MINIMAX_API_KEY else DOUBAO_MODEL_ENDPOINT,
        "messages": [
            {"role": "system", "content": "你是一个只输出 JSON 数据、深谙货代江湖的分析师。请确保输出是一个合法的 JSON 对象。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }
    
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
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"!! LLM Parsing Error: {str(e)}")
        print(f"!! Raw Content: {content if 'content' in locals() else 'None'}")
        raise e
