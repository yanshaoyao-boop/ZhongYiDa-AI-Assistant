import re

path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend-uniapp\src\pages\chat\chat.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 强力同色：把所有黄色替换为 Web 版的蓝色
# 原色：#f59e0b (琥珀黄) -> Web色：#2563eb (专业蓝)
content = content.replace("#f59e0b", "#2563eb")
# 替换文字：全能助手
content = content.replace("全能助手", "小易全能助手")

# 2. 强力布局：在 <style scoped> 的最开头插入卡片布局代码
# 这样它比后面的旧样式优先级更高
style_tag = "<style scoped>"
if style_tag in content:
    # 注入一套极高权重的 Web 风格 CSS
    web_sync_css = """
/* ======= 深度 Web 一致性重构 ======= */
:deep(.zen-card-button), 
.zen-card-button {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  border-radius: 20px !important;
  padding: 30rpx 40rpx !important;
  margin: 15rpx 20rpx !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-start !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
  width: auto !important;
  height: auto !important;
}

.zen-card-title {
  font-size: 32rpx !important;
  font-weight: 700 !important;
  color: #1e293b !important;
  margin-bottom: 8rpx !important;
  display: block !important;
}

.zen-card-desc {
  font-size: 24rpx !important;
  color: #64748b !important;
  display: block !important;
}

.zen-welcome-stage {
  padding-top: 40rpx !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
}
"""
    content = content.replace(style_tag, style_tag + "\n" + web_sync_css, 1)
    print("✅ Web 风格强力注入成功！")
else:
    print("⚠️ 未找到 style 标签")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("🎉 小程序 UI 已通过覆盖技术全面蓝化并对齐 Web 端！")
