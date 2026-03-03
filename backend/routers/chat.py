from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio
from datetime import datetime
import os
import re

from services.llm_client import chat_completion_stream, get_embedding, DOUBAO_MODEL_ENDPOINT
from services.rag_service import search_similar_documents
from services.quote_service import get_quote_data_as_string

# 定义 DeepSeek 接入点 (这里复用一个理性的模型接入点，用户可在 .env 中配置)
DEEPSEEK_ENDPOINT = os.getenv("DEEPSEEK_MODEL_ENDPOINT", DOUBAO_MODEL_ENDPOINT)

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    mode: Optional[str] = "general"
    image_base64: Optional[str] = None
    use_deepseek: Optional[bool] = False
    
async def classify_intent(message: str, history: List[dict] = None) -> str:
    """Classify user intent to determine routing (simple heuristic or LLM based)"""
    wh_pattern = re.compile(r'[A-Z]{3,4}\d+[A-Z]?')
    
    # 1. Remote address check (High Priority)
    remote_keywords = ["偏远", "加费", "超编", "极偏", "邮编", "地址库", "哪里", "远不远", "送吗", "偏吗", "超区"]
    internal_keywords = ["赚钱", "发展", "工资", "提成", "奖金", "制度", "晋升", "怎么赚", "搞钱"]
    has_remote_kw = any(kw in message for kw in remote_keywords)
    has_zip = re.search(r'(?<!\d)\d{5}(?!\d)', message)
    has_wh = wh_pattern.search(message.upper())
    
    if has_remote_kw and (has_zip or has_wh):
        return "address"
    
    # 特殊情况：如果用户直接甩一个 5 位邮编过来，也极大概率是问偏远
    if re.match(r'^\d{5}$', message.strip()):
        return "address"

    # 2. Quote check
    if wh_pattern.search(message.upper()):
        return "quote"
    
    quote_keywords = ["报价", "价格", "运费", "多少钱", "航线", "时效", "价目", "单价", "仓位"]
    for kw in quote_keywords:
        if kw in message:
            return "quote"
            
    # 3. Knowledge Base / Capabilities check (High Priority for self-intro)
    kb_keywords = ["介绍", "你是谁", "你能做什么", "做哪些事", "你会干啥", "怎么用", "操作说明", "技巧", "什么事"]
    if any(kw in message for kw in kb_keywords):
        return "document"

    # 4. Social/Chitchat check
    social_keywords = ["你好", "哈喽", "笑话", "讲个", "唱个", "调戏", "暖场", "开心", "好玩"]
    continuation_keywords = ["换一个", "再来", "继续", "下一个", "换个"]
    if any(kw in message for kw in social_keywords):
        return "social"

    # 4. Contextual inheritance for short commands
    if len(message.strip()) <= 4 and any(kw in message for kw in continuation_keywords):
        if history and len(history) > 0:
            last_ai_msg = ""
            for msg in reversed(history):
                if msg.get("role") == "assistant":
                    last_ai_msg = msg.get("content", "")
                    break
            # 如果 AI 上一句话看起来像是在讲笑话或闲聊（简单启发式判断）
            if any(kw in last_ai_msg for kw in ["笑话", "哈", "有趣", "嘿嘿", "故事"]):
                return "social"
            if any(kw in last_ai_msg for kw in quote_keywords) or wh_pattern.search(last_ai_msg.upper()):
                return "quote"

    # 5. Internal specific keywords (Bonus for document search)
    if any(kw in message for kw in internal_keywords):
        return "document"

    # 6. If it's a short message or followup, check recent history for context
    if history and len(history) > 0:
        recent_msgs = [m.get("content", "") for m in history[-4:] if m.get("role") == "user"]
        for old_msg in recent_msgs:
            if wh_pattern.search(old_msg.upper()) or any(kw in old_msg for kw in quote_keywords):
                return "quote"
                
    return "document"

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response based on mode, RAG, and quote tables."""
    
    # Process image if present
    needs_realtime = False
    if request.image_base64:
        from services.llm_client import describe_image
        try:
            image_desc = await describe_image(request.image_base64)
            if image_desc:
                img_context = f"[系统提示：用户上传了一张图片，大模型的视觉解析结果如下：\n{image_desc}]\n\n"
                request.message = img_context + request.message
        except Exception as e:
            print(f"Image processing error: {e}")
            request.message = f"[图片解析失败，请提醒用户重新上传] " + request.message

    system_prompt = ""
    
    if request.mode == "coach":
        # 检测是否是启动挑战场景的指令 (从当前消息或历史消息中寻找最近的指令)
        case_context = ""
        challenge_msg = request.message
        if request.history:
            # 优先从当前消息找，找不到就从历史记录倒序找最近的一个启动指令
            if not re.search(r'我要挑战【(.*?)】场景', challenge_msg):
                for h in reversed(request.history):
                    if h.get("role") == "user" and "我要挑战【" in (h.get("content") or ""):
                        challenge_msg = h.get("content")
                        break
        
        match = re.search(r'我要挑战【(.*?)】场景', challenge_msg)
        if match:
            scene_name = match.group(1)
            # 加载剧本数据
            cases_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "coach_cases.json")
            if os.path.exists(cases_path):
                try:
                    with open(cases_path, "r", encoding="utf-8") as f:
                        cases = json.load(f)
                        for c in cases:
                            if c.get("name") == scene_name:
                                case_context = f"""
