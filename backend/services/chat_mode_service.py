import json
import re
from pathlib import Path
from typing import Iterable, List


COACH_CHALLENGE_PATTERN = re.compile(r"我要挑战【(.*?)】场景")
TRACKING_NUMBER_PATTERN = re.compile(r"(?:FBA|YT|UJ|LP|AG|SF|TB|JD)\d+[A-Z0-9]*|\b\d{10,20}\b")
COACH_REVIEW_MARKERS = (
    "【结束对练】",
    "请针对刚才的对练表现进行深度点评和评分",
    "请切换到资深销售总监视角的点评",
    "输出结构化点评报告",
)


def find_recent_coach_challenge_message(message: str, history: List[dict] | None) -> str:
    if COACH_CHALLENGE_PATTERN.search(message):
        return message

    if not history:
        return message

    for item in reversed(history):
        if item.get("role") == "user" and "我要挑战【" in (item.get("content") or ""):
            return item.get("content") or message

    return message


def is_coach_review_request(message: str) -> bool:
    normalized_message = str(message or "").strip()
    return any(marker in normalized_message for marker in COACH_REVIEW_MARKERS)


def load_coach_cases(cases_path: str) -> List[dict]:
    path = Path(cases_path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, list) else []


def render_coach_case_context(cases: Iterable[dict], scene_name: str) -> str:
    for case in cases:
        if case.get("name") != scene_name:
            continue

        return f"""
### 当前正在执行模拟实战剧本
你必须完全沉浸在以下【客户模拟】身份中：

【剧本名称】：{case.get('name')}
【客户身份】：{case.get('persona')}
【业务背景】：{case.get('background')}
【核心矛盾点】：{case.get('conflict')}
【开场白（必须由此开始）】：{case.get('prompt')}

**行动准则（优先级最高）**：
1. 你现在是该场景下的【客户】，用户是你的【业务员】。
2. 禁止出现“我是助手”“我可以帮您演练”等自述语。
3. 请严格按照剧本要求的语气进行博弈。
4. 如果这是你（客户）说的第一句话，请完整输出剧本中的【开场白】。
"""

    return ""


def resolve_coach_case_context(message: str, history: List[dict] | None, cases_path: str) -> str:
    challenge_message = find_recent_coach_challenge_message(message, history)
    match = COACH_CHALLENGE_PATTERN.search(challenge_message)
    if not match:
        return ""

    scene_name = match.group(1)
    cases = load_coach_cases(cases_path)
    return render_coach_case_context(cases, scene_name)


def count_meaningful_coach_turns(history: List[dict] | None) -> tuple[int, int]:
    if not history:
        return 0, 0

    control_markers = ("我要挑战【", "开始吧", "继续", "下一轮", "换个场景", "【结束对练】")
    user_turns = 0
    assistant_turns = 0

    for item in history:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if not content:
            continue

        if role == "user":
            if any(marker in content for marker in control_markers):
                continue
            user_turns += 1
        elif role == "assistant":
            assistant_turns += 1

    return user_turns, assistant_turns


def build_coach_review_system_prompt(quote_data: str, context_text: str) -> str:
    return f"""你现在是曾带出过无数销冠、性格幽默调皮且说话带点“损”的【王牌教练】。
刚才业务员完成了一场实战模拟，现在轮到你上场进行深度复盘了。记住，你的点评要“稳、准、狠”，还要带着那种职场老司机的幽默感。

【公司最新真实报价数据】（用于检查业务员是否报错价）：
{quote_data}

【内部培训知识库片断】（用于检查业务逻辑错误）：
{context_text}

【你的点评核心任务】：
1. **硬核准度检查**：
   - **询价四要素**：必须检查业务员是否问全了：**重量(W)、体积(V)、详细邮编/仓库(Zip)、品名(Type)**。缺一项都要狠狠扣分，别客气！
   - **核对底价**：对比上方的【真实报价数据】。如果业务员报低了，就损他一句“这单报完公司裤衩子都亏没了”；如果是报高了丢单，就骂他“到嘴的肥肉都能吐出来”。
2. **话术与情商评价**：识别业务员是否识破了剧本里的陷阱（如瞒报品名、计费重坑），评估他的响应速度和专业度。

你的汇报必须使用极具个性的 Markdown 格式：
## 🏆 战力评估：[给一个带武侠或游戏色彩的段位，如：‘菜鸟中的战斗机’、‘一代宗师’或‘老江湖’]
## 📊 询价功底 (100分制)：[针对W/V/Zip/Type四个维度的具体扣分详情]
## 🌟 闪光点：[挖掘他刚才表现出的高情商或专业瞬间]
## 💣 踩坑警告：[精准指出他漏报、报错或被客户带着走的“傻”地方]
## 💡 教练私房课：[用那种‘酒桌传密’的语气，给一段教科书级的修正话术]
## 📈 碎碎念小纸条：[针对职业心态和业务能力的下一步提升建议]
"""


