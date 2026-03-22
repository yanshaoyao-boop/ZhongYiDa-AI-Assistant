<template>
	<view class="welcome-screen-root">
		<!-- 全能助手模式欢迎 -->
		<view v-if="mode === 'general'" class="zen-welcome-stage welcome-centered">
			<view class="welcome-content welcome-panel">
				<view class="zen-avatar-breathe">
					<image :src="aiAvatar" mode="aspectFit" class="zen-avatar-img" />
				</view>
				<text class="zen-title">{{ userName }} 您好，我是小易</text>
				<text class="zen-subtitle">{{ welcomeMsg }}</text>

				<view class="suggestion-chips suggestion-chip-shell">
					<view class="zen-suggestion-grid">
						<button class="zen-card zen-card-button" @tap="$emit('presetMsg', '我能帮你做哪些事情')">
							<view class="zen-card-content">
								<text class="zen-card-title">查看核心能力</text>
								<text class="zen-card-desc">了解我能帮您完成的物流与办公任务</text>
							</view>
						</button>
						<button class="zen-card zen-card-button" @tap="$emit('presetMsg', '如何正确使用小易')">
							<view class="zen-card-content">
								<text class="zen-card-title">获取使用指南</text>
								<text class="zen-card-desc">掌握与小易合作的最佳提示词技巧</text>
							</view>
						</button>
					</view>
				</view>
			</view>
		</view>

		<!-- 专家指导模式欢迎 -->
		<view v-else-if="mode === 'expert'" class="zen-welcome-stage expert-stage welcome-centered mode-stage-offset">
			<view class="zen-expert-icon">
				<text class="expert-emoji">💡</text>
			</view>
			<text class="zen-title zen-title-expert">专家指导</text>
			<text class="zen-subtitle">请描述您遇到的模糊或复杂的问题，我会通过 1-2 轮追问帮你理清思路并提供专业建议。</text>
		</view>

		<!-- 知识教练模式欢迎 -->
		<view v-else-if="mode === 'coach'" class="zen-welcome-stage coach-stage welcome-centered">
			<!-- 教练答题流程 -->
			<view v-if="coachQuizSession" class="coach-quiz-stage">
				<!-- 答题总结 -->
				<view v-if="coachQuizSession.completed" class="coach-quiz-card coach-quiz-summary-premium glass-panel">
					<view class="summary-visual">
						<text class="summary-emoji">🏆</text>
					</view>
					<text class="summary-title-main">训练任务达成</text>
					<view class="summary-score-row">
						<view class="score-card">
							<text class="score-val">{{ coachQuizSession.correctCount }}</text>
							<text class="score-lab">答对</text>
						</view>
						<view class="score-line"></view>
						<view class="score-card">
							<text class="score-val">{{ Math.round((coachQuizSession.correctCount / coachQuizSession.questions.length) * 100) }}%</text>
							<text class="score-lab">正确率</text>
						</view>
					</view>
					<text class="summary-note">坚持每日训练，是通往业务专家的必经之路。</text>
					<view class="premium-actions-stack">
						<button class="quiz-primary-stack-btn" @tap="$emit('restartQuiz')">重新发起训练</button>
						<button class="quiz-ghost-stack-btn" @tap="$emit('switchCoachEntry', 'menu')">返回教练菜单</button>
					</view>
				</view>

				<!-- 答题进行中 -->
				<view v-else-if="currentCoachQuizQuestion" class="coach-quiz-panel-premium glass-panel">
					<view class="quiz-panel-head">
						<view class="quiz-panel-tag">
							<text class="tag-primary">知识训练</text>
							<text v-if="currentCoachQuizQuestion.category" class="tag-secondary">{{ currentCoachQuizQuestion.category }}</text>
						</view>
						<text class="quiz-panel-progress">{{ coachQuizSession.currentIndex + 1 }} / {{ coachQuizSession.questions.length }}</text>
					</view>
					
					<view class="quiz-panel-question">
						<text class="question-text">{{ currentCoachQuizQuestion.question }}</text>
					</view>

					<view class="quiz-panel-options">
						<button
							v-for="option in currentCoachQuizQuestion.options"
							:key="option.key"
							class="quiz-panel-option-btn"
							:class="getOptionClass(option.key)"
							:disabled="Boolean(currentCoachQuizQuestion.selectedAnswer)"
							@tap="$emit('selectQuizAnswer', option.key)"
						>
							<view class="opt-prefix">{{ option.key }}</view>
							<text class="opt-label">{{ option.text }}</text>
							<view class="opt-status">
								<text v-if="currentCoachQuizQuestion.selectedAnswer && currentCoachQuizQuestion.answer === option.key" class="opt-ico-correct">✔</text>
								<text v-else-if="currentCoachQuizQuestion.selectedAnswer === option.key && currentCoachQuizQuestion.selectedAnswer !== currentCoachQuizQuestion.answer" class="opt-ico-wrong">✘</text>
							</view>
						</button>
					</view>

					<view
						v-if="currentCoachQuizQuestion.selectedAnswer"
						class="quiz-panel-feedback"
						:class="{ 'is-correct': currentCoachQuizQuestion.isCorrect, 'is-wrong': !currentCoachQuizQuestion.isCorrect }"
					>
						<view class="feedback-head-row">
							<text class="fb-icon">{{ currentCoachQuizQuestion.isCorrect ? '✅' : '❌' }}</text>
							<text class="fb-title">{{ currentCoachQuizQuestion.isCorrect ? '回答正确' : '回答错误' }}</text>
						</view>
						<view class="fb-body">
							<text class="fb-ans">正确答案：{{ currentCoachQuizQuestion.answer }}</text>
							<text v-if="currentCoachQuizQuestion.explanation" class="fb-expl">{{ currentCoachQuizQuestion.explanation }}</text>
						</view>
					</view>

					<view class="quiz-panel-actions">
						<button class="quiz-btn-nav ghost" @tap="$emit('restartQuiz')">重试</button>
						<button class="quiz-btn-nav primary" :disabled="!currentCoachQuizQuestion.selectedAnswer" @tap="$emit('nextQuizQuestion')">
							<text>{{ coachQuizSession.currentIndex === coachQuizSession.questions.length - 1 ? '查看总结' : '下一题' }}</text>
							<text class="ico-next">→</text>
						</button>
					</view>
				</view>
			</view>

			<!-- 正常教练菜单 -->
			<view v-else>
				<text class="zen-title zen-title-coach">知识教练</text>
				<text class="zen-subtitle">场景化陪练，帮助你把经验真正练到手。</text>

				<!-- 入口选择 -->
				<view v-if="coachEntryMode === 'menu'" class="coach-entry-grid">
					<button class="zen-level-card zen-level-card-button coach-entry-card" @tap="$emit('switchCoachEntry', 'duel')">
						<view class="zen-card-huge-emoji">🎯</view>
						<view class="zen-level-info">
							<text class="zen-level-title">实战对练</text>
							<text class="zen-level-desc-mini">模拟真实客户对话场景，磨练报价、排雷、逼单技巧。</text>
						</view>
					</button>
					<button class="zen-level-card zen-level-card-button coach-entry-card" @tap="$emit('switchCoachEntry', 'quiz')">
						<view class="zen-card-huge-emoji">📝</view>
						<view class="zen-level-info">
							<text class="zen-level-title">每日一练</text>
							<text class="zen-level-desc-mini">随机抽取业务知识题，通过单选卡片加深记忆。</text>
						</view>
					</button>
				</view>

				<!-- 题量选择 -->
				<view v-else-if="coachEntryMode === 'quiz'" class="coach-quiz-picker-premium glass-panel">
					<button class="picker-back-btn" @tap="$emit('switchCoachEntry', 'menu')">
						<text class="ico-back">←</text> 返回
					</button>
					<view class="picker-title-pnl">
						<text class="p-title">题目数量</text>
						<text class="p-subtitle">点击下方选项即可立即开始训练</text>
					</view>
					<view class="count-grid-modern">
						<button v-for="count in [5, 10, 20]" :key="count" class="count-card-item" @tap="$emit('startQuizSession', count)">
							<text class="c-num">{{ count }}</text>
							<text class="c-unit">道题</text>
						</button>
					</view>
				</view>

				<!-- 实战航线选择 -->
				<view v-else class="coach-selection-shell">
					<view class="zen-level-header">
						<text class="coach-step-pill">{{ coachStepLabel }}</text>
					</view>

					<view v-if="!selectedRegion" class="zen-level-grid">
						<button v-for="reg in coachRegions" :key="reg.name" class="zen-level-card zen-level-card-button" @tap="$emit('update:selectedRegion', reg.name)">
							<view class="zen-card-huge-icon">{{ reg.short }}</view>
							<view class="zen-level-info">
								<text class="zen-level-title">{{ reg.name }}</text>
								<text class="zen-level-desc-mini">{{ reg.desc }}</text>
							</view>
						</button>
					</view>

					<view v-else-if="!selectedPersona" class="zen-level-grid slide-in">
						<view class="coach-selection-summary">
							<button class="zen-breadcrumb" @tap="$emit('update:selectedRegion', null)">
								{{ selectedRegion }} <text class="arrow">←</text>
							</button>
						</view>
						<button v-for="persona in coachPersonas" :key="persona.name" class="zen-level-card zen-level-card-button" @tap="$emit('update:selectedPersona', persona.name)">
							<view class="zen-card-huge-emoji">{{ persona.emoji }}</view>
							<view class="zen-level-info">
								<text class="zen-level-title">{{ persona.name }}</text>
								<text class="zen-level-desc-mini">{{ persona.desc }}</text>
							</view>
						</button>
					</view>

					<view v-else class="zen-level-grid slide-in">
						<view class="coach-selection-summary">
							<button class="zen-breadcrumb" @tap="$emit('update:selectedPersona', null)">
								{{ selectedPersona }} <text class="arrow">←</text>
							</button>
						</view>
						<button v-for="subject in coachSubjects" :key="subject.name" class="zen-level-card zen-level-card-button" @tap="$emit('startDuel', subject.name)">
							<view class="zen-card-huge-emoji">{{ subject.emoji }}</view>
							<view class="zen-level-info">
								<text class="zen-level-title">{{ subject.name }}</text>
								<text class="zen-level-desc-mini">{{ subject.desc }}</text>
							</view>
						</button>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	mode: String,
	userName: String,
	welcomeMsg: String,
	aiAvatar: {
		type: String,
		default: '/static/xiaoyi_transparent.png'
	},
	coachEntryMode: String,
	coachQuizSession: Object,
	currentCoachQuizQuestion: Object,
	selectedRegion: String,
	selectedPersona: String,
	coachRegions: Array,
	coachPersonas: Array,
	coachSubjects: Array
})

