"""
注入针对小程序“欢迎屏”及整体布局的高级 Web 端审美重构 CSS
"""
path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\frontend-uniapp\src\pages\chat\chat.vue"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

advanced_ui_css = """
/* ======= 独家定制：Web级高端 UI 布局修复 (2026-03 Refactor) ======= */

/* 1. 修复欢迎屏中心布局与间距 */
.welcome-content {
	display: flex !important;
	flex-direction: column !important;
	align-items: center !important;
	justify-content: center !important;
	width: 100% !important;
	transform: translateY(-4vh) !important;
}

/* 2. 让头像呼吸发光 */
.zen-avatar-img {
	width: 140rpx !important;
	height: 140rpx !important;
	border-radius: 50% !important;
	background: linear-gradient(135deg, #f8fafc, #e2e8f0) !important;
	padding: 12rpx !important;
	box-shadow: 0 12rpx 36rpx rgba(99, 102, 241, 0.15), inset 0 2px 4px rgba(255,255,255,0.8) !important;
	margin-bottom: 24rpx !important;
}

.zen-avatar-breathe {
	animation: floatAvatar 4s ease-in-out infinite !important;
}

@keyframes floatAvatar {
	0%, 100% { transform: translateY(0); }
	50% { transform: translateY(-10rpx); }
}

/* 3. 字体层次：高级、克制、醒目 */
.zen-title {
	font-size: 44rpx !important;
	font-weight: 800 !important;
	background: linear-gradient(135deg, #1e293b 0%, #475569 100%) !important;
	-webkit-background-clip: text !important;
	color: transparent !important;
	letter-spacing: 2rpx !important;
	margin-bottom: 16rpx !important;
	line-height: 1.2 !important;
}

.zen-title-expert {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
    -webkit-background-clip: text !important;
    color: transparent !important;
}

.zen-title-coach {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
    -webkit-background-clip: text !important;
    color: transparent !important;
}

.zen-subtitle {
	font-size: 28rpx !important;
	color: #64748b !important;
	font-weight: 500 !important;
	max-width: 85% !important;
	text-align: center !important;
	line-height: 1.5 !important;
	margin-bottom: 60rpx !important;
}

/* 4. 重构卡片网格 (解决粘连、居中、和按钮默认流破坏) */
.suggestion-chips {
	width: 100% !important;
	padding: 0 40rpx !important;
	box-sizing: border-box !important;
}

.zen-suggestion-grid, .zen-level-grid, .coach-entry-grid {
	display: flex !important;
	flex-direction: column !important;
	gap: 24rpx !important;
	width: 100% !important;
	box-sizing: border-box !important;
}

/* 如果是小程序教练页的并排网格 */
.coach-entry-grid {
    flex-direction: row !important;
}
.coach-entry-card {
    flex: 1 !important;
}

/* 5. 重新定义卡片（Web级玻璃拟态） */
.zen-card.zen-card-button, .zen-level-card.zen-level-card-button {
	background: rgba(255, 255, 255, 0.8) !important;
	backdrop-filter: blur(20px) !important;
	-webkit-backdrop-filter: blur(20px) !important;
	border: 2rpx solid rgba(255, 255, 255, 0.9) !important;
	border-radius: 36rpx !important;
	padding: 36rpx 40rpx !important;
	box-shadow: 0 12rpx 40rpx rgba(31, 38, 135, 0.05), inset 0 2px 4px rgba(255, 255, 255, 0.8) !important;
	display: flex !important;
	flex-direction: column !important;
	align-items: flex-start !important;
	text-align: left !important;
	width: 100% !important;
	line-height: normal !important;
	box-sizing: border-box !important;
	position: relative !important;
	overflow: hidden !important;
}

.zen-card.zen-card-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 100%;
    background: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 100%);
    pointer-events: none;
}

.zen-card-content, .zen-level-info {
	display: flex !important;
	flex-direction: column !important;
	gap: 8rpx !important;
	width: 100% !important;
}

.zen-card-title, .zen-level-title {
	font-size: 32rpx !important;
	font-weight: 700 !important;
	color: #1e293b !important;
	display: block !important;
}

.zen-card-desc, .zen-level-desc-mini {
	font-size: 24rpx !important;
	color: #94a3b8 !important;
	font-weight: 500 !important;
	display: block !important;
	white-space: normal !important;
	word-wrap: break-word !important;
	line-height: 1.4 !important;
}

/* 6. 解决输入区域上边缘过硬的问题 */
.mp-chat-footer {
	background: linear-gradient(to bottom, rgba(248,250,252,0) 0%, rgba(248,250,252,0.95) 20%, #f8fafc 100%) !important;
}
"""

end_style = "</style>"
idx = content.rfind(end_style)
if idx != -1:
    content = content[:idx] + advanced_ui_css + "\n" + content[idx:]
    print("CSS Injected!")
else:
    print("Tag </style> not found")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