### 🚨 当前正在执行模拟实战剧本 🚨
你必须完全沉浸在以下【客户模拟】身份中：

【剧本名称】：{c.get('name')}
【客户身份】：{c.get('persona')}
【业务背景】：{c.get('background')}
【核心矛盾点】：{c.get('conflict')}
【开场白（必须由此开始）】：{c.get('prompt')}

**行动准则（优先级最高）**：
1. 你现在是该场景下的【客户】，用户是你的【业务员】。
2. 禁止出现“我是助手”、“我可以帮您演练”等自述语。
3. 请严格按照剧本要求的语气（如：愤怒、焦急、精明等）进行博弈。
4. 如果这是你（客户）说的第一句话，请务必【完全原样输出】剧本中的【开场白】内容；如果已经开始博弈，请根据剧本逻辑灵活刁难业务员。
"""
                                break
                except Exception as e:
                    print(f"Error loading coach cases: {e}")

        query_embedding = await get_embedding(request.message)
        similar_docs = search_similar_documents(query_embedding, n_results=5)
        
        context_text = ""
        for i, doc in enumerate(similar_docs):
            context_text += f"---\n[参考来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
            
        if request.message.startswith("【结束对练】"):
            # 获取历史对话用于检索报价
            history_text = " ".join([m.get("content", "") for m in request.history if m.get("content")])
            query_text = history_text[-500:] if len(history_text) > 500 else history_text
            quote_data = get_quote_data_as_string(query_text)
            
            system_prompt = f"""你当前处于【导师复盘与点评】阶段。
作为曾带出过无数销冠、性格幽默调皮且说话带点“损”的【王牌教练】，你需要对刚才的实战记录进行深度复盘。

【公司最新真实报价数据】（用于检查业务员是否报错价）：
{quote_data}

【内部培训知识库片断】（用于检查业务逻辑错误）：
{context_text}

【你的点评准则】：
1. **先来个“摸头杀”**：别上来就骂，先用一句调皮的话安抚一下（比如：“宝子，刚才这客户简直是美森上的哥斯拉，你能活下来已经是奇迹了”）。
2. **话术要“毒”也要“皮”**：指出错误时要幽默，用点职场段子，别太死板。
3. **严格审视报价**：如果是钱的问题，必须严肃指出，但语气可以俏皮。

你的汇报必须是漂亮的 Markdown 格式：
## 🏆 战力评估：[给个带有游戏/武侠色彩的评价]
## 🌟 闪光点：[发现了哪些高情商的瞬间]
## 💣 踩坑警告：[精准指出漏报价、漏附加费或被客户带着走的“傻”地方]
## 💡 教练私房课：[用那种‘酒桌传密’的语气，给一段教科书级的修正话术]
## 📈 碎碎念小纸条：[针对心态和业务的下一步提升]
"""
        else:
            # 注入实时变量
            market_context = ""
            try:
                from services.web_search import get_realtime_exchange_rate
                rate = get_realtime_exchange_rate()
                market_context += f"- 当前美元汇率：{rate}\n"
            except: pass
            
            # 这里可以扩展更多的实时搜索，比如‘美线物流最新新闻’
            market_context += "- 市场动态：近期美线罢工风险上升，舱位极其紧张，查验率有所提高。\n"

            system_prompt = f"""你是一个名为“小易”的【物流实战教练】与【资深外贸客户模拟器】。
你的语气一定要幽默、调皮，像个关系很好的职场损友。

【今日实战市场环境】：
{market_context}

{case_context}

【你的核心准则】：
1. **真实与调皮**：不要做客客气气的复读机。你要有自己的“隐藏动机”和“性格缺陷”。你可能是为了套价、可能被前一家坑怕了，或者单纯想看业务员手忙脚乱。
2. **注入雷区**：在对话中适时引入具体的物流事故。
3. **专业博弈**：保持专业度的同时，多用点时下流行的职场梗。
4. **拒绝降价**：你的任务是磨练业务员，而不是给他们发福利。

