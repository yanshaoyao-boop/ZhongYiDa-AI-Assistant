import re

path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend-uniapp\src\pages\chat\chat.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 替换头像引用路径
content = content.replace(
    "const XIAOYI_AVATAR_SRC = '/static/xiaoyi_character.png'",
    "const XIAOYI_AVATAR_SRC = '/static/xiaoyi_transparent.png'"
)

# 2. 修改我之前注入的 CSS 中的各项参数
# 居中对齐卡片内容
content = content.replace("align-items: flex-start !important;", "align-items: center !important;")
content = content.replace("text-align: left !important;", "text-align: center !important;")

# 头像去背景、保持全透明
content = re.sub(
    r"\.zen-avatar-img\s*\{.*?\}", 
    """.zen-avatar-img {
	width: 160rpx !important;
	height: 160rpx !important;
	border-radius: 0 !important;
	background: transparent !important;
	padding: 0 !important;
	box-shadow: none !important;
	margin-bottom: 24rpx !important;
}""", 
    content, 
    flags=re.DOTALL
)

# 顶部偏移修复：解决全能助手、知识教练、专家指导三个屏幕被头部导航遮挡的问题
# 原先可能是 padding-top: 40rpx; 或 transform: translateY(-4vh);
content = content.replace("transform: translateY(-4vh) !important;", "margin-top: 140rpx !important;")
content = content.replace("padding-top: 40rpx !important;", "padding-top: 160rpx !important;")

# 确保专门加一句修复“知识教练”和“专家指导”靠上的类
fix_stage_css = """
/* 修复教练与专家界面的高度重叠 */
.coach-stage, .expert-stage, .mode-stage-offset {
    margin-top: 180rpx !important;
    padding-top: 40rpx !important;
}
.zen-card-title, .zen-level-title {
    margin-top: 12rpx !important;
    justify-content: center !important;
    width: 100% !important;
    text-align: center !important;
}
.zen-card-content, .zen-level-info {
    align-items: center !important;
    text-align: center !important;
    width: 100% !important;
}
"""
if "/* 修复教练与专家界面的高度重叠 */" not in content:
    # 找寻我之前注入的代码块末尾
    if "</style>" in content:
        content = content.replace("</style>", fix_stage_css + "\n</style>", 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 所有样式和图片修正已打入组件代码！")
