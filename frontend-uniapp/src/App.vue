<script>
	import { captureAppError, captureUnhandledRejection } from './utils/error-logger'

    export default {
        onLaunch() {
            console.log('App Launch')
        },
        onShow() {
            console.log('App Show')
        },
        onHide() {
            console.log('App Hide')
        },
        onError(error) {
            captureAppError(error, { hook: 'onError' })
        },
        onUnhandledRejection(event) {
            captureUnhandledRejection(event)
        }
    }
</script>

<style>
	/* 每个页面公共css */
	page {
		/* --- 高级 HSL 配色方案 --- */
		
		/* 全能助手: 琥珀渐变 */
		--theme-general: 38, 92%, 50%; /* #F59E0B */
		--theme-general-soft: 38, 92%, 95%; 
		--theme-general-glow: hsla(38, 92%, 50%, 0.15);

		/* 知识教练: 翡翠森林 */
		--theme-coach: 161, 84%, 39%; /* #10B981 */
		--theme-coach-soft: 161, 84%, 96%;
		--theme-coach-glow: hsla(161, 84%, 39%, 0.12);

		/* 专家指导: 蔚蓝深海 */
		--theme-expert: 217, 91%, 60%; /* #3B82F6 */
		--theme-expert-soft: 217, 91%, 97%;
		--theme-expert-glow: hsla(217, 91%, 60%, 0.12);
		
		/* 基础中性色 */
		--slate-50:  210, 40%, 98%;
		--slate-100: 210, 40%, 96%;
		--slate-200: 214, 32%, 91%;
		--slate-400: 215, 25%, 65%;
		--slate-600: 215, 19%, 35%;
		--slate-900: 222, 47%, 11%;

		--bg-app: #FDFEFE;
		--card-white: #FFFFFF;
		
		/* --- 设计规范 --- */
		--radius-soft: 24rpx;
		--radius-pill: 999rpx;
		--radius-card: 40rpx;
		--radius-xl: 60rpx;

		/* 深度投影系统 */
		--shadow-deep: 0 20rpx 50rpx -12rpx rgba(0, 0, 0, 0.08);
		--shadow-soft: 0 8rpx 30rpx rgba(0, 0, 0, 0.03);
		--shadow-border: 0 0 0 1px rgba(0, 0, 0, 0.02);
		
		font-family: -apple-system, system-ui, "SF Pro Text", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
		-webkit-font-smoothing: antialiased;
	}

	view, scroll-view, swiper, button, input, textarea, label, navigator, image {
		box-sizing: border-box;
	}

	page {
		height: 100%;
		background-color: var(--bg-primary);
		color: var(--text-primary);
		font-size: 28rpx;
	}

	/* 新一代卡片面板规范 */
	.glass-panel {
		background: var(--bg-secondary);
		border: 1px solid var(--border-light);
		box-shadow: var(--shadow-md);
		border-radius: var(--radius-lg);
	}

	.gradient-text {
		color: var(--theme-general-primary);
		font-weight: bold;
	}

	button {
		font-family: inherit;
		border: none;
		background: none;
		padding: 0;
		margin: 0;
		line-height: normal;
	}

	button::after {
		border: none;
	}
</style>