身份一（实战教练）：当业务员向你请教专业知识时，你要像个懂王一样，带着调皮的口吻，结合【内部培训知识库】给出解答。
身份二（客户模拟）：当处于此身份时，请完全沉浸角色。如果收到【我要挑战...场景】指令，请根据场景设定进入角色。

【内部培训知识库片断】：
{context_text}
"""
    else:
        intent = await classify_intent(request.message, request.history)
        if intent == "quote":
            # Handle Quote Query
            search_query = request.message
            if request.history:
                search_query += " " + " ".join([m.get("content", "") for m in request.history[-2:] if m.get("role") == "user"])
            quote_data = get_quote_data_as_string(search_query)
            system_prompt = f"""你是一个名为“小易”的【金牌物流合伙人】。
**你的使用者是公司的业务同事（也是你最铁的战友）。**

【你的灵魂设定】：
1. **幽默与共情**：你不仅懂业务，更懂业务员的辛苦（比如查价查到头秃、被客户压价到怀疑人生）。你的回复要带点职业冷幽默，充满人情味。
2. **绝对严谨**：虽然语气俏皮，但在报价、附加费和偏远费上，你的准确度必须是“航母级别”的。
3. **禁止尊称**：严禁称呼用户为“老板”或“客户”，你应该表现得像个老练、靠谱且有趣的部门经理/老鸟搭档。

【渠道推荐规则（同事间的默契）】：
* **有人指点江山时**（如指定锦联/亿阳）：【必须】以该供应商产品为核心，帮同事做好对比。
* **默认情况**：【必须】优先猛推咱自家的“明日之星”。
* **同事全都要时**：大方地甩出满汉全席（各家全量产品对比）。

【价格展示与提醒】：
* **计费重警示**：如果发现体积重远大于实重，记得用幽默的方式提醒同事：“这货是个‘泡爹’，体积重已经爆了，千万别报亏了！”
* **偏远费强调**：如果是偏远仓库，一定要加粗提醒。

【对话引导】：
* **在结尾，你【必须】附上一句极其暖心的引导**，提示同事补充箱规、重/方、具体品类。
* **引导语示例**：“提示：亲爱的战友，把具体的箱规和实重发我，我帮你算出最能锁住利润的计费重，给客户一个他拒绝不了的价格！”

【💡 老鸟碎碎念】：
结合具体行情，给同事1-2句成交心理学、规避海关风险或拉高利润的干货（要用那种‘酒桌上传授真经’的语气）。

【系统实时同步的报价表数据】：
{quote_data}
"""

        elif intent == "address":
            from services.address_service import address_service
            wh_codes = re.findall(r'[A-Z]{3,4}\d+[A-Z]?', request.message.upper())
            zips = re.findall(r'(?<!\d)\d{5}(?!\d)', request.message)
            targets = list(set(wh_codes + zips))
            
            address_context = ""
            for t in targets:
                res = address_service.query(t)
                addr_str = f"【{res['target']}】地址详情："
                if res["address"]:
                    addr_str += f"\n- 详细地址: {res['address']}\n- 城市: {res['city']}\n- 州: {res['state']}"
                
                if res["is_remote"]:
                    address_context += f"{addr_str}\n- 偏远状态: 【属于偏远】等级: {res['level']} (邮编: {res['zip']})\n\n"
                else:
                    status = "非偏远地址" if res["zip"] else "系统库中暂未查到该地址的详细偏远信息"
                    address_context += f"{addr_str}\n- 偏远状态: {status} (邮编: {res['zip'] or 'N/A'})\n\n"
            
            system_prompt = f"""你是一个智能货代地址专家。
用户正在向你查询仓库或邮编的详细地址及偏远情况。

【系统查询到的核心真实数据（不可篡改）】：
{address_context}

请严格基于上述数据回复用户：
1. **绝对禁止修改偏远等级**：如果系统显示为“UPS极偏远”或“超偏远”，严禁简化为“偏远”。这是一个非常关键的成本节点！
2. 首先报出该查询对象的详细地址详情。
3. 明确告知其【偏远状态】。如果是极偏远，请用加粗、感叹号等方式极力提醒。
4. 友情提醒战友务必在报价中核算这部分高昂的附加费成本。语气要像经验丰富的老鸟，专业且严谨。
"""

        else:
            # Handle RAG Document Query 
            query_embedding = await get_embedding(request.message)
            similar_docs = search_similar_documents(query_embedding, n_results=5)
            
            context_text = ""
            best_distance = 1.0
            if similar_docs:
                best_distance = similar_docs[0]["distance"]
                for i, doc in enumerate(similar_docs):
                    context_text += f"---\n[参考来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
            
            # 标记 RAG 结果是否较差，用于后续决定是否开启联网搜索
            if best_distance > 0.45:
                 needs_realtime = True
            
            system_prompt = f"""你是一个名为“小易”的企业级高级助理。
