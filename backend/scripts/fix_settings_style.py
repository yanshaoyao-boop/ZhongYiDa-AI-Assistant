path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend\src\views\ChatView.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 管理员入口按钮的参考样式（通常是紫色渐变）
# 我将直接重写 .sidebar-settings-btn 的 CSS，使其与 .sidebar-admin-btn 保持高度一致

old_settings_css = """/* ====== 设置按钮 ====== */
.sidebar-settings-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sidebar-settings-btn:hover {
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
}"""

new_settings_css = """/* ====== 设置按钮 (同步管理员入口风格) ====== */
.sidebar-settings-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}

.sidebar-settings-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.3);
  opacity: 0.95;
}

.sidebar-settings-btn:active {
  transform: translateY(0);
}"""

if old_settings_css in content:
    content = content.replace(old_settings_css, new_settings_css)
    print("✅ 设置按钮样式已同步为紫色风格")
else:
    # 如果没匹配到，尝试用正则匹配或重新插入
    import re
    content = re.sub(r'\.sidebar-settings-btn\s*\{.*?\}', new_settings_css, content, flags=re.DOTALL)
    print("⚠️ 采用正则匹配替换样式")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
