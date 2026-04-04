<template>
	<div class="welcome-screen">
		<!-- 全能助手模式 -->
		<template v-if="mode === 'general'">
			<div class="welcome-brand fadeIn">
				<img src="@/assets/xiaoyi_image.png" alt="小易形象" class="welcome-avatar" />
				<h2 class="welcome-name">{{ welcomeMsg }}</h2>
			</div>
			<div class="suggestion-chips fadeIn">
				<button @click="$emit('presetMsg', '我能帮你做哪些事')">🤖 我能帮你做哪些事</button>
				<button @click="$emit('presetMsg', '如何正确的使用小易')">📖 如何正确的使用小易</button>
			</div>
		</template>

		<!-- 专家指导模式 -->
		<template v-else-if="mode === 'expert'">
			<div class="expert-welcome fadeIn">
				<div class="icon-circle"><FileQuestion size="40" /></div>
				<h2 class="welcome-name">欢迎来到专家指导模式</h2>
				<p class="welcome-slogan">请描述您遇到的模糊或复杂的问题，我会通过 1-2 轮追问帮你理清思路并提供专业建议。</p>
			</div>
		</template>

		<!-- 知识教练模式 -->
		<template v-else-if="mode === 'coach'">
			<h2 class="welcome-name coach-mode-title">欢迎来到知识教练模式</h2>
			
			<!-- 入口选择：对练 vs 出题 -->
			<div v-if="coachSubMode === 'entrance'" class="coach-gates fadeIn">
				<div class="category-main-card gate-card" @click="$emit('update:coachSubMode', 'practice')">
					<div class="cat-icon-lg"><Zap size="48" /></div>
					<div class="cat-info">
						<h3>教练对练</h3>
						<p>场景化沉浸式对练，模拟真实业务沟通</p>
					</div>
				</div>
				<div class="category-main-card gate-card" @click="$emit('startQuiz')">
					<div class="cat-icon-lg"><Target size="48" /></div>
					<div class="cat-info">
						<h3>教练出题</h3>
						<p>单选题专项训练，巩固业务知识点</p>
					</div>
				</div>
			</div>

			<!-- 教练对练流程 -->
			<template v-if="coachSubMode === 'practice'">
				<div class="category-step-header fadeIn">
					<button class="back-link" @click="$emit('update:coachSubMode', 'entrance'); $emit('update:selectedRegion', null); $emit('update:selectedScenario', null)">← 返回主入口</button>
					<div class="category-step-label" v-if="!selectedRegion">第一步：选择实战航线</div>
				</div>
				
				<div class="category-grid fadeIn" v-if="!selectedRegion">
					<div v-for="reg in coachRegions" :key="reg.name" 
						class="category-main-card region-card" 
						@click="$emit('update:selectedRegion', reg.name)">
						<span class="cat-emoji">{{ reg.emoji }}</span>
						<div class="cat-info">
							<h3>{{ reg.name }}</h3>
							<p>{{ reg.desc }}</p>
						</div>
					</div>
				</div>

				<!-- 第二层：选择练习情景 -->
				<div class="category-step-header fadeIn" v-if="selectedRegion">
					<button class="back-link" @click="$emit('update:selectedRegion', null)">← 返回重选航线</button>
					<div class="category-step-label">第二步：选择【{{ selectedRegion }}】练习情景</div>
				</div>
				<div class="category-grid subjects fadeIn" v-if="selectedRegion">
					<div v-for="scene in coachScenarios" :key="scene.name" 
						class="category-main-card subject-card" 
						@click="$emit('startDuel', scene.name)">
						<span class="cat-emoji">{{ scene.emoji }}</span>
						<div class="cat-info">
							<h3>{{ scene.name }}</h3>
							<p>{{ scene.desc }}</p>
						</div>
					</div>
				</div>
			</template>

			<!-- 教练出题流程 -->
			<div v-if="coachSubMode === 'quiz'" class="quiz-flow fadeIn">
				<!-- 步 1：选择题量 -->
				<div v-if="quizStep === 'count_selection'" class="quiz-setup">
					<button class="back-link-quiz" @click="$emit('update:coachSubMode', 'entrance')">← 返回</button>
					<h3>请选择本次训练题量</h3>
					<div class="count-options">
						<button class="count-btn" @click="$emit('fetchQuestions', 5)">5 道题</button>
						<button class="count-btn" @click="$emit('fetchQuestions', 10)">10 道题</button>
						<button class="count-btn" @click="$emit('fetchQuestions', 20)">20 道题</button>
					</div>
				</div>

				<!-- 步 2：答题中 -->
				<div v-if="quizStep === 'answering'" class="quiz-card-container">
					<div class="quiz-progress">
						<span>题量进度: {{ currentQuizIdx + 1 }} / {{ quizQuestions.length }}</span>
						<div class="progress-bar">
							<div class="progress-fill" :style="{ width: ((currentQuizIdx + 1) / quizQuestions.length) * 100 + '%' }"></div>
						</div>
					</div>
					
					<div v-if="quizQuestions[currentQuizIdx]" class="quiz-card glass-panel">
						<div class="quiz-question">{{ quizQuestions[currentQuizIdx].question }}</div>
						<div class="quiz-options">
							<button 
								v-for="optObj in quizQuestions[currentQuizIdx].options" 
								:key="optObj.key"
								:class="['opt-btn', { 
									selected: selectedOption === optObj.key,
									correct: isQuizSubmitted && quizQuestions[currentQuizIdx].answer === optObj.key,
									wrong: isQuizSubmitted && selectedOption === optObj.key && quizQuestions[currentQuizIdx].answer !== optObj.key
								}]"
								@click="$emit('selectOption', optObj.key)"
								:disabled="isQuizSubmitted"
							>
								<span class="opt-label">{{ optObj.key }}</span>
								<span class="opt-text">{{ optObj.text }}</span>
								<CheckCircle v-if="isQuizSubmitted && quizQuestions[currentQuizIdx].answer === optObj.key" size="18" class="status-icon" />
								<XCircle v-if="isQuizSubmitted && selectedOption === optObj.key && quizQuestions[currentQuizIdx].answer !== optObj.key" size="18" class="status-icon" />
							</button>
						</div>

						<div v-if="isQuizSubmitted" class="quiz-feedback-box animate-in">
							<div :class="['feedback-header', selectedOption === quizQuestions[currentQuizIdx].answer ? 'text-correct' : 'text-wrong']">
								<template v-if="selectedOption === quizQuestions[currentQuizIdx].answer">
									<CheckCircle size="20" /> 回答正确！
								</template>
								<template v-else>
									<XCircle size="20" /> 回答错误。正确答案是 【{{ quizQuestions[currentQuizIdx].answer }}】
								</template>
							</div>
							<div class="quiz-explanation" v-if="quizQuestions[currentQuizIdx].explanation">
								<strong>解析：</strong>{{ quizQuestions[currentQuizIdx].explanation }}
							</div>
							<button class="next-quiz-btn" @click="$emit('nextQuestion')">
								{{ currentQuizIdx === quizQuestions.length - 1 ? '查看结果' : '下一题' }}
								<ChevronRight size="18" />
							</button>
						</div>
					</div>
				</div>

				<!-- 步 3：总结页 -->
				<div v-if="quizStep === 'result'" class="quiz-result-card glass-panel">
					<Trophy size="64" class="trophy-icon" />
					<h2>训练完成！</h2>
					<div class="result-stats">
						<div class="stat-item">
							<label>答对题数</label>
							<span class="stat-value text-correct">{{ quizStats.correct }}</span>
						</div>
						<div class="stat-item">
							<label>正确率</label>
							<span class="stat-value">{{ Math.round((quizStats.correct / quizStats.total) * 100) }}%</span>
						</div>
					</div>
					<button class="restart-quiz-btn" @click="$emit('restartQuiz')">
						<RotateCcw size="18" /> 重新开始
					</button>
				</div>
			</div>

			<div v-if="coachSubMode !== 'quiz'" class="suggestion-chips coach-bottom-chips fadeIn">
				<button @click="$emit('presetMsg', '能通俗地给我讲解一下什么是DDP和DDU吗？')">📖 常见物流基础名词讲解</button>
			</div>
		</template>
	</div>
