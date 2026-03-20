import re

path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend-uniapp\src\pages\chat\chat.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 修正变量定义
# 修复之前注入错误的文本
content = content.replace("const isIntelOpen = ref(false)\\nconst isIntelCollapsed = ref(false)", 
                          "const isIntelOpen = ref(false)\nconst isIntelCollapsed = ref(false)")

# 2. 修改模板：在面板头部增加折叠按钮
# 我们找到 <text class="panel-close" @tap="isIntelOpen = false">×</text> 并在此之前插入折叠按钮
old_close = '<text class="panel-close" @tap="isIntelOpen = false">×</text>'
new_header_btns = '<view class="panel-header-btns">' + \
                  '<text class="panel-collapse-btn" @tap="isIntelCollapsed = true">－</text>' + \
                  '<text class="panel-close" @tap="isIntelOpen = false">×</text>' + \
                  '</view>'

content = content.replace(old_close, new_header_btns)

# 3. 增加折叠后的悬浮球 (在面板外部)
# 只要 Intel 面板开启且处于折叠状态，就显示这个标签
collapsed_tag = """
<view v-if="isIntelOpen && isIntelCollapsed" class="combat-intel-minimized" @tap="isIntelCollapsed = false">
    <text class="minimized-icon">📊</text>
    <text class="minimized-text">实战情报</text>
</view>
"""
# 插入在情报面板容器之前
content = content.replace("<view :class=\"['combat-intel-panel'", collapsed_tag + "\n<view :class=\"['combat-intel-panel'")

# 4. 调整面板容器的 Class，支持 colllapsed 状态
content = content.replace("{ show: isIntelOpen }]", "{ show: isIntelOpen, collapsed: isIntelCollapsed }]")

# 5. 注入 CSS 样式
collapse_css = """
/* 实战情报中心折叠逻辑 */
.combat-intel-panel.collapsed {
    transform: translateX(110%) !important;
    pointer-events: none !important;
}

.panel-header-btns {
    display: flex;
    align-items: center;
    gap: 15px;
}

.panel-collapse-btn {
    font-size: 40rpx;
    color: #64748b;
    padding: 10rpx;
    line-height: 1;
}

.combat-intel-minimized {
    position: fixed;
    right: 0;
    top: 30%;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-right: none;
    border-radius: 40rpx 0 0 40rpx;
    padding: 16rpx 20rpx 16rpx 30rpx;
    display: flex;
    align-items: center;
    gap: 8rpx;
    box-shadow: -4rpx 8rpx 24rpx rgba(0, 0, 0, 0.1);
    z-index: 999;
    animation: slideInRight 0.3s ease;
}

@keyframes slideInRight {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
}

.minimized-icon {
    font-size: 32rpx;
}

.minimized-text {
    font-size: 24rpx;
    font-weight: 600;
    color: #5046e5;
    white-space: nowrap;
}
"""

# 注入到末尾的 </style> 之前
if "</style>" in content:
    content = content.replace("</style>", collapse_css + "\n</style>", 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 灵动折叠面板逻辑已部署！")