defineEmits([
	'presetMsg', 
	'switchCoachEntry', 
	'startQuizSession', 
	'restartQuiz', 
	'selectQuizAnswer', 
	'nextQuizQuestion',
	'update:selectedRegion',
	'update:selectedPersona',
	'startDuel'
])

const coachStepLabel = computed(() => {
	if (!props.selectedRegion) return '第一阶段 · 选择实战航线'
	if (!props.selectedPersona) return '第二阶段 · 选择客户背景'
	return '最后阶段 · 选择训练科目'
})

const getOptionClass = (optionKey) => {
	const question = props.currentCoachQuizQuestion
	if (!question?.selectedAnswer) return ''
	if (question.answer === optionKey) return 'correct'
	if (question.selectedAnswer === optionKey) return 'wrong'
	return ''
}
</script>

<style scoped>
.welcome-screen-root {
	padding: 40px 20px;
}

.welcome-centered {
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
}

.zen-avatar-breathe {
	width: 120px;
	height: 120px;
	margin-bottom: 24px;
	animation: breathe 4s infinite ease-in-out;
}

@keyframes breathe {
	0%, 100% { transform: scale(1); opacity: 0.9; }
	50% { transform: scale(1.05); opacity: 1; }
}

.zen-avatar-img {
	width: 100%;
	height: 100%;
}

