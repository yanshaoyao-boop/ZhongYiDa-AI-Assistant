import re

path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend-uniapp\src\pages\chat\chat.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 寻找所有包含“DEBUG”或“小易全能”的 tab-text 标签并强制还原
# 正则：匹配 <text class="xxx">...任意文字...</text>，只要中间出现了 DEBUG/小易全能
content = re.sub(
    r'<text class="tab-text">.*?(?:DEBUG|小易全能).*?</text>',
    '<text class="tab-text">全能助手</text>',
    content
)

# 兜底防御：直接把那一整段 Tab 导航的核心文字复原
content = content.replace("【DEBUG】Web风格重构中...", "全能助手")
content = content.replace("【DEBUG】蓝色版", "全能助手")
content = content.replace("小易全能助手", "全能助手")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 文字精准复原完成，现在代码处于最纯净状态！")