</template>

<script setup>
import { Zap, Target, FileQuestion, CheckCircle, XCircle, Trophy, RotateCcw, ChevronRight } from 'lucide-vue-next'

defineProps({
	mode: {
		type: String,
		default: 'general'
	},
	welcomeMsg: {
		type: String,
		default: ''
	},
	coachSubMode: {
		type: String,
		default: 'entrance'
	},
	selectedRegion: {
		type: String,
		default: null
	},
	selectedScenario: {
		type: String,
		default: null
	},
	coachRegions: {
		type: Array,
		default: () => []
	},
	coachScenarios: {
		type: Array,
		default: () => []
	},
	// Quiz Props
	quizStep: {
		type: String,
		default: 'count_selection'
	},
	quizQuestions: {
		type: Array,
		default: () => []
	},
	currentQuizIdx: {
		type: Number,
		default: 0
	},
	selectedOption: {
		type: String,
		default: ''
	},
	isQuizSubmitted: {
		type: Boolean,
		default: false
	},
	quizStats: {
		type: Object,
		default: () => ({ correct: 0, total: 0 })
	}
})

defineEmits([
	'presetMsg', 'update:coachSubMode', 'startQuiz', 'restartQuiz', 
	'update:selectedRegion', 'update:selectedScenario', 'startDuel',
	'fetchQuestions', 'selectOption', 'nextQuestion'
])
</script>