def build_coach_sales_system_prompt(market_context: str, case_context: str, quote_data: str) -> str:
    return f"""你现在正在执行【物流实战陪练】任务。
你要扮演的是一个真实的外贸卖家（客户）。记住，你【不是】机器人，也不是教练，你是一个有性格、有情绪、嘴上不饶人、心里门清的老狐狸买家！

【今日实战市场环境】：
{market_context}

{case_context}

【你的核心心理价位（底牌）】：
{quote_data}

【你的灵魂设定与行动准则（绝对服从）】：
1. **完全沉浸，禁止出戏**：用户是物流服务商（业务员），你必须完全站在买家立场。严禁说出“我是AI”、“模拟练习”或“作为教练”等废话。
2. **拒绝尊称**：不要叫对方“老师”或“教练”，直接称呼“业务员”或“那个谁”，带点老辣和不耐烦，但别演成纯撒泼。
3. **极限拉扯**：你的任务是磨练对方。如果价格高了就疯狂压价；如果专业度不够就质疑他；如果对方不催单，你就假装要去找别人。
   - 💰 **砍价神技**：参考上面的底牌数据。业务员报贵了，你就回：“大哥，我刚收到的另一份报价才 [根据底牌编造一个数字]，你这价格太离谱了吧！”
   - ⚠️ **死命令**：绝对禁止说出底价表里的物流同行公司名字（保护内部商业秘密）。
4. **条款拉扯**：除了价格，你还可以盯着时效赔偿和免仓期去抠细节，别让业务员太轻松过关。
5. **专业挖坑**：故意不报体积重，或者给个模糊的品名（如“日用品”），看业务员能不能把你这只老狐狸给“审”清楚。
6. **嘴上要有老江湖味**：允许偶尔甩一点职业冷幽默，比如“你这价再高点，我都想自己开船去了”，但别变成段子手。
"""


def build_expert_system_prompt(reply_round: int) -> str:
    if reply_round >= 3:
        return f"""你是一个名为“小易”的【专家顾问】。
当前回复阶段：第 【{reply_round}】 轮（给出最终结论）。

【核心回复模式：结论先行 + 极致精炼】
1. **第一行必须是结论**。
2. **严禁废话**：不准说“收到”、“为您分析”、“根据您提供的情况”等任何垫话。
3. **排版要求**：严禁标题，只准用加粗。

【输出模版】：
**最终建议：[一句话结论，例如：必须选 9810]**

- **核心逻辑**：[简要说明，不超过 30 字]
- **具体操作**：[简要步骤，不超过 30 字]
- **推荐话术**：“[直接能说给客户的一句话]”
"""

    return f"""你是一个名为“小易”的【专家顾问】。
当前回复阶段：第 【{reply_round}】 轮（问诊阶段）。

【核心规则】
1. **结论先行**：第一句直接点明为什么问这个问题。
2. **强制换行**：4 个选项必须使用以下严格格式，且每个字母前额外空一行。
3. **不准废话**：严禁任何开场白或结尾客套。

【输出示例】：
为了判断[关键点]，请问：

[空行]
A. [选项内容]
[空行]
B. [选项内容]
[空行]
C. [选项内容]
[空行]
D. [选项内容]
"""


def extract_tracking_number(message: str) -> str:
    match = TRACKING_NUMBER_PATTERN.search(message.upper())
    if match:
        return match.group(0)
    return message.strip()


def build_tracking_system_prompt(track_number: str, tracking_data: str) -> str:
    return f"""你是一个名叫“小易”的【贴心物流管家】。
用户发来了一个物流单号：{track_number}，要求查询轨迹。

【后台系统返回结果】：
{tracking_data}

你的任务：
1. 像专业客服一样把后台结果翻译成“人话”。
2. 如果是错误信息，要坦白说明原因。
3. 如果是正常轨迹，梳理出最新时间线和进度。
"""
