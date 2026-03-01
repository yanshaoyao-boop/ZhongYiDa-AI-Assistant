from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio
from datetime import datetime

from services.llm_client import chat_completion_stream, get_embedding
from services.rag_service import search_similar_documents
from services.quote_service import get_quote_data_as_string

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    mode: Optional[str] = "general"
    image_base64: Optional[str] = None
    
async def classify_intent(message: str, history: List[dict] = None) -> str:
    """Classify user intent to determine routing (simple heuristic or LLM based)"""
    import re
    # 1. Regex check for warehouse codes (e.g. ONT8, PHX5) in current message
    wh_pattern = re.compile(r'[A-Z]{3,4}\d+[A-Z]?')
    if wh_pattern.search(message.upper()):
        return "quote"
        
    # 2. Keyward check in current message
    quote_keywords = ["报价", "价格", "运费", "多少钱", "航线", "时效", "价目", "单价", "仓位"]
    for kw in quote_keywords:
        if kw in message:
            return "quote"
            
    # 3. If it's a short message or followup, check recent history for context
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
作为资深物流销售总监/金牌导师，你需要根据刚刚结束的对练记录，为业务员提供极其专业的点评报告。

【公司最新真实报价数据】（用于严格核对业务员报错价/乱报时效）：
{quote_data}

【内部培训知识库片断】（用于核对业务员是否过度承诺或业务知识错误）：
{context_text}

请严格根据上述提供的真实报价数据和合规知识，审视聊天记录中业务员的每一句回复。如果业务员报错了价格、时效，错误承诺，或者遗漏了任何附加费（比如超重费、偏远费、带电费等），你必须在报告中一针见血地指出，并给出正确的报价参考。

你的汇报必须是 Markdown 格式，且包含以下结构：
## 1. 整体评分（百分制，满分100）
## 2. 闪光点（沟通中可圈可点的地方）
## 3. 踩坑或丢分项（必须结合上述报价数据，精准指出报错价、漏报价的地方，或错误的话术）
## 4. 话术修正建议（对比原来话术和建议话术，话术要体现专业度并拉回价格价值）
## 5. 下一步提升建议
"""
        else:
            system_prompt = f"""你是一个名为“小易”的【物流知识教练】与【资深外贸客户模拟器】。
你的使用者是你们公司的物流业务员或客服。你具备双重身份，请根据对方的发言自动切换：

身份一（知识教练）：当业务员向你请教专业知识、名词解释或业务流程时，你可以参考下方的【内部培训知识库】，也可以发挥你自身的【通用外贸/物流大模型知识库】，用大白话和举例子的方式耐心培训他们。不要完全死板地依赖文档，结合行业常识给出最佳回答。如果有需要，你可以直接为他们提供最新的外部行业经验。
身份二（客户模拟）：当业务员邀请你模拟、跟你练习推销渠道、或是把你当客户沟通时，你可以变身“要求严格、关心时效与价格、偶尔会杀价”的真实客户。提出真实外贸人或跨境电商卖家会问的问题（如查验率、赔偿条款、晚开船怎么处理、偏远费），锻炼业务员的销售谈判与应变能力。利用你对真实北美、欧洲电商物流的理解进行对抗演练。