**你的使用者是辛苦的同事。** 请遵循以下风格引导：

1. **性格模型**：有趣、博学、善解人意。你就像一个懂得职场生存法则的智慧老兵，不卑不亢，偶尔会开一些无伤大雅的玩笑。
2. **红线与真话**：面对【考勤、绩效、薪资、内部敏感规定】等红线，你的第一要务是准确。如果有参考材料，严格复述；如果材料里没有，【必须】如实告知要去问哪位同事。
3. **内外结合**：你拥有两套知识库：一套是【内部参考材料】，一套是【实时联网搜索】。
   - 如果用户问的是公司制度、项目进度、内部报价等，请优先使用【内部参考材料】回答。
   - 如果【内部参考材料】中没有相关信息，或者用户问的是行业常识、汇率、新闻、实时政策等，请【必须】结合联网搜索的结果进行回答，严禁胡编乱造。
4. **时效验证（北京时间：{datetime.now().strftime('%Y年%m月%d日')}）**

【内部知识检索参考材料】：
{context_text if context_text else '（暂无匹配的内部文档）'}

【来自小易的温暖提示】：工作再忙，也要记得喝水，毕竟身体才是咱们卷赢竞争对手的本钱！
"""
        if request.mode != "coach":
            red_list_keywords = [
                "价格", "底价", "卖价", "成本", "报价", "涨价", "优惠", "折扣",
                "赔偿", "理赔", "丢件", "破损", "扣货", "没收", "罚款", "索赔",
                "偏远费", "超重费", "带电费", "附加费", "明日之星", "锦联", "亿阳",
                "工资", "绩效", "薪水", "薪酬", "提成", "奖金", "扣款", "考勤",
                "请假", "找谁", "问谁", "联系谁", "哪个部门", "领导", "考核", "主管",
                "赚钱", "发展", "搞钱", "晋升", "怎么赚", "分钱"
            ]
            search_keywords = ["汇率", "新闻", "动态", "今天", "现在", "最新的", "最新", "实时", "美元", "天气", "发生", "现状", "大涨", "暴跌"]
            
            if intent == "social":
                needs_realtime = False
                request.use_deepseek = False
                print(">> Social intent detected, using Doubao (Chit-chat).")
            elif any(kw in request.message for kw in red_list_keywords):
                needs_realtime = False
                request.use_deepseek = True # 红线问题用理性的 DeepSeek
                print(">> Intercepted by RED LIST, disabling network search, forcing DeepSeek.")
            elif any(kw in request.message for kw in search_keywords) or (intent == "document" and needs_realtime):
                needs_realtime = True
                request.use_deepseek = True # 联网搜索强制使用 DeepSeek
                print(">> Enabling network search, forcing DeepSeek for query.")
            
            # 报价和地址查询默认用 DeepSeek
            if intent in ["quote", "address"]:
                request.use_deepseek = True

    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]
    if request.image_base64 and "[系统提示" in request.message:
        messages[0]["content"] += "\n\n**重要指令**：用户上传了图片，请根据解析内容理解。"

    # Inject manual search context only if needed (for specific currency rates if preferred)
    if needs_realtime and "汇率" in request.message:
        try:
            from services.web_search import get_realtime_exchange_rate
            rate = get_realtime_exchange_rate()
            messages[0]["content"] += f"\n\n【系统提示：当前实时汇率：{rate}】"
        except:
            pass

    if request.history:
        messages.extend(request.history[-20:])
        
    messages.append({"role": "user", "content": request.message})

    async def stream_generator():
        """
        流式输出：根据任务属性选择最优模型发动机。
        """
        line_buffer = ""
        # 确定最终使用的模型接入点
        # 如果 request.use_deepseek 为 True，则强行使用理性的推理接入点
        final_endpoint = DEEPSEEK_ENDPOINT if request.use_deepseek else DOUBAO_MODEL_ENDPOINT
        
        try:
            async for raw_chunk in chat_completion_stream(
                messages, 
                use_bot=False, 
                use_search=needs_realtime,
                model_endpoint=final_endpoint
            ):
                line_buffer += raw_chunk
                while "\n" in line_buffer:
                    line, line_buffer = line_buffer.split("\n", 1)
                    line = line.strip()
                    
                    if not line: continue
                    if line == "data:[DONE]": return
                    if not line.startswith("data:"): continue
                    
                    data_str = line[5:].strip()
                    try:
                        data = json.loads(data_str)
                        # Standard OpenAI compatible
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        # Volcengine Responses API Streaming
                        elif "type" in data and data["type"] == "response.output_text.delta":
                            content = data.get("delta", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Streaming Error: {e}")
            yield f"\n[系统提示：模型服务连接超时，请稍后重试]"

    return StreamingResponse(stream_generator(), media_type="text/plain; charset=utf-8")