<style scoped>
.welcome-screen {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 80px 20px;
	width: 100%;
	max-width: 900px;
	margin: 0 auto;
}

.fadeIn {
	animation: fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes fadeIn {
	from { opacity: 0; transform: translateY(10px); }
	to { opacity: 1; transform: translateY(0); }
}

.welcome-brand {
	text-align: center;
	margin-bottom: 40px;
}

.welcome-avatar {
	width: 140px;
	height: 140px;
	margin-bottom: 32px;
	filter: drop-shadow(0 15px 30px rgba(0, 0, 0, 0.08));
	animation: avatarFloat 3s ease-in-out infinite;
}

@keyframes avatarFloat {
	0%, 100% { transform: translateY(0); }
	50% { transform: translateY(-8px); }
}

.welcome-name {
	font-size: 28px;
	font-weight: 800;
	color: #1e293b;
	margin-bottom: 0;
	letter-spacing: -0.01em;
}

.welcome-slogan {
	font-size: 16px;
	font-weight: 500;
	color: #64748b;
	max-width: 500px;
	margin: 12px auto 0;
	line-height: 1.6;
}

.suggestion-chips {
	display: flex;
	flex-wrap: wrap;
	gap: 12px;
	justify-content: center;
}

.suggestion-chips button {
	padding: 10px 20px;
	background: #ffffff;
	border: 1px solid rgba(0, 0, 0, 0.05);
	border-radius: 999px;
	color: #475569;
	font-size: 14px;
	font-weight: 600;
	cursor: pointer;
	transition: all 0.2s;
	box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
}
.suggestion-chips button:hover {
	border-color: #2563eb;
	color: #2563eb;
	box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
	transform: translateY(-2px);
}

/* 专家页 */
.expert-welcome {
	text-align: center;
}
.icon-circle {
	width: 80px;
	height: 80px;
	background: #eff6ff;
	color: #3b82f6;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin: 0 auto 24px;
	box-shadow: 0 10px 20px rgba(59, 130, 246, 0.1);
}

/* 教练页 */
.coach-mode-title { margin-bottom: 40px; }
.coach-gates {
    display: flex;
    gap: 24px;
    width: 100%;
}

.category-main-card {
    flex: 1;
    background: #ffffff;
    border-radius: 20px;
    padding: 32px;
    border: 1px solid rgba(0,0,0,0.05);
    cursor: pointer;
    transition: all 0.3s;
    text-align: left;
    display: flex;
    align-items: flex-start;
    gap: 20px;
}
.category-main-card:hover { transform: translateY(-4px); border-color: #3b82f6; box-shadow: 0 20px 40px rgba(0,0,0,0.06); }

.cat-icon-lg { color: #3b82f6; }
.cat-info h3 { margin: 0 0 8px; font-size: 18px; color: #1e293b; }
.cat-info p { margin: 0; font-size: 13px; color: #94a3b8; }

.category-step-header {
    width: 100%;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.back-link { background: transparent; border: none; color: #64748b; font-weight: 600; cursor: pointer; }
.category-step-label { font-weight: 700; color: #1e293b; }

.category-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    width: 100%;
}
.cat-emoji { font-size: 32px; }

/* Quiz Styles */
.quiz-flow { width: 100%; max-width: 600px; }
.count-options { display: flex; gap: 12px; margin-top: 20px; justify-content: center; }
.count-btn { padding: 12px 24px; border-radius: 12px; background: #2563eb; color: white; border: none; font-weight: 700; cursor: pointer; }

.quiz-card { background: white; border-radius: 20px; padding: 32px; box-shadow: 0 10px 30px rgba(0,0,0,0.04); }
.quiz-question { font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 24px; }
.quiz-options { display: flex; flex-direction: column; gap:12px; }
.opt-btn { 
    display: flex; align-items: center; gap: 12px; padding: 16px; 
    border-radius: 12px; border: 1px solid #e2e8f0; background: #fff; text-align: left; cursor: pointer;
}
.opt-btn.selected { border-color: #2563eb; background: #eff6ff; }
.opt-btn.correct { border-color: #10b981; background: #ecfdf5; color: #059669; }
.opt-btn.wrong { border-color: #ef4444; background: #fef2f2; color: #dc2626; }

.quiz-result-card { text-align: center; padding: 48px; background: white; border-radius: 24px; }
.trophy-icon { color: #eab308; margin-bottom: 24px; }
.result-stats { display: flex; gap: 40px; justify-content: center; margin: 32px 0; }

@media screen and (max-width: 640px) {
    .coach-gates, .category-grid { grid-template-columns: 1fr; flex-direction: column; }
}
</style>
