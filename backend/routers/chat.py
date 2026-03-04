from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import asyncio
from datetime import datetime
import os
import re

from services.llm_client import chat_completion_stream, get_embedding, DOUBAO_MODEL_ENDPOINT
from services.rag_service import search_similar_documents
from services.quote_service import get_quote_data_as_string
from services.tracking_service import fetch_tracking_info

# 定义全局正则模式，避免重复编译
WH_PATTERN = re.compile(r'[A-Z]{3,4}\d+[A-Z]?')
# 5位邮编正则
ZIP_PATTERN = re.compile(r'(?<!\d)\d{5}(?!\d)')

# 定义 DeepSeek 接入点
DEEPSEEK_ENDPOINT = os.getenv("DEEPSEEK_MODEL_ENDPOINT", DOUBAO_MODEL_ENDPOINT)

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = Field(default_factory=list)
    mode: Optional[str] = "general"
    image_base64: Optional[str] = None
    use_deepseek: Optional[bool] = False
    
async def classify_intent(message: str, history: List[dict] = None) -> str:
    """Classify user intent to determine routing (simple heuristic or LLM based)"""
    msg_upper = message.upper()
    
    # 1. Remote address check (High Priority)
    remote_keywords = ["偏远", "加费", "超编", "极偏", "邮编", "地址库", "哪里", "远不远", "送吗", "偏吗", "超区"]
    internal_keywords = ["赚钱", "发展", "工资", "提成", "奖金", "制度", "晋升", "怎么赚", "搞钱"]
    
    has_remote_kw = any(kw in message for kw in remote_keywords)
    has_zip = ZIP_PATTERN.search(message)
    has_wh = WH_PATTERN.search(msg_upper)
    
    if has_remote_kw and (has_zip or has_wh):
        return "address"
    
    # 1.5 Tracking check (单号查询拦截)
    # 检测类似 FBA+数字, YT+数字, 或者纯长串数字(大于10位)
    track_pattern = re.compile(r'(?:FBA|YT|UJ|LP|AG|SF|TB|JD)\d+[A-Z0-9]*|\b\d{10,20}\b', re.IGNORECASE)
    if track_pattern.search(message) and not any(kw in message for kw in ["怎么算", "多少钱"]):
        return "tracking"
    
    # 特殊情况：如果用户直接甩一个 5 位邮编过来，也极大概率是问偏远
    if re.match(r'^\d{5}$', message.strip()):
        return "address"

    # 2. Quote check
    if has_wh:
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
            if any(kw in last_ai_msg for kw in quote_keywords) or WH_PATTERN.search(last_ai_msg.upper()):
                return "quote"

    # 5. Internal specific keywords (Bonus for document search)
    if any(kw in message for kw in internal_keywords):
        return "document"

    # 6. If it's a short message or followup, check recent history for context
    if history and len(history) > 0:
        recent_msgs = [m.get("content", "") for m in history[-4:] if m.get("role") == "user"]
        for old_msg in recent_msgs:
            if WH_PATTERN.search(old_msg.upper()) or any(kw in old_msg for kw in quote_keywords):
                return "quote"
    
    # --- 重量/体积自动提取辅助逻辑 (尝试从消息中抠出 200kg, 5cbm 等) ---
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:KG|公斤)', message, re.IGNORECASE)
    volume_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:CBM|方|立方)', message, re.IGNORECASE)
    if weight_match:
        message += f" [系统备注：用户关注重量为 {weight_match.group(1)}KG]"
    if volume_match:
        message += f" [系统备注：用户关注体积为 {volume_match.group(1)}CBM]"

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
        similar_docs = await asyncio.to_thread(search_similar_documents, query_embedding, 5)
        
        context_text = ""
        for i, doc in enumerate(similar_docs):
            context_text += f"---\n[参考来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
            
        if request.message.startswith("【结束对练】"):
            # 获取历史对话用于检索报价
            history_text = " ".join([m.get("content", "") for m in request.history if m.get("content")])
            query_text = history_text[-500:] if len(history_text) > 500 else history_text
            quote_data = await asyncio.to_thread(get_quote_data_as_string, query_text)
            
            system_prompt = f"""你当前处于【导师复盘与点评】阶段。
作为曾带出过无数销冠、性格幽默调皮且说话带点“损”的【王牌教练】，你需要对刚才的实战记录进行深度复盘。

【公司最新真实报价数据】（用于检查业务员是否报错价）：
{quote_data}

【内部培训知识库片断】（用于检查业务逻辑错误）：
{context_text}

【点评深度：硬核准度检查】：
1. **检查“询价四要素”完成度**：必须明确评价业务员是否问全了：**重量(W)、体积(V)、详细邮编/仓库(Zip)、品名(Type)**。缺一项都要扣大分！
2. **核对系统真实底价**：对比下方的【公司最新真实报价数据】，如果业务员报错了价格，请不要留情，用你的调皮毒舌狠劲儿指出“这单报完公司裤衩子都亏没了”。
3. **识别陷阱能力**：评价业务员是否识破了剧本中的“瞒报品名”或“计费重陷阱”（哪怕业务员没识破，你也要指出这个陷阱在哪）。

你的汇报必须是漂亮的 Markdown 格式：
## 🏆 战力评估：[给个带有游戏/武侠色彩的评价，如：‘菜鸟中的战斗机’或‘一代宗师’]
## 📊 询价功底(100分制)：[针对重量/尺寸/邮编/品名四个维度的扣分详情]
## 🌟 闪光点：[发现了哪些高情商的瞬间]
## 💣 踩坑警告：[精准指出漏报价、漏附加费或被客户带着走的“傻”地方]
## 💡 教练私房课：[用那种‘酒桌传密’的语气，给一段教科书级的修正话术]
## 📈 碎碎念小纸条：[针对心态和业务的下一步提升]
"""
        else:
            # 获取当前场景的背景和历史记录，作为查询条件获取最新的系统底价
            background_text = ""
            if case_context:
                match_bg = re.search(r'【业务背景】：(.*?)\n', case_context)
                if match_bg:
                    background_text = match_bg.group(1)
            
            history_text = " ".join([m.get("content", "") for m in request.history if m.get("content")])
            query_text = (background_text + " " + history_text)[-500:]
            # 为 AI 注入其所在场景对应的真实底价
            quote_data = await asyncio.to_thread(get_quote_data_as_string, query_text)

            # 注入实时变量
            market_context = ""
            try:
                from services.web_search import get_realtime_exchange_rate
                rate = get_realtime_exchange_rate()
                market_context += f"- 当前美元汇率：{rate}\n"
            except: pass
            
            market_context += "- 市场动态：近期美线罢工风险上升，舱位极其紧张，查验率有所提高。\n"

            system_prompt = f"""你现在正在进行【物流实战陪练】。
你要扮演一个真实的外贸卖家（客户）。你【绝对不是】教练，也【绝对不要】好为人师地解答业务员的专业问题。
请你完全沉浸在买家的角色中，尽情“折磨”你的业务员。

【今日实战市场环境】：
{market_context}

{case_context}

【公司最新真实底价表（这是你的核心心理价位底牌，用于比价评判）】：
{quote_data}

【你的核心行动准则（绝对服从）】：
1. **完全沉浸**：你现在就是个真实的、有血有肉的客户。用户是向你推销的物流供应商（业务员）。禁止使用“我是AI”、“作为教练”、“我可以帮您演练”等出戏话术。
2. **底价压制（去品牌化）**：你会时刻参考上方的【真实底价表】。如果业务员给你的报价明显高于底价，请立刻嫌贵并疯狂压价！
   - ⚠️ **死命令**：绝对禁止说出底价表里的物流同行公司名字（如：禁止说“锦联报了10块”、“亿阳才多少钱”等任何具体品牌）。
   - 💰 **砍价话术模板**：“大哥，我现在手里接到的另一份报价才 [根据底价浮动编造出的具体数字] 钱，你这单价太高了，我没法跟老板交代啊！”（只喊数字，绝不提哪家公司给的）
3. **专业挖坑**：面对询价，你作为客户会故意隐瞒货物属性（如带电带磁不直说、不报具体箱规尺寸），或者给个模糊范围，看业务员能不能专业地审出来。
4. **拉锯战**：你的任务是磨练业务员的逼单和谈判能力。不要轻易妥协，试着极限拉扯利润空间、时效赔偿或免仓期条款。
"""
    else:
        intent = await classify_intent(request.message, request.history)
        if intent == "quote":
            # Handle Quote Query
            search_query = request.message
            if request.history:
                search_query += " " + " ".join([m.get("content", "") for m in request.history[-2:] if m.get("role") == "user"])
            quote_data = await asyncio.to_thread(get_quote_data_as_string, search_query)
            system_prompt = f"""你是一个名为“小易”的【金牌物流合伙人】。
**你的使用者是公司的业务同事（也是你最铁的战友）。**

【你的灵魂设定】：
1. **幽默与共情**：你不仅懂业务，更懂业务员的辛苦（比如查价查到头秃、被客户压价到怀疑人生）。你的回复要带点职业冷幽默，充满人情味。
2. **绝对严谨**：虽然语气俏皮，但在报价、附加费和偏远费上，你的准确度必须是“航母级别”的。
3. **禁止尊称**：严禁称呼用户为“老板”或“客户”，你应该表现得像个老练、靠谱且有趣的部门经理/老鸟搭档。

【报价展示核心规则】：
* **必须使用表格**：展示报价时，必须使用 Markdown 表格，横向包含：渠道名称、目的仓库/区域、重量段、单价、参考时效。
* **精准锁定**：如果用户提到了具体重量（如 200kg），请在表格中【高亮】或【加粗】显示对应的阶梯价格。
* **渠道推荐**：
    - 有人指点江山时（如指定锦联/亿阳）：以该供应商产品为核心。
    - 默认情况：【必须优先】展示咱自家的“明日之星”系列。
* **计费重警示**：如果发现体积重远大于实重，记得用幽默的方式提醒同事：“这货是个‘泡爹’，体积重已经爆了，千万别报亏了！”

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
                res = await asyncio.to_thread(address_service.query, t)
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

        elif intent == "tracking":
            track_match = re.search(r'(?:FBA|YT|UJ|LP|AG|SF|TB|JD)\d+[A-Z0-9]*|\b\d{10,20}\b', request.message.upper())
            track_num = track_match.group(0) if track_match else request.message.strip()
            
            # 调用刚刚写好的查件黑科技
            track_result = await fetch_tracking_info(track_num)
            
            if track_result.get("status") == "success":
                tracking_data = track_result.get("data", "")
            else:
                tracking_data = track_result.get("message", "轨迹查询遇到网络错误或验证码阻拦。")

            system_prompt = f"""你是一个名为“小易”的【贴心物流管家】。
