import re

path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend\src\views\ChatView.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 查找 .sidebar-admin-btn 的原始样式块，精确提取参数
admin_btn_match = re.search(r'\.sidebar-admin-btn\s*\{([^}]*)\}', content, re.DOTALL)
if admin_btn_match:
    admin_styles = admin_btn_match.group(1).strip()
    print("✅ 成功提取管理员入口按钮样式")
    
    # 2. 构造设置按钮的克隆样式，同时保持 flex 居中
    # 由于 a 标签和 button 标签在默认盒模型上略有不同，我会通过盒模型校准来保证视觉一致
    cloned_css = f""".sidebar-settings-btn {{
  {admin_styles}
  display: flex; /* 确保内容居中 */
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  cursor: pointer;
  border: none;
  font-family: inherit; /* 统一字体 */
}}"""
    
    # 3. 更新设置按钮样式（包括 hover 状态也同步）
    # 我们找一个典型的 .sidebar-admin-btn:hover 样式
    admin_hover_match = re.search(r'\.sidebar-admin-btn:hover\s*\{([^}]*)\}', content, re.DOTALL)
    if admin_hover_match:
        admin_hover_styles = admin_hover_match.group(1).strip()
        cloned_css += f"\n\n.sidebar-settings-btn:hover {{\n  {admin_hover_styles}\n  opacity: 0.9; \n}}"
    
    # 执行替换
    content = re.sub(r'\.sidebar-settings-btn\s*\{.*?\}\s*\.sidebar-settings-btn:hover\s*\{.*?\}', cloned_css, content, flags=re.DOTALL)
    # 兜底：如果上面的正则没匹配到（因为样式还没加 hover），就只换基础块
    if "sidebar-settings-btn" not in content or admin_styles[:10] not in content:
        content = re.sub(r'\.sidebar-settings-btn\s*\{.*?\}', cloned_css, content, flags=re.DOTALL)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("🎉 设置按钮已完美克隆管理员入口的尺寸和圆角参数！")
else:
    print("⚠️ 未能提取到管理员入口样式，请检查文件内容。")