.zen-title {
	font-size: 24px;
	font-weight: 700;
	color: #1e293b;
	margin-bottom: 12px;
}

.zen-subtitle {
	font-size: 15px;
	color: #64748b;
	margin-bottom: 32px;
	line-height: 1.6;
}

.zen-suggestion-grid {
	display: grid;
	grid-template-columns: 1fr;
	gap: 16px;
	width: 100%;
	max-width: 400px;
}

.zen-card {
	padding: 16px;
	border-radius: 16px;
	background: #ffffff;
	border: 1px solid rgba(0, 0, 0, 0.05);
	text-align: left;
	transition: all 0.2s;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
}

.zen-card-title {
	font-size: 15px;
	font-weight: 600;
	color: #1e293b;
	display: block;
	margin-bottom: 4px;
}

.zen-card-desc {
	font-size: 12px;
	color: #94a3b8;
}

/* 专家/教练 统一卡片系统 */
.zen-level-grid, .coach-entry-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 16px;
	width: 100%;
}

.zen-level-card {
	background: #ffffff;
	border-radius: 20px;
	padding: 20px 16px;
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
	border: 1px solid rgba(0, 0, 0, 0.05);
	transition: all 0.3s;
}

.zen-card-huge-emoji, .zen-card-huge-icon {
	font-size: 40px;
	margin-bottom: 16px;
}

