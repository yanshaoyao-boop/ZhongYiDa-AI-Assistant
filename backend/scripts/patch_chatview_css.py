"""
向 ChatView.vue 的 <style scoped> 末尾注入设置弹窗所需的 CSS 样式。
"""
path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend\src\views\ChatView.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

settings_css = """
/* ====== 设置按钮 ====== */
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
}

/* ====== 设置弹窗 ====== */
.settings-modal {
  width: 460px;
  max-width: 95vw;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.settings-section {
  padding: 20px 0;
}
.settings-label {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}
.settings-desc {
  font-size: 12px;
  color: #94a3b8;
  margin: 0 0 14px;
}
.settings-divider {
  height: 1px;
  background: #f1f5f9;
  margin: 4px 0;
}

/* 输出长度选项 */
.output-length-group {
  display: flex;
  gap: 10px;
}
.length-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 8px;
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  background: #f8fafc;
  cursor: pointer;
  transition: all 0.2s ease;
}
.length-btn:hover {
  border-color: #6366f1;
  background: #f0f0ff;
}
.length-btn.active {
  border-color: #6366f1;
  background: linear-gradient(135deg, #ede9fe, #e0e7ff);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}
.length-icon { font-size: 22px; }
.length-label { font-size: 13px; font-weight: 700; color: #1e293b; }
.length-desc { font-size: 10px; color: #94a3b8; text-align: center; line-height: 1.3; }

/* 密码修改表单 */
.pwd-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.settings-input {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: 13px;
  color: #1e293b;
  background: #f8fafc;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.settings-input:focus {
  border-color: #6366f1;
  background: #fff;
}
.pwd-msg {
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}
.pwd-msg.success { background: #f0fdf4; color: #16a34a; }
.pwd-msg.error { background: #fff1f2; color: #dc2626; }
.pwd-submit-btn {
  padding: 11px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s;
}
.pwd-submit-btn:hover:not(:disabled) { opacity: 0.88; }
.pwd-submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
"""

# 在 </style> 前最后插入
end_style = "</style>"
last_style_idx = content.rfind(end_style)
if last_style_idx != -1:
    content = content[:last_style_idx] + settings_css + "\n" + content[last_style_idx:]
    print("✅ CSS 样式注入成功")
else:
    print("⚠️  未找到 </style> 标签")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("🎉 CSS 写入完成！")
