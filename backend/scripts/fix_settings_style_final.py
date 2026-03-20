path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend\src\views\ChatView.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 采用更深、更沉稳的紫色方案（#5046e5 是更接近管理员入口的饱和色）
# 取消渐变中的浅色部分，加强阴影

new_settings_css = """/* ====== 设置按钮 (同步管理员入口风格 - 深度优化) ====== */
.sidebar-settings-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 13px;
  margin-bottom: 14px;
  background: #5046e5; /* 调深紫色 */
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.2);
}

.sidebar-settings-btn:hover {
  background: #4338ca; /* 悬停时更深 */
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.3);
}

.sidebar-settings-btn:active {
  transform: translateY(1px);
  background: #3730a3;
}"""

# 替换现有的 .sidebar-settings-btn 样式
import re
content = re.sub(r'\.sidebar-settings-btn\s*\{.*?\}\s*\.sidebar-settings-btn:hover\s*\{.*?\}\s*\.sidebar-settings-btn:active\s*\{.*?\}', new_settings_css, content, flags=re.DOTALL)

# 如果上面的正则失效，再尝试更通用的正则
if ".sidebar-settings-btn" not in content or "5046e5" not in content:
     content = re.sub(r'\.sidebar-settings-btn\s*\{.*?\}', new_settings_css, content, flags=re.DOTALL)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
