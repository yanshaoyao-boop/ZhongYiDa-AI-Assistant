import re

# 1. 搬运美化代码，直接塞进 App.vue 的顶端
app_path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend-uniapp\src\App.vue"
scss_path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend-uniapp\src\antigravity_modern.scss"

with open(scss_path, "r", encoding="utf-8") as f:
    modern_css = f.read()

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# 替换掉那个报错的 @import 语句，换成实际的代码内容
content = content.replace("@import './antigravity_modern.scss';", modern_css)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ App.vue 代码内联成功，已彻底消除路径识别问题！")