.zen-level-title {
	font-size: 16px;
	font-weight: 700;
	color: #1e293b;
	margin-bottom: 8px;
	display: block;
}

.zen-level-desc-mini {
	font-size: 11px;
	color: #94a3b8;
	line-height: 1.4;
}

.coach-step-pill {
	background: #2563eb;
	color: #ffffff;
	font-size: 12px;
	padding: 4px 12px;
	border-radius: 20px;
	margin-bottom: 12px;
	display: inline-block;
}

/* 答题卡片 */
.coach-quiz-panel-premium {
	padding: 24px;
	width: 100%;
}

.quiz-panel-head {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.tag-primary {
	background: #dbeafe;
	color: #2563eb;
	font-size: 11px;
	font-weight: 600;
	padding: 2px 8px;
	border-radius: 4px;
	margin-right: 8px;
}

.tag-secondary {
	color: #94a3b8;
	font-size: 11px;
}

.quiz-panel-progress {
	font-size: 13px;
	color: #64748b;
}

.question-text {
	font-size: 18px;
	font-weight: 600;
	color: #1e293b;
	line-height: 1.5;
	margin-bottom: 24px;
	display: block;
}

.quiz-panel-options {
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.quiz-panel-option-btn {
	display: flex;
	align-items: center;
	padding: 14px 16px;
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	text-align: left;
	transition: all 0.2s;
}

.quiz-panel-option-btn.correct {
	background: #ecfdf5;
	border-color: #10b981;
}

.quiz-panel-option-btn.wrong {
	background: #fef2f2;
	border-color: #ef4444;
}

.opt-prefix {
	width: 28px;
	height: 28px;
	background: #ffffff;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 12px;
	font-weight: 700;
	font-size: 13px;
	flex-shrink: 0;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.opt-label {
	flex: 1;
	font-size: 15px;
	color: #475569;
}

.opt-status {
	width: 20px;
	height: 20px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.opt-ico-correct { color: #10b981; font-weight: bold; }
.opt-ico-wrong { color: #ef4444; font-weight: bold; }

.quiz-panel-feedback {
	margin-top: 24px;
	padding: 16px;
	border-radius: 12px;
	background: #f1f5f9;
}

.feedback-head-row {
	display: flex;
	align-items: center;
	margin-bottom: 8px;
}

.fb-title {
	font-weight: 700;
	font-size: 14px;
	margin-left: 8px;
}

.fb-ans {
	font-weight: 600;
	font-size: 13px;
	display: block;
	margin-bottom: 4px;
}

.fb-expl {
	font-size: 12px;
	color: #64748b;
	line-height: 1.5;
}

.quiz-panel-actions {
	display: flex;
	gap: 12px;
	margin-top: 24px;
}

.quiz-btn-nav {
	flex: 1;
	height: 48px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 15px;
	font-weight: 600;
}

.quiz-btn-nav.primary {
	background: #2563eb;
	color: #ffffff;
}

.quiz-btn-nav.ghost {
	background: #f1f5f9;
	color: #64748b;
}

/* 总结卡片 */
.coach-quiz-summary-premium {
	padding: 40px 24px;
	text-align: center;
}

.summary-emoji {
	font-size: 64px;
	display: block;
	margin-bottom: 16px;
}

.summary-score-row {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 32px;
	margin: 24px 0;
}

.score-val {
	font-size: 32px;
	font-weight: 800;
	color: #1e293b;
	display: block;
}

.score-lab {
	font-size: 12px;
	color: #94a3b8;
}

.score-line {
	width: 1px;
	height: 40px;
	background: #e2e8f0;
}

.premium-actions-stack {
	display: flex;
	flex-direction: column;
	gap: 12px;
	margin-top: 32px;
}

.quiz-primary-stack-btn {
	height: 48px;
	background: #2563eb;
	color: #ffffff;
	border-radius: 14px;
	font-size: 15px;
	font-weight: 600;
}

.quiz-ghost-stack-btn {
	height: 48px;
	background: transparent;
	color: #64748b;
	font-size: 14px;
}
</style>