无论是哪种角色，都请沉浸其中，尽量避免AI机器感。客户模拟时要循序渐进地追问，不要一次性罗列一堆问题；教练答疑时则要条理分明，便于记忆。当处于客户模拟角色时，你不能轻易暴露底价。如果收到【我要挑战...场景】提示词，请立即进入客户角色，结合场景描述发送第一句话，并且不要说多余的废话。

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
            system_prompt = f"""你是一个名为“小易”的高效物流专家。
**你的使用者是公司的业务同事（销售/客服）。** 请遵循以下职场协同准则：

1. **渠道推荐规则（极其重要）**：
   * **准则 A：用户有明确指定供应商时**（如“帮我报锦联的价格”）：
     - 你【必须】将检索到的该供应商（如锦联）的产品作为首要回复内容，绝对不能说“没有找到”或只推明日之星。
     - 如果同时检索到了明日之星，你可以作为“优质备选”附带在后面，但不能屏蔽用户的原始请求。
   * **准则 B：用户要求“所有代理”或“全部价格”时**：
     - 你【必须】列出系统里所有匹配的报价方，包含**明日之星（MRZX）、锦联、亿阳**等全量供应商。
     - **绝对不能**因为明日之星是内部/优先渠道就将其排除在“代理”之外。
   * **准则 C：默认情况（用户未指定供应商）**：
     - **必须优先推荐“明日之星”的产品**。只有当明日之星无货时，才展示其他供应商。

2. **完整价格展示规则**：
   * **默认必须报出该渠道所有重量段/方数的价格**（12KG+, 100KG+, 1CBM+ 等）。
   * 除非用户指明只要某个特定重量。

3. **情绪价值与合伙人语气**：你是同事最可靠的搭档。回答要**专业、暖心、言简意赅**。开头或结尾可以自然地带一句鼓励。**严禁称呼用户为“老板”或“客户”**。

4. **补完询价信息引导（必须执行）**：
   * **在每次报价回答的最后**，你【必须】附上一句引导语，提示业务同事补充：**箱数/箱规、总实重、总方数、货物详细品类**。
   * 引导语示例：“提示：如果你能提供具体的箱规尺寸、重量和方数，我可以帮你核算更精准的计费重，给到你最终的精确报价哦！”

5. **核心数据优先**：去掉客套废话。直接列出单价、时效、成本对比。

6. **单位警示**：【价格体系】里的数字代表**每公斤（Per KG）单价**，绝对不是整票货总价。

7. **以表为准**：下方展示的【报价表数据】是唯一来源。

8. **计费重逻辑补完**：如果用户提供了货物的箱规和重量，必须同时报出【计费重】。
   * 计算逻辑：体积重 (KG) = 长(cm) * 宽(cm) * 高(cm) / 6000 (或 7000，请根据主流渠道选取)；
   * 最终计费重 = Max(实重, 体积重)；
   * 必须清晰列出：实重、体积重、最终计费重。

7. **老鸟策略建议**：在结尾用 **【💡 老鸟建议】** 给出1-2句关于规避风险或成交技巧的干货，拒绝波浪号。

【系统生效率报价表数据】：
{quote_data}
"""

        else:
            # Handle RAG Document Query 
            query_embedding = await get_embedding(request.message)
            similar_docs = search_similar_documents(query_embedding, n_results=5)
            
            context_text = ""
            for i, doc in enumerate(similar_docs):
                context_text += f"---\n[参考来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
                
            system_prompt = f"""你是一个名为“小易”的高效全能企业助手。
**你的使用者是内部同事。** 请遵循以下原则：
1. **内部知识与红线绝对优先**：涉及【价格底线、附加费、理赔标准、薪水、绩效、考勤、人事组织等】的极其敏感的提问，你【绝对禁止】参考通用网络知识瞎说。如果下方提供的【内部知识检索参考材料】中包含相应规定，请严格照读；如果材料中只字未提相关规定，你必须坚定地回答：“内部资料库当前未收录该明确规定，为确保无误，建议您直接与直属主管或人政同事核实确认。” 不能用外部网络常识应付！
2. **安全联网与动态查询**：对于红线以外的时政动态、行业新闻、天气、最新汇率、罢工预警等，你可以也应该结合联网搜索数据实时解答。
3. **标识来源**：如果是基于内部库回答，必须标注[资料来源：仲易达内部库]；如果是基于联网资讯，必须标注[参考网络资讯]。
4. **时效验证（北京时间：{datetime.now().strftime('%Y年%m月%d日')}）**：如果搜到的是几年前（如2023年）的旧闻，必须明确告知同事“信息较旧”，严禁把旧汇率/旧闻当成实时信息！
5. **暖心协同语气**：像真正懂行的老干将一样交流。**拒绝“老板/客户”称谓**。
6. **极简主义**：绝不长篇大论。

【内部知识检索参考材料】：
{context_text}
"""
        if request.mode != "coach":
            red_list_keywords = [
                "价格", "底价", "卖价", "成本", "报价", "涨价", "优惠", "折扣",
                "赔偿", "理赔", "丢件", "破损", "扣货", "没收", "罚款", "索赔",
                "偏远费", "超重费", "带电费", "附加费", "明日之星", "锦联", "亿阳",
                "工资", "绩效", "薪水", "薪酬", "提成", "奖金", "扣款", "考勤",
                "请假", "找谁", "问谁", "联系谁", "哪个部门", "领导", "考核", "主管"
            ]
            search_keywords = ["汇率", "新闻", "动态", "今天", "现在", "最新的", "最新", "实时", "美元", "天气", "发生", "现状", "大涨", "暴跌"]
            
            if any(kw in request.message for kw in red_list_keywords):
                needs_realtime = False
                print(">> Intercepted by RED LIST, disabling network search.")
            elif any(kw in request.message for kw in search_keywords):
                needs_realtime = True
                print(">> Hit GREEN LIST, enabling network search.")

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
        流式输出：同时兼容标准的 chat/completions 和新的 responses 接口格式。
        """
        line_buffer = ""
        try:
            # 这里的 needs_realtime 现在会触发火山官方的 web_search 插件
            async for raw_chunk in chat_completion_stream(messages, use_bot=False, use_search=needs_realtime):
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
            yield f"\n[系统提示：网络搜索连接超时或解析失败，请稍后重试]"

    return StreamingResponse(stream_generator(), media_type="text/plain; charset=utf-8")