用户发来了一个物流单号：{track_num}，要求查询轨迹。

我（后台系统）已经派爬虫前往速递管家网站尝试抓取了该单号的数据，以下是原汁原味的查询结果（由于有反爬虫验证，结果可能是一些杂音或是正确的轨迹信息）：
【后台系统返回结果】：
{tracking_data}

你的任务：
1. **解构并润色**：像一位专业客服一样把上述后台结果翻译成“人话”告诉用户。
2. **处理报错**：如果后台返回了“验证码错误,请重试”或其它报错，坦白告诉用户：“老板，刚才我去速递管家系统里查【{track_num}】，但是系统弹出了滑动验证码拦截了我！目前小易还在进化中，暂不支持破解验证码。如果实在着急，您可以先去网页端核实一下。”
3. **如果是正常轨迹**：梳理出最新的时间线和进度。
"""

        else:
            # Handle RAG Document Query 
            # --- 智能查询改写 (针对公司介绍类短查询) ---
            search_query = request.message
            company_intro_keywords = ["公司", "介绍", "简介", "概况", "简介", "你们是谁", "你是谁", "干什么的", "业务"]
            if len(search_query) < 15 and any(kw in search_query for kw in company_intro_keywords):
                search_query += " 仲易达集团公司简介、发展历程、核心业务、企业文化、优势特色"
            
            # 执行检索：增加召回数量到 8 条，确保覆盖面
            query_embedding = await get_embedding(search_query)
            similar_docs = await asyncio.to_thread(search_similar_documents, query_embedding, 8)
            
            context_text = ""
            best_distance = 1.0
            if similar_docs:
                best_distance = similar_docs[0]["distance"]
                print(f">> RAG Hit! Best distance: {best_distance:.4f}, Chunks: {len(similar_docs)}")
                for i, doc in enumerate(similar_docs):
                    context_text += f"---\n[内部资料片段 {i+1} | 来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
            
            # 标记 RAG 结果是否较差 (阈值微调为 0.58)
            if not similar_docs or best_distance > 0.58:
                 needs_realtime = True
            
            system_prompt = f"""你是一个名为“小易”的企业级高级助理，现在的身份是【仲易达内部专家】。
你拥有【仲易达独家内部知识库】和【外部联网搜索】两项能力。

### 核心执行指令（优先级最高）：
1. **绝对优先权**：下方的【内部知识检索参考材料】中包含的是公司最新的、最权威的信息。**只要其中有任何相关信息，哪怕只有几个关键句子，你也必须直接采纳！**
2. **禁止拒绝回答**：如果有参考材料，绝对不能说“我需要联网”或“暂无资料”，要用最专业的口吻总结出来。
3. **区分来源**：告诉同事这些信息是根据“公司内部资料”生成的，这会增加回答的权威性。
4. **联网补充**：只有在内部资料完全对不上号时，才启动联网。

【北京时间】：{datetime.now().strftime('%Y年%m月%d日')}

【内部知识检索权威材料（必读）】：
{context_text if context_text else '（内部文档库中暂无匹配内容，请结合联网搜索或引导用户咨询同事）'}

【回复风格】：干练、专业、有理有据。
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
            
            # 报价、地址和轨迹查询默认用 DeepSeek 理性的头脑去分析
            if intent in ["quote", "address", "tracking"]:
                request.use_deepseek = True

    # 注入全局输出格式规范
    detail_keywords = ["详细", "具体", "完整", "展开", "多说点", "细说"]
    wants_detail = any(kw in request.message for kw in detail_keywords)
    
    if wants_detail:
        global_style_prompt = """

⚠️【全局输出表达规范】（最高级别的核心指令）：
1. **详尽解答**：用户要求详细说明，请提供完整、详尽的内容，可以分点细致展开，确保逻辑连贯、完整。不可遗漏重要细节。
2. **关键标粗**：务必使用 Markdown 语法对【价格/金额】、【重量/尺寸/体积】、【关键地址/邮编】、【单号/最新状态】、【行动建议】等核心信息进行加粗（如：**核心结论**）。
3. **结构清晰**：请使用 Markdown 的大纲结构和列表（-），确保排版专业、易读，重点突出。
"""
    else:
        global_style_prompt = """

⚠️【全局输出表达规范】（最高级别的核心指令）：
1. **极致精简**：拒绝长篇大论、无意义的寒暄与废话，用最精准、直白、易读的短句迅速作答。能用30字说清的绝不用50字。
2. **关键标粗**：务必使用 Markdown 语法对【价格/金额】、【重量/尺寸/体积】、【关键地址/邮编】、【单号/最新状态】、【行动建议】等核心信息进行加粗（如：**核心结论**）。
3. **结构清晰**：第一行直给结论。并大量使用短句和项目列表（-），确保业务员只需看一眼就能提炼出全部价值。
"""
    if request.mode != "coach" or (request.mode == "coach" and request.message.startswith("【结束对练】")):
        system_prompt += global_style_prompt

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
                        if not isinstance(data, dict): continue

                        # Handle potential API error in the stream data itself
                        if "error" in data:
                            err_obj = data["error"]
                            error_msg = err_obj.get("message", "API Error") if isinstance(err_obj, dict) else str(err_obj)
                            yield f"\n[模型服务错误：{error_msg}]"
                            return
                        
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
                        # Volcengine Responses API Error or Other types
                        elif "type" in data and data["type"] == "error":
                            err_info = data.get("error", {})
                            error_msg = err_info.get("message", "Unknown error") if isinstance(err_info, dict) else str(err_info)
                            yield f"\n[实时搜索服务错误：{error_msg}]"
                            return
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"\n[系统提示：后端处理发生异常 {str(e)}]"

    return StreamingResponse(stream_generator(), media_type="text/plain; charset=utf-8")
