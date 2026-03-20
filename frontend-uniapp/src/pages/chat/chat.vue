<template>
	<view :class="['app-layout', `${currentMode}-mode`]">
		<view v-if="isSidebarOpen" class="sidebar-overlay show" @tap="isSidebarOpen = false"></view>

		<view :class="['sidebar', 'glass-panel', { show: isSidebarOpen }]">
			<view class="sidebar-header">
				<button class="new-chat-btn" @tap="startNewChatWithClose">
					<text class="new-chat-plus">+</text>
					<text>新对话</text>
				</button>
			</view>

			<scroll-view scroll-y class="session-list">
				<view
					v-for="session in sessions"
					:key="session.id"
					:class="['session-item', 'session-item-shell', { active: session.id === currentSessionId }]"
					@tap="switchSessionWithClose(session.id)"
				>
					<text class="session-title">{{ session.title || '新对话' }}</text>
					<button class="delete-btn" @tap.stop="deleteSession(session.id)">×</button>
				</view>
			</scroll-view>

			<view class="sidebar-footer">
				<button class="sidebar-settings-btn" @tap="openSettings">⚙️ 设置</button>
				<button v-if="auth.isAdmin" class="sidebar-admin-btn" @tap="goToAdmin">管理后台</button>

				<view class="sidebar-user-info sidebar-account-card">
					<view class="user-avatar-sidebar">{{ userInitial }}</view>
					<view class="user-details">
						<text class="user-name-sidebar">{{ auth.userName }}</text>
						<button class="logout-link-sidebar" @tap="handleLogout">退出登录</button>
					</view>
				</view>
			</view>
		</view>

		<view class="chat-container">
			<view class="chat-nav nav-shell glass-panel">
				<view class="nav-left">
					<button class="nav-btn-hamburg" @tap="toggleSidebar">
						<text class="nav-btn-text">{{ isSidebarOpen ? '×' : '≡' }}</text>
					</button>
				</view>

				<view class="mode-selector mode-selector-pill">
					<view
						:class="['mode-tab', 'mode-btn', { active: currentMode === 'general', 'tab-active-general': currentMode === 'general' }]"
						@tap="switchMode('general')"
					>
						<text class="tab-text">全能助手</text>
					</view>
					<view class="tab-divider"></view>
					<view
						:class="['mode-tab', 'mode-btn', { active: currentMode === 'coach', 'tab-active-coach': currentMode === 'coach' }]"
						@tap="switchMode('coach')"
					>
						<text class="tab-text">知识教练</text>
					</view>
					<view class="tab-divider"></view>
					<view
						:class="['mode-tab', 'mode-btn', { active: currentMode === 'expert', 'tab-active-expert': currentMode === 'expert' }]"
						@tap="switchMode('expert')"
					>
						<text class="tab-text">专家指导</text>
					</view>
				</view>
				<view class="nav-right-spacer"></view>
			</view>

			<view class="main-body-wrapper">
				<scroll-view
					scroll-y
					class="chat-main"
					:scroll-top="scrollTop"
					:scroll-into-view="scrollIntoViewTarget"
					scroll-with-animation
				>
					<view v-if="messages.length === 0" class="welcome-screen">
						<view class="welcome-stage">
						<view v-if="currentMode === 'general'" class="zen-welcome-stage">
								<view class="welcome-content welcome-panel welcome-centered">
									<view class="zen-avatar-breathe">
										<image :src="XIAOYI_AVATAR_SRC" mode="aspectFit" class="zen-avatar-img" />
									</view>
								<text class="zen-title">您好，我是小易</text>
								<text class="zen-subtitle">{{ welcomeMsg }}</text>

								<view class="suggestion-chips suggestion-chip-shell">
									<view class="zen-suggestion-grid">
										<button class="zen-card zen-card-button" @tap="presetMsg('我能帮你做哪些事情')">
											<view class="zen-card-content">
												<text class="zen-card-title">查看核心能力</text>
												<text class="zen-card-desc">了解我能帮您完成的物流与办公任务</text>
											</view>
										</button>
										<button class="zen-card zen-card-button" @tap="presetMsg('如何正确使用小易')">
											<view class="zen-card-content">
												<text class="zen-card-title">获取使用指南</text>
												<text class="zen-card-desc">掌握与小易合作的最佳提示词技巧</text>
											</view>
										</button>
									</view>
								</view>
							</view>
						</view>

						<view v-else-if="currentMode === 'expert'" class="zen-welcome-stage expert-stage welcome-centered mode-stage-offset">
							<view class="zen-expert-icon">
								<text class="expert-emoji">💡</text>
							</view>
							<text class="zen-title zen-title-expert">专家指导</text>
							<text class="zen-subtitle">请描述您遇到的模糊或复杂的问题，我会通过 1-2 轮追问帮你理清思路并提供专业建议。</text>

						</view>

						<view v-else-if="isCoachQuizActive" class="coach-quiz-stage">
							<!-- 移动端总结卡片 -->
							<view v-if="coachQuizSession?.completed" class="coach-quiz-card coach-quiz-summary-premium glass-panel">
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
										<text class="score-val">{{ coachQuizAccuracy }}%</text>
										<text class="score-lab">正确率</text>
									</view>
								</view>
								<text class="summary-note">坚持每日训练，是通往业务专家的必经之路。</text>
								<view class="premium-actions-stack">
									<button class="quiz-primary-stack-btn" @tap="restartCoachQuiz">重新发起训练</button>
									<button class="quiz-ghost-stack-btn" @tap="coachEntryMode = 'menu'; restartCoachQuiz()">返回教练菜单</button>
								</view>
							</view>

							<!-- 移动端答题卡片 -->
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
										:class="coachQuizOptionClass(option.key)"
										:disabled="Boolean(currentCoachQuizQuestion.selectedAnswer)"
										@tap="selectCoachQuizAnswer(option.key)"
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
									<button class="quiz-btn-nav ghost" @tap="restartCoachQuiz">重试</button>
									<button class="quiz-btn-nav primary" :disabled="!currentCoachQuizQuestion.selectedAnswer" @tap="nextCoachQuizQuestion">
										<text>{{ coachQuizSession.currentIndex === coachQuizSession.questions.length - 1 ? '查看总结' : '下一题' }}</text>
										<text class="ico-next">→</text>
									</button>
								</view>
							</view>
						</view>

						<view v-else class="zen-welcome-stage coach-stage welcome-centered mode-stage-offset">
							<text class="zen-title zen-title-coach">知识教练</text>
							<text class="zen-subtitle">场景化陪练，帮助你把经验真正练到手。</text>

							<view v-if="coachEntryMode === 'menu'" class="coach-entry-grid">
								<button class="zen-level-card zen-level-card-button coach-entry-card" @tap="enterCoachDuelMode">
									<view class="zen-card-huge-emoji">🎯</view>
									<view class="zen-level-info">
										<text class="zen-level-title">教练对练</text>
										<text class="zen-level-desc-mini">继续使用原来的场景陪练流程，适合练报价、排雷、纠纷和逼单节奏。</text>
									</view>
								</button>
								<button class="zen-level-card zen-level-card-button coach-entry-card" @tap="enterCoachQuizMode">
									<view class="zen-card-huge-emoji">📝</view>
									<view class="zen-level-info">
										<text class="zen-level-title">教练出题</text>
										<text class="zen-level-desc-mini">选择 5 / 10 / 20 题进入单题卡片流，答完立刻反馈结果。</text>
									</view>
								</button>
							</view>

							<view v-else-if="coachEntryMode === 'quiz'" class="coach-quiz-picker-premium glass-panel">
								<button class="picker-back-btn" @tap="coachEntryMode = 'menu'; restartCoachQuiz()">
									<text class="ico-back">←</text> 返回
								</button>
								<view class="picker-title-pnl">
									<text class="p-title">题目数量</text>
									<text class="p-subtitle">点击下方选项即可立即开始训练</text>
								</view>
								<view class="count-grid-modern">
									<button v-for="count in coachQuizQuestionCounts" :key="count" class="count-card-item" :disabled="coachQuizLoading" @tap="startCoachQuizSession(count)">
										<text class="c-num">{{ count }}</text>
										<text class="c-unit">道题</text>
									</button>
								</view>
								<view v-if="coachQuizLoading" class="picker-status-box">
									<text class="shimmer-text">正在为您精心抽题...</text>
								</view>
								<text v-else-if="coachQuizError" class="picker-status-box error">{{ coachQuizError }}</text>
							</view>

							<view v-else class="coach-selection-shell">
								<view class="zen-level-up-container">
									<view class="zen-level-header">
										<text class="coach-step-pill">{{ currentCoachStep }}</text>
										<text class="zen-level-desc" v-if="!selectedRegion">先选择实战航线</text>
										<text class="zen-level-desc" v-else-if="!selectedPersona">再选择客户画像</text>
										<text class="zen-level-desc" v-else>最后选择训练科目</text>
									</view>

									<view v-if="currentCoachSelections.length" class="coach-selection-summary">
										<view class="zen-breadcrumbs">
											<button class="zen-breadcrumb coach-selection-chip coach-selection-chip-button" @tap="selectedRegion = null; selectedPersona = null">
												{{ selectedRegion }}
												<text v-if="selectedPersona" class="arrow">→</text>
											</button>
											<button v-if="selectedPersona" class="zen-breadcrumb coach-selection-chip coach-selection-chip-button" @tap="selectedPersona = null">
												{{ selectedPersona }}
											</button>
										</view>
									</view>

									<view v-if="!selectedRegion" class="zen-level-grid">
										<button v-for="reg in coachRegions" :key="reg.name" class="zen-level-card zen-level-card-button" @tap="selectedRegion = reg.name">
											<view class="zen-card-huge-icon">{{ reg.short }}</view>
											<view class="zen-level-info">
												<text class="zen-level-title">{{ reg.name }}</text>
												<text class="zen-level-desc-mini">{{ reg.desc }}</text>
											</view>
										</button>
									</view>

									<view v-else-if="!selectedPersona" class="zen-level-grid slide-in">
										<button v-for="persona in coachPersonas" :key="persona.name" class="zen-level-card zen-level-card-button" @tap="selectedPersona = persona.name">
											<view class="zen-card-huge-emoji">{{ persona.emoji }}</view>
											<view class="zen-level-info">
												<text class="zen-level-title">{{ persona.name }}</text>
												<text class="zen-level-desc-mini">{{ persona.desc }}</text>
											</view>
										</button>
									</view>

									<view v-else class="zen-level-grid slide-in">
										<button v-for="subject in coachSubjects" :key="subject.name" class="zen-level-card zen-level-card-button" @tap="startRandomCoachDetailed(subject.name)">
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
					</view>

					<view class="message-list">
						<view v-for="msg in messages" :key="msg.id" class="message-wrapper" :class="msg.role">
							<view class="avatar">
								<image v-if="msg.role === 'assistant'" :src="XIAOYI_AVATAR_SRC" class="xiaoyi-avatar" />
								<view v-else class="user-avatar">{{ userInitial }}</view>
							</view>

							<view class="message-body message-content" :class="{ 'is-typing': msg.isTyping }">
								<image
									v-if="msg.image"
									:src="msg.image"
									mode="widthFix"
									class="chat-message-image"
									@tap="previewImage(msg.image)"
								/>
								<!-- #ifdef MP-WEIXIN -->
								<view class="mp-message-rich">
									<view
										v-for="(block, blockIndex) in renderMpMessageBlocks(msg.content)"
										:key="`${msg.id}-${blockIndex}`"
										class="mp-message-block"
										:class="`is-${block.type}`"
									>
										<view v-if="block.type === 'divider'" class="mp-message-divider"></view>
										<view v-else class="mp-message-line">
											<text v-if="block.prefix" class="mp-message-prefix">{{ block.prefix }}</text>
											<text class="mp-message-line-text">{{ block.text }}</text>
										</view>
									</view>
								</view>
								<!-- #endif -->
								<!-- #ifndef MP-WEIXIN -->
								<rich-text class="markdown-body" :nodes="renderMarkdown(msg.content)"></rich-text>
								<!-- #endif -->
								<text v-if="msg.isTyping" class="cursor-blink"></text>
							</view>
						</view>

						<view id="chat-bottom-anchor" class="chat-bottom-anchor"></view>
						<view class="message-tail-spacer"></view>
					</view>
				</scroll-view>

				<view :class="['combat-intel-panel', 'combat-intel-shell', 'glass-panel', { show: isIntelOpen }]">
					<view class="panel-header">
						<text>实战情报中心</text>
						<text class="panel-close" @tap="isIntelOpen = false">×</text>
					</view>
					<scroll-view scroll-y class="panel-content">
						<view class="intel-section">
							<text class="intel-label">当前场景</text>
							<text class="intel-text">{{ currentScenario ? currentScenario.name : '未开始' }}</text>
						</view>
						<view class="intel-section intel-section-highlight">
							<text class="intel-label">客户画像</text>
							<text class="intel-text">{{ selectedPersona || '待选择' }}</text>
						</view>
						<view class="intel-section">
							<text class="intel-label">过关要点</text>
							<view v-if="currentScenario && formatSuccessCriteria(currentScenario.success_criteria).length">
								<text
									v-for="(item, index) in formatSuccessCriteria(currentScenario.success_criteria)"
									:key="`${currentScenario.name}-${index}`"
									class="intel-text intel-text-block"
								>
									{{ index + 1 }}. {{ item }}
								</text>
							</view>
							<text v-else class="intel-text">先进入一个教练场景，情报会自动出现在这里。</text>
						</view>
						<button class="quit-combat-btn" @tap="requestCoachEvaluation">结束对练并点评</button>
					</scroll-view>
				</view>
			</view>

			<!-- #ifdef MP-WEIXIN -->
			<view v-if="!isCoachQuizView" class="mp-chat-footer">
				<view class="mp-composer-shell" :class="{ 'has-image': selectedImage, 'is-focused': isInputFocused }">
					<view v-if="selectedImage" class="zen-image-preview-area">
						<view class="image-preview-frame">
							<image :src="selectedImage" mode="aspectFill" class="zen-image-preview" @tap="previewImage(selectedImage)" />
						</view>
						<view class="image-preview-meta">
							<text class="image-preview-chip">已附图</text>
						</view>
						<view class="zen-remove-image-btn" @tap="removeImage">脳</view>
					</view>

					<view class="mp-composer-main">
						<view class="zen-upload-btn upload-pic-btn" :class="{ 'has-attachment': selectedImage }" @tap="triggerImageUpload">
							<text class="upload-pic-mark">+</text>
						</view>
						<input
							v-model="inputMsg"
							class="zen-input-box zen-input-box-mp mp-composer-input"
							:cursor-spacing="24"
							confirm-type="send"
							:placeholder="selectedImage ? '补充图片说明，或直接发送...' : '发送消息、粘贴或拖入图片...'"
							@input="handleComposerInput"
							@confirm="sendMessage"
							@focus="isInputFocused = true"
							@blur="isInputFocused = false"
						/>
						<button
							v-if="!isGenerating"
							class="zen-send-btn mp-send-btn"
							:class="{ active: canSendMessage }"
							:disabled="!canSendMessage"
							@tap="sendMessage"
						>
							<image class="icon-send-image" :src="SEND_ICON_SRC" mode="aspectFit" />
						</button>
						<button v-else class="zen-send-btn mp-send-btn stop" @tap="stopGeneration">
							<text class="icon-send">■</text>
						</button>
					</view>
				</view>

				<view v-if="selectedImage || isGenerating" class="composer-status-row">
					<text v-if="selectedImage" class="composer-status-chip image-ready">宸查檮鍔犲浘鐗囷紝鍙洿鎺ュ彂閫佹垨缁х画琛ュ厖鏂囧瓧</text>
					<text v-if="isGenerating" class="composer-status-chip generating">姝ｅ湪鐢熸垚鍥炲锛屽彲鐐瑰嚮鍋滄鎸夐挳涓柇</text>
				</view>
			</view>
			<!-- #endif -->

			<!-- #ifndef MP-WEIXIN -->
			<view v-if="!isCoachQuizView" class="zen-footer-wrapper chat-footer">
				<view class="input-shell input-container" :class="{ 'has-image': selectedImage, 'is-focused': isInputFocused }">
				<view class="zen-floating-pill" :class="{ 'has-image': selectedImage, 'is-focused': isInputFocused }">
					<view v-if="selectedImage" class="zen-image-preview-area">
						<view class="image-preview-frame">
							<image :src="selectedImage" mode="aspectFill" class="zen-image-preview" @tap="previewImage(selectedImage)" />
						</view>
						<view class="image-preview-meta">
							<text class="image-preview-chip">已附图</text>
						</view>
						<view class="zen-remove-image-btn" @tap="removeImage">×</view>
					</view>

					<view class="zen-input-row">
						<view class="zen-upload-btn upload-pic-btn" :class="{ 'has-attachment': selectedImage }" @tap="triggerImageUpload">
							<!-- color="selectedImage ? '#2563eb' : '#64748b'" -->
							<text class="upload-pic-mark">＋</text>
						</view>

						<input
							:value="inputMsg"
							class="zen-input-box zen-input-box-mp"
							:cursor-spacing="24"
							confirm-type="send"
							:placeholder="selectedImage ? '补充图片说明，或直接发送...' : '发送消息、粘贴或拖入图片...'"
							@input="handleComposerInput"
							@confirm="sendMessage"
							@focus="isInputFocused = true"
							@blur="isInputFocused = false"
						/>
						<textarea
							v-model="inputMsg"
							auto-height
							class="zen-input-box"
							:cursor-spacing="24"
							:show-confirm-bar="false"
							confirm-type="send"
							:placeholder="selectedImage ? '补充图片说明，或直接发送...' : '发送消息、粘贴或拖入图片...'"
							@input="handleComposerInput"
							@confirm="sendMessage"
							@focus="isInputFocused = true"
							@blur="isInputFocused = false"
						></textarea>

						<view class="zen-send-area">
							<button v-if="!isGenerating" class="zen-send-btn" :class="{ active: canSendMessage }" :disabled="!canSendMessage" @tap="sendMessage">
								<image class="icon-send-image" :src="SEND_ICON_SRC" mode="aspectFit" />
							</button>
							<button v-else class="zen-send-btn stop" @tap="stopGeneration">
								<text class="icon-send">■</text>
							</button>
						</view>
					</view>
				</view>
				</view>

				<view v-if="selectedImage || isGenerating" class="composer-status-row">
					<text v-if="selectedImage" class="composer-status-chip image-ready">已附加图片，可直接发送或继续补充文字</text>
					<text v-if="isGenerating" class="composer-status-chip generating">正在生成回复，可点击停止按钮中断</text>
				</view>
			</view>
			<!-- #endif -->
		</view>

		<view class="zen-bottom-nav">
			<view class="zen-nav-item" :class="{ active: currentTab === 'chat' }" @tap="switchTab('chat')">
				<view class="zen-nav-icon-wrapper">
					<view class="zen-nav-icon">
						<image class="zen-nav-icon-image" :class="{ active: currentTab === 'chat' }" :src="CHAT_NAV_ICON_SRC" mode="aspectFit" />
					</view>
				</view>
				<text class="zen-nav-label">对话</text>
			</view>

			<view class="zen-nav-item" :class="{ active: currentTab === 'notice' }" @tap="switchTab('notice')">
				<view class="zen-nav-icon-wrapper">
					<view class="zen-nav-icon">
						<image class="zen-nav-icon-image" :class="{ active: currentTab === 'notice' }" :src="NOTICE_NAV_ICON_SRC" mode="aspectFit" />
						<view v-if="hasUnreadNotices" class="zen-nav-badge"></view>
					</view>
				</view>
				<text class="zen-nav-label">通知</text>
			</view>

			<view class="zen-nav-item" :class="{ active: currentTab === 'tools' }" @tap="switchTab('tools')">
				<view class="zen-nav-icon-wrapper">
					<view class="zen-nav-icon">
						<image class="zen-nav-icon-image" :class="{ active: currentTab === 'tools' }" :src="TOOLS_NAV_ICON_SRC" mode="aspectFit" />
					</view>
				</view>
				<text class="zen-nav-label">工具</text>
			</view>

			<view class="zen-nav-item" :class="{ active: currentTab === 'admin' }" @tap="switchTab('admin')">
				<view class="zen-nav-icon-wrapper">
					<view class="zen-nav-icon">
						<image class="zen-nav-icon-image" :class="{ active: currentTab === 'admin' }" :src="ADMIN_NAV_ICON_SRC" mode="aspectFit" />
					</view>
				</view>
				<text class="zen-nav-label">管理</text>
			</view>
		</view>

		<view v-if="showSettings" class="settings-overlay" @tap="closeSettings">
			<view class="settings-sheet" @tap.stop>
				<view class="settings-sheet-header">
					<view>
						<text class="settings-sheet-title">用户设置</text>
						<text class="settings-sheet-desc">调整回复详略程度，并修改当前账号密码</text>
					</view>
					<text class="settings-sheet-close" @tap="closeSettings">×</text>
				</view>

				<view class="settings-section">
					<text class="settings-section-title">输出长度</text>
					<text class="settings-section-desc">控制小易每次回答内容的详尽程度</text>
					<view class="length-option-list">
						<button
							v-for="option in outputLengthOptions"
							:key="option.value"
							:class="['length-option-btn', { active: outputLength === option.value }]"
							@tap="setOutputLength(option.value)"
						>
							<view class="length-option-main">
								<text class="length-option-icon">{{ option.icon }}</text>
								<text class="length-option-label">{{ option.label }}</text>
							</view>
							<text class="length-option-desc">{{ option.desc }}</text>
						</button>
					</view>
				</view>

				<view class="settings-section">
					<text class="settings-section-title">修改密码</text>
					<text class="settings-section-desc">需要先验证当前密码，新密码至少 6 位</text>
					<input
						v-model="pwdForm.oldPwd"
						class="settings-input"
						type="password"
						password
						placeholder="当前密码"
					/>
					<input
						v-model="pwdForm.newPwd"
						class="settings-input"
						type="password"
						password
						placeholder="新密码（至少 6 位）"
					/>
					<input
						v-model="pwdForm.confirmPwd"
						class="settings-input"
						type="password"
						password
						placeholder="确认新密码"
					/>
					<button class="settings-submit-btn" :disabled="pwdLoading" @tap="submitChangePassword">
						{{ pwdLoading ? '提交中...' : '确认修改密码' }}
					</button>
				</view>
			</view>
		</view>

		<view v-if="showNoticeCenter" class="notice-center-overlay" @tap="closeNoticeCenter">
			<view class="notice-center-sheet" @tap.stop>
				<view class="notice-center-head">
					<text class="notice-center-title">重要通知</text>
					<text class="notice-center-close" @tap="closeNoticeCenter">×</text>
				</view>
				<view class="notice-center-tabs">
					<view class="notice-center-tab" :class="{ active: noticeTab === 'current' }" @tap="noticeTab = 'current'">
						<text>本周通知</text>
					</view>
					<view class="notice-center-tab" :class="{ active: noticeTab === 'history' }" @tap="noticeTab = 'history'">
						<text>历史通知</text>
					</view>
				</view>
				<scroll-view scroll-y class="notice-center-scroll">
					<view v-if="noticesLoading" class="notice-center-empty">通知加载中…</view>
					<view v-else-if="displayNotices.length === 0" class="notice-center-empty">
						{{ noticeTab === 'current' ? '本周暂无通知' : '暂无历史通知' }}
					</view>
					<view v-for="notice in displayNotices" :key="notice.id" class="notice-center-card" @tap="previewNotice(notice)">
						<text class="notice-center-date">{{ formatNoticeDate(notice.created_at) }}</text>
						<text class="notice-center-content">{{ notice.content }}</text>
					</view>
				</scroll-view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useAuthStore } from '@/store/auth'
import { renderMarkdown } from '@/utils/markdown'
import { resolveApiUrl } from '@/utils/api'
import { buildImageDataUrl } from '@/utils/image-data-url'
import { validateMpImageSelection } from '@/utils/image-data-url'
import { uploadChatImage } from '@/utils/chat-image-upload'
import { captureClientEvent } from '@/utils/error-logger'
import { createMpStreamChatController } from '@/utils/mp-stream-chat'

const auth = useAuthStore()
const XIAOYI_AVATAR_SRC = '/static/xiaoyi_character.png'
const CHAT_NAV_ICON_SRC = '/static/nav_chat.png'
const NOTICE_NAV_ICON_SRC = '/static/nav_notice.png'
const TOOLS_NAV_ICON_SRC = '/static/nav_tools.png'
const ADMIN_NAV_ICON_SRC = '/static/nav_admin.png'
const SEND_ICON_SRC = '/static/send.png'
const NOTICE_SEEN_STORAGE_KEY = 'zyd_notice_last_seen_id'

const messages = ref([])
const inputMsg = ref('')
const isInputFocused = ref(false)
const isGenerating = ref(false)
const isSidebarOpen = ref(false)
const welcomeMsg = ref('您的全天候智能助手')
const currentMode = ref('general')
const sessions = ref([])
const currentSessionId = ref(null)
const selectedImage = ref(null)
const selectedImageUploadId = ref('')
const isImageUploading = ref(false)
const currentTab = ref('chat')
const scrollTop = ref(0)
const scrollIntoViewTarget = ref('')
const coachCases = ref([])
const currentScenario = ref(null)
const isIntelOpen = ref(false)
const selectedRegion = ref(null)
const selectedPersona = ref(null)
const coachEntryMode = ref('menu')
const coachQuizQuestionCounts = [5, 10, 20]
const coachQuizSession = ref(null)
const coachQuizLoading = ref(false)
const coachQuizError = ref('')
const showNoticeCenter = ref(false)
const noticeTab = ref('current')
const currentNotices = ref([])
const noticeHistory = ref([])
const noticesLoading = ref(false)
const hasUnreadNotices = ref(false)
const showSettings = ref(false)

const POST_LOGIN_FRESH_CHAT_KEY = 'zyd_post_login_fresh_chat'
const LAST_CHAT_MODE_KEY = 'zyd_last_chat_mode'
const OUTPUT_LENGTH_KEY = 'zyd_output_length'
const outputLengthOptions = [
	{ value: 'short', icon: '⚡', label: '简洁', desc: '精炼核心要点，适合快速查询' },
	{ value: 'medium', icon: '📋', label: '标准', desc: '均衡详细，适合日常对话' },
	{ value: 'long', icon: '📄', label: '详细', desc: '完整展开，适合复杂分析' },
]
const outputLength = ref(uni.getStorageSync(OUTPUT_LENGTH_KEY) || 'medium')
const pwdForm = ref({ oldPwd: '', newPwd: '', confirmPwd: '' })
const pwdLoading = ref(false)

const coachRegions = [
	{ name: '美国线', short: 'US', desc: '重视海派、邮编偏远、计费重量规则。' },
	{ name: '欧洲线', short: 'EU', desc: '重视铁派、VAT 税号、清关和派送规则。' },
]

const coachPersonas = [
	{ name: '行业小白', emoji: '🙂', desc: '礼貌但不懂行，需要你用专业和耐心带着走。' },
	{ name: '江湖老手', emoji: '😏', desc: '话术老练、压价明显，更考验底盘和判断。' },
]

const coachSubjects = [
	{ name: '报价拉锯战', emoji: '💵', desc: '面对客户反复压价，如何守住利润空间。' },
	{ name: '异常纠纷处理', emoji: '🛡', desc: '处理查验、投诉、破损和延误等异常问题。' },
	{ name: '业务排雷', emoji: '🔎', desc: '识别隐藏风险、敏感货和信息不完整订单。' },
	{ name: '逼单与维护', emoji: '🤝', desc: '推进成交，同时维持客户信任与节奏。' },
]

const userInitial = computed(() => String(auth.userName || '易').trim().slice(0, 1).toUpperCase() || '易')
const canSendMessage = computed(() => Boolean(inputMsg.value.trim() || selectedImage.value))
const displayNotices = computed(() => (noticeTab.value === 'history' ? noticeHistory.value : currentNotices.value))
const isCoachQuizActive = computed(() => currentMode.value === 'coach' && Boolean(coachQuizSession.value))
const isCoachQuizView = computed(() => currentMode.value === 'coach' && coachEntryMode.value === 'quiz')
const currentCoachQuizQuestion = computed(() => {
	if (!coachQuizSession.value || coachQuizSession.value.completed) return null
	return coachQuizSession.value.questions[coachQuizSession.value.currentIndex] || null
})
const coachQuizAccuracy = computed(() => {
	if (!coachQuizSession.value || coachQuizSession.value.questions.length === 0) return 0
	return Math.round((coachQuizSession.value.correctCount / coachQuizSession.value.questions.length) * 100)
})

const currentBrandMode = computed(() => {
	const modeMeta = {
		general: { label: '全能助手' },
		coach: { label: '实战教练' },
		expert: { label: '专家指导' },
	}
	return modeMeta[currentMode.value] || modeMeta.general
})

const currentCoachSelections = computed(() => {
	return [selectedRegion.value, selectedPersona.value].filter(Boolean)
})

const currentCoachStep = computed(() => {
	if (!selectedRegion.value) return '第一步 · 选择实战航线'
	if (!selectedPersona.value) return '第二步 · 选择客户背景'
	return '第三步 · 选择练习科目'
})

const openSettings = () => {
	showSettings.value = true
	isSidebarOpen.value = false
}

const closeSettings = () => {
	showSettings.value = false
	pwdForm.value = { oldPwd: '', newPwd: '', confirmPwd: '' }
	pwdLoading.value = false
}

const setOutputLength = (value) => {
	outputLength.value = value
	uni.setStorageSync(OUTPUT_LENGTH_KEY, value)
	uni.showToast({ title: '输出偏好已保存', icon: 'none' })
}

const buildMessageWithOutputPreference = (content) => {
	if (!content) {
		return content
	}
	if (outputLength.value === 'short') {
		return `[输出偏好:极致精简] ${content}`
	}
	if (outputLength.value === 'long') {
		return `[输出偏好:详尽展开] ${content}`
	}
	return content
}

const submitChangePassword = async () => {
	const { oldPwd, newPwd, confirmPwd } = pwdForm.value
	if (!oldPwd || !newPwd || !confirmPwd) {
		uni.showToast({ title: '请填写完整密码信息', icon: 'none' })
		return
	}
	if (newPwd.length < 6) {
		uni.showToast({ title: '新密码至少 6 位', icon: 'none' })
		return
	}
	if (newPwd !== confirmPwd) {
		uni.showToast({ title: '两次输入的新密码不一致', icon: 'none' })
		return
	}

	pwdLoading.value = true
	const result = await auth.changePassword(oldPwd, newPwd)
	pwdLoading.value = false

	if (result?.success) {
		uni.showToast({ title: '密码修改成功', icon: 'success' })
		closeSettings()
		return
	}

	uni.showToast({ title: result?.message || '修改失败，请重试', icon: 'none' })
}

const persistLastMode = (mode) => {
	try {
		uni.setStorageSync(LAST_CHAT_MODE_KEY, mode)
	} catch (error) {}
}

const getInitialChatMode = () => {
	try {
		return uni.getStorageSync(LAST_CHAT_MODE_KEY) || 'general'
	} catch (error) {
		return 'general'
	}
}

const formatSuccessCriteria = (criteria) => {
	if (Array.isArray(criteria)) return criteria
	if (typeof criteria === 'string') {
		return criteria.split('\n').map((item) => item.trim()).filter(Boolean)
	}
	return []
}

const sanitizeMpInlineText = (text) => {
	return String(text || '')
		.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1')
		.replace(/\*\*(.*?)\*\*/g, '$1')
		.replace(/__(.*?)__/g, '$1')
		.replace(/~~(.*?)~~/g, '$1')
		.replace(/`([^`]+)`/g, '$1')
		.replace(/\s+/g, ' ')
		.trim()
}

const flushMpParagraph = (blocks, paragraphLines) => {
	if (paragraphLines.length === 0) return
	const text = sanitizeMpInlineText(paragraphLines.join('\n'))
	if (text) {
		blocks.push({
			type: 'paragraph',
			text,
			prefix: '',
		})
	}
	paragraphLines.length = 0
}

const renderMpMessageBlocks = (content) => {
	const lines = String(content || '').replace(/\r\n/g, '\n').split('\n')
	const blocks = []
	const paragraphLines = []

	for (const rawLine of lines) {
		const line = rawLine.trim()

		if (!line) {
			flushMpParagraph(blocks, paragraphLines)
			continue
		}

		if (/^([-*_])\1{2,}$/.test(line)) {
			flushMpParagraph(blocks, paragraphLines)
			blocks.push({ type: 'divider', text: '', prefix: '' })
			continue
		}

		const headingMatch = line.match(/^#{1,6}\s+(.+)$/)
		if (headingMatch) {
			flushMpParagraph(blocks, paragraphLines)
			blocks.push({
				type: 'heading',
				text: sanitizeMpInlineText(headingMatch[1]),
				prefix: '',
			})
			continue
		}

		const orderedMatch = line.match(/^(\d+)\.\s+(.+)$/)
		if (orderedMatch) {
			flushMpParagraph(blocks, paragraphLines)
			blocks.push({
				type: 'ordered-item',
				text: sanitizeMpInlineText(orderedMatch[2]),
				prefix: `${orderedMatch[1]}.`,
			})
			continue
		}

		const bulletMatch = line.match(/^[-*+]\s+(.+)$/)
		if (bulletMatch) {
			flushMpParagraph(blocks, paragraphLines)
			blocks.push({
				type: 'bullet-item',
				text: sanitizeMpInlineText(bulletMatch[1]),
				prefix: '•',
			})
			continue
		}

		paragraphLines.push(rawLine)
	}

	flushMpParagraph(blocks, paragraphLines)

	if (blocks.length === 0) {
		const fallbackText = sanitizeMpInlineText(content)
		return fallbackText
			? [{ type: 'paragraph', text: fallbackText, prefix: '' }]
			: []
	}

	return blocks
}

const readSeenNoticeId = () => {
	try {
		return Number(uni.getStorageSync(NOTICE_SEEN_STORAGE_KEY) || 0)
	} catch (error) {
		return 0
	}
}

const writeSeenNoticeId = (noticeId) => {
	try {
		uni.setStorageSync(NOTICE_SEEN_STORAGE_KEY, String(noticeId || 0))
	} catch (error) {}
}

const syncUnreadNoticeState = (notices) => {
	const latestId = Array.isArray(notices) && notices.length > 0 ? Number(notices[0].id || 0) : 0
	const seenId = readSeenNoticeId()
	hasUnreadNotices.value = latestId > seenId
}

const formatNoticeDate = (value) => {
	if (!value) return ''
	const date = new Date(value)
	if (Number.isNaN(date.getTime())) return String(value)
	const year = date.getFullYear()
	const month = `${date.getMonth() + 1}`.padStart(2, '0')
	const day = `${date.getDate()}`.padStart(2, '0')
	const hours = `${date.getHours()}`.padStart(2, '0')
	const minutes = `${date.getMinutes()}`.padStart(2, '0')
	return `${year}-${month}-${day} ${hours}:${minutes}`
}

const requestNoticeApi = async (path) => {
	return await new Promise((resolve, reject) => {
		uni.request({
			url: resolveApiUrl(path),
			method: 'GET',
			header: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					resolve(Array.isArray(res.data) ? res.data : [])
					return
				}
				reject(new Error(res.data?.detail || `notice request failed (${res.statusCode})`))
			},
			fail: reject,
		})
	})
}

const fetchCurrentNotices = async ({ markAsRead = false } = {}) => {
	try {
		const notices = await requestNoticeApi('/api/notices/current')
		currentNotices.value = notices
		syncUnreadNoticeState(notices)
		if (markAsRead && notices.length > 0) {
			writeSeenNoticeId(notices[0].id)
			hasUnreadNotices.value = false
		}
	} catch (error) {
		currentNotices.value = []
		hasUnreadNotices.value = false
	}
}

const fetchNoticeHistory = async () => {
	try {
		const notices = await requestNoticeApi('/api/notices/history')
		noticeHistory.value = notices
	} catch (error) {
		noticeHistory.value = []
	}
}

const openNoticeCenter = async () => {
	currentTab.value = 'notice'
	showNoticeCenter.value = true
	noticeTab.value = 'current'
	noticesLoading.value = true
	try {
		await Promise.all([
			fetchCurrentNotices({ markAsRead: true }),
			fetchNoticeHistory(),
		])
	} finally {
		noticesLoading.value = false
	}
}

const closeNoticeCenter = () => {
	showNoticeCenter.value = false
	if (currentTab.value === 'notice') {
		currentTab.value = 'chat'
	}
}

const previewNotice = (notice) => {
	if (!notice?.content) return
	uni.showModal({
		title: formatNoticeDate(notice.created_at) || '通知详情',
		content: notice.content,
		showCancel: false,
	})
}

let requestTask = null
let scrollBottomTimer = null

const toggleSidebar = () => {
	isSidebarOpen.value = !isSidebarOpen.value
}

const clearSelectedImage = () => {
	selectedImage.value = null
	selectedImageUploadId.value = ''
	isImageUploading.value = false
}

const switchTab = (tab) => {
	if (tab === 'notice') {
		openNoticeCenter()
		return
	}

	if (tab === 'tools') {
		uni.showToast({ title: '工具中心开发中', icon: 'none' })
		return
	}

	currentTab.value = tab
	showNoticeCenter.value = false
	if (tab === 'admin') {
		isSidebarOpen.value = false
		uni.navigateTo({ url: '/pages/admin/admin' })
	}
}

const switchSession = (sessionId) => {
	const targetSession = sessions.value.find((session) => session.id === sessionId)
	if (!targetSession) return
	currentSessionId.value = sessionId
	messages.value = [...(targetSession.messages || [])]
	clearSelectedImage()
	scrollToBottom()
}

const switchSessionWithClose = (sessionId) => {
	switchSession(sessionId)
	isSidebarOpen.value = false
}

const saveSessions = () => {
	if (!currentSessionId.value) return

	const targetSession = sessions.value.find((session) => session.id === currentSessionId.value)
	if (!targetSession) return

	targetSession.messages = [...messages.value]
	const firstUserMessage = targetSession.messages.find((item) => item.role === 'user' && item.content)
	if (firstUserMessage) {
		const compactTitle = firstUserMessage.content.trim()
		targetSession.title = compactTitle.length > 16 ? `${compactTitle.slice(0, 16)}...` : compactTitle
	}

	try {
		uni.setStorageSync(`zyd_sessions_${currentMode.value}`, JSON.stringify(sessions.value.slice(0, 20)))
	} catch (error) {}
}

const startNewChat = ({ forceCreate = false } = {}) => {
	if (currentMode.value === 'coach') {
		resetCoachState()
	}
	if (!forceCreate && currentSessionId.value) {
		const currentSession = sessions.value.find((item) => item.id === currentSessionId.value)
		if (currentSession && (!currentSession.messages || currentSession.messages.length === 0)) {
			messages.value = []
			inputMsg.value = ''
			clearSelectedImage()
			return
		}
	}

	const newSessionId = `${Date.now()}`
	sessions.value = [
		{
			id: newSessionId,
			title: '新对话',
			messages: [],
		},
		...sessions.value,
	].slice(0, 20)

	currentSessionId.value = newSessionId
	messages.value = []
	inputMsg.value = ''
	clearSelectedImage()
	saveSessions()
}

const startNewChatWithClose = () => {
	startNewChat({ forceCreate: true })
	isSidebarOpen.value = false
}

const deleteSession = (sessionId) => {
	sessions.value = sessions.value.filter((item) => item.id !== sessionId)
	if (currentSessionId.value === sessionId) {
		if (sessions.value[0]) {
			switchSession(sessions.value[0].id)
		} else {
			startNewChat({ forceCreate: true })
		}
	}
	saveSessions()
}

const scrollToBottom = () => {
	nextTick(() => {
		scrollIntoViewTarget.value = ''
		scrollTop.value += 1000
		if (scrollBottomTimer) {
			clearTimeout(scrollBottomTimer)
		}
		scrollBottomTimer = setTimeout(() => {
			scrollIntoViewTarget.value = 'chat-bottom-anchor'
			scrollTop.value += 1
			scrollBottomTimer = null
		}, 80)
	})
}

const appendAssistantPlaceholder = () => {
	const aiMsgId = `ai-${Date.now()}`
	messages.value.push({
		id: aiMsgId,
		role: 'assistant',
		content: '',
		isTyping: true,
	})
	return aiMsgId
}

const handleComposerInput = (event) => {
	inputMsg.value = event?.detail?.value || ''
	console.info('[chat-debug] input', {
		value: inputMsg.value,
		length: inputMsg.value.length,
	})
}

const sendMessage = async () => {
	const content = inputMsg.value.trim()
	const messageWithPreference = buildMessageWithOutputPreference(content)
	console.info('[chat-debug] send-attempt', {
		content,
		raw: inputMsg.value,
		hasImage: Boolean(selectedImage.value),
		isGenerating: isGenerating.value,
	})
	if (!content && !selectedImage.value) return
	if (isGenerating.value) return

	if (selectedImage.value && isImageUploading.value) {
		uni.showToast({ title: '图片仍在上传中', icon: 'none' })
		return
	}

	const currentImageUploadId = selectedImageUploadId.value || null
	const currentImageBase64 = selectedImage.value && selectedImage.value.startsWith('data:')
		? selectedImage.value.split(',')[1]
		: null

	messages.value.push({
		id: `user-${Date.now()}`,
		role: 'user',
		content,
		image: selectedImage.value,
	})
	console.info('[chat-debug] user-message-pushed', {
		messagesLength: messages.value.length,
		currentSessionId: currentSessionId.value,
		lastRoles: messages.value.slice(-3).map((item) => item.role),
	})

	inputMsg.value = ''
	clearSelectedImage()
	isGenerating.value = true
	const aiMsgId = appendAssistantPlaceholder()
	console.info('[chat-debug] assistant-placeholder-pushed', {
		aiMsgId,
		messagesLength: messages.value.length,
	})
	scrollToBottom()

	const streamLogContext = {
		mode: currentMode.value,
		session_id: currentSessionId.value,
		has_image: Boolean(currentImageUploadId || currentImageBase64),
	}

	requestTask = createMpStreamChatController({
		buildRequestOptions: () => ({
			url: '/api/chat/stream',
			method: 'POST',
			header: {
				Authorization: `Bearer ${auth.token}`,
				'content-type': 'application/json',
			},
			data: {
				message: messageWithPreference,
				mode: currentMode.value,
				image_upload_id: currentImageUploadId,
				image_base64: currentImageBase64,
				history: messages.value.slice(0, -2).map((item) => ({
					role: item.role,
					content: item.content,
				})),
			},
		}),
		chunkTimeoutMs: 20000,
		retryLimit: 1,
		onRetry: ({ attempt, error }) => {
			captureClientEvent({
				level: 'warn',
				type: 'chat-stream-retry',
				message: error?.message || 'stream retry',
				context: { ...streamLogContext, attempt },
			})
		},
	})

	try {
		await requestTask.start({
			onStatus: (statusCode) => {
				console.info('[chat-debug] stream-status', { statusCode })
				if (statusCode >= 400) {
					const aiMsg = messages.value.find((item) => item.id === aiMsgId)
					if (aiMsg && !aiMsg.content) {
						aiMsg.content = `请求失败 (${statusCode})，请检查登录状态和后端服务。`
					}
				}
			},
			onText: (text) => {
				console.info('[chat-debug] stream-text', {
					length: text?.length || 0,
					preview: text?.slice?.(0, 60) || '',
				})
				const aiMsg = messages.value.find((item) => item.id === aiMsgId)
				if (aiMsg && text) {
					aiMsg.content += text
					scrollToBottom()
				}
			},
		})
	} catch (error) {
		console.error('[chat-debug] stream-error', {
			code: error?.code,
			message: error?.message,
			cause: error?.cause?.errMsg || error?.cause?.message || '',
		})
		const aiMsg = messages.value.find((item) => item.id === aiMsgId)
		if (aiMsg) {
			if (error?.code === 'STREAM_ABORTED') {
				aiMsg.content += '\n\n[已停止生成]'
			} else if (error?.code === 'STREAM_TIMEOUT') {
				captureClientEvent({
					level: 'warn',
					type: 'chat-stream-timeout',
					message: error?.message || 'stream timed out',
					context: streamLogContext,
				})
				aiMsg.content = aiMsg.content || '响应超时，请稍后重试。'
			} else if (!aiMsg.content) {
				aiMsg.content = `请求失败：${error?.message || '网络异常'}`
			}
		}

		captureClientEvent({
			level: 'error',
			type: 'chat-stream-failure',
			message: error?.message || 'chat stream failed',
			context: { ...streamLogContext, code: error?.code || 'REQUEST_FAILED' },
		})
	} finally {
		const aiMsg = messages.value.find((item) => item.id === aiMsgId)
		if (aiMsg) aiMsg.isTyping = false
		isGenerating.value = false
		requestTask = null
		console.info('[chat-debug] send-finished', {
			messagesLength: messages.value.length,
			lastMessageRole: messages.value[messages.value.length - 1]?.role || '',
			lastMessagePreview: messages.value[messages.value.length - 1]?.content?.slice?.(0, 60) || '',
		})
		saveSessions()
	}
}

const stopGeneration = () => {
	if (requestTask) {
		requestTask.abort()
	}
	isGenerating.value = false
}

const loadSessionsByMode = (mode) => {
	try {
		const raw = uni.getStorageSync(`zyd_sessions_${mode}`)
		sessions.value = raw ? JSON.parse(raw) : []
	} catch (error) {
		sessions.value = []
	}
}

const switchMode = (mode) => {
	if (currentMode.value === mode) return
	currentMode.value = mode
	persistLastMode(mode)
	resetCoachState()
	isSidebarOpen.value = false
	isIntelOpen.value = false
	selectedRegion.value = null
	selectedPersona.value = null
	if (mode !== 'coach') {
		currentScenario.value = null
	}
	loadSessionsByMode(mode)
	if (sessions.value.length === 0) {
		startNewChat({ forceCreate: true })
		return
	}
	switchSession(sessions.value[0].id)
}

const matchesCoachSubject = (category, subjectName) => {
	if (!category || !subjectName) return false
	const map = {
		'报价拉锯战': ['报价', '比价', '拉锯'],
		'异常纠纷处理': ['纠纷', '异常', '投诉', '处理'],
		业务排雷: ['排雷', '风险', '敏感', '异常'],
		'逼单与维护': ['逼单', '维护', '转化', '成交'],
	}
	if (category.includes(subjectName)) return true
	return (map[subjectName] || []).some((keyword) => category.includes(keyword))
}

const buildCoachFallbackScenario = (subjectName) => ({
	name: `${selectedRegion.value} · ${selectedPersona.value} · ${subjectName}`,
	success_criteria: [
		'识别客户真实诉求与隐藏顾虑',
		'给出专业且有利润空间的回应',
		'推动下一步成交或锁定关键参数',
	],
})

const resetCoachQuiz = () => {
	coachQuizSession.value = null
	coachQuizLoading.value = false
	coachQuizError.value = ''
}

const resetCoachState = () => {
	currentScenario.value = null
	isIntelOpen.value = false
	selectedRegion.value = null
	selectedPersona.value = null
	coachEntryMode.value = 'menu'
	resetCoachQuiz()
}

const enterCoachDuelMode = () => {
	resetCoachQuiz()
	coachEntryMode.value = 'duel'
}

const enterCoachQuizMode = () => {
	currentScenario.value = null
	isIntelOpen.value = false
	selectedRegion.value = null
	selectedPersona.value = null
	coachEntryMode.value = 'quiz'
	resetCoachQuiz()
}

const startCoachQuizSession = async (count) => {
	coachQuizLoading.value = true
	coachQuizError.value = ''
	coachQuizSession.value = null
	try {
		const response = await new Promise((resolve, reject) => {
			uni.request({
				url: resolveApiUrl(`/api/coach-quiz/session?count=${count}`),
				method: 'GET',
				header: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
				success: resolve,
				fail: reject,
			})
		})

		if (response.statusCode >= 400) {
			throw new Error(response.data?.detail || `coach quiz request failed: ${response.statusCode}`)
		}

		const questions = Array.isArray(response.data?.questions) ? response.data.questions : []
		if (questions.length === 0) {
			coachQuizError.value = '当前还没有可用题库，请先让管理员上传题目。'
			return
		}

		coachQuizSession.value = {
			requestedCount: count,
			currentIndex: 0,
			correctCount: 0,
			completed: false,
			questions: questions.map((question) => ({
				...question,
				selectedAnswer: '',
				isCorrect: false,
			})),
		}
	} catch (error) {
		coachQuizError.value = error.message || '抽题失败，请稍后重试'
	} finally {
		coachQuizLoading.value = false
	}
}

const selectCoachQuizAnswer = (answerKey) => {
	const question = currentCoachQuizQuestion.value
	if (!question || question.selectedAnswer) return
	question.selectedAnswer = answerKey
	question.isCorrect = question.answer === answerKey
	if (question.isCorrect) {
		coachQuizSession.value.correctCount += 1
	}
}

const nextCoachQuizQuestion = () => {
	if (!coachQuizSession.value || !currentCoachQuizQuestion.value?.selectedAnswer) return
	if (coachQuizSession.value.currentIndex >= coachQuizSession.value.questions.length - 1) {
		coachQuizSession.value.completed = true
		return
	}
	coachQuizSession.value.currentIndex += 1
}

const restartCoachQuiz = () => {
	resetCoachQuiz()
	coachEntryMode.value = 'quiz'
}

const coachQuizOptionClass = (optionKey) => {
	const question = currentCoachQuizQuestion.value
	if (!question?.selectedAnswer) return ''
	if (question.answer === optionKey) return 'correct'
	if (question.selectedAnswer === optionKey) return 'wrong'
	return ''
}

const startRandomCoachDetailed = (subjectName) => {
	if (!selectedRegion.value || !selectedPersona.value) return
	coachEntryMode.value = 'duel'
	resetCoachQuiz()

	const matchingCases = coachCases.value.filter((item) => {
		const category = item.category || ''
		return category.includes(selectedRegion.value)
			&& category.includes(selectedPersona.value.replace('行业', ''))
			&& matchesCoachSubject(category, subjectName)
	})

	const randomCase = matchingCases[Math.floor(Math.random() * matchingCases.length)]
	const scenario = randomCase || buildCoachFallbackScenario(subjectName)
	if (randomCase) {
		currentScenario.value = randomCase
	} else {
		currentScenario.value = scenario
	}
	isIntelOpen.value = true
	inputMsg.value = `我要挑战【${scenario.name}】场景`
	sendMessage()
}

const presetMsg = (message) => {
	console.info('[chat-debug] preset', { message })
	inputMsg.value = message
	sendMessage()
}

const handleLogout = () => {
	auth.logout()
	uni.reLaunch({ url: '/pages/login/login' })
}

const goToAdmin = () => {
	isSidebarOpen.value = false
	currentTab.value = 'admin'
	uni.navigateTo({ url: '/pages/admin/admin' })
}

const requestCoachEvaluation = () => {
	if (isGenerating.value || messages.value.length === 0) return
	inputMsg.value = [
		'请切换到资深销售总监 / 金牌导师的视角，基于刚才全部对话输出结构化点评。',
		'要求包含：',
		'1. 战力评分（百分制）',
		'2. 报价功底与关键参数完整度',
		'3. 盈利分析与风险提醒',
		'4. 更好的成交推进话术',
		'请用 Markdown 输出。',
	].join('\n')
	sendMessage()
}

const previewImage = (url) => {
	uni.previewImage({ urls: [url] })
}

const readImageAsDataUrl = async (filePath) => {
	if (!filePath || !uni.getFileSystemManager) return ''
	return await new Promise((resolve) => {
		try {
			uni.getFileSystemManager().readFile({
				filePath,
				encoding: 'base64',
				success: ({ data }) => resolve(buildImageDataUrl(filePath, data)),
				fail: () => resolve(''),
			})
		} catch (error) {
			resolve('')
		}
	})
}

const triggerImageUpload = () => {
	uni.chooseImage({
		count: 1,
		sizeType: ['compressed'],
		success: async (res) => {
			const filePath = res.tempFilePaths?.[0]
			const selectedTempFile = res.tempFiles?.[0] || {}
			if (!filePath) return

			const imageValidationError = validateMpImageSelection(selectedTempFile)
			if (imageValidationError) {
				uni.showToast({ title: imageValidationError, icon: 'none' })
				return
			}

			selectedImage.value = filePath
			selectedImageUploadId.value = ''
			isImageUploading.value = true

			try {
				const uploadPayload = await uploadChatImage({
					filePath,
					token: auth.token,
				})
				selectedImageUploadId.value = uploadPayload.image_upload_id
			} catch (error) {
				const dataUrl = await readImageAsDataUrl(filePath)
				if (dataUrl) {
					selectedImage.value = dataUrl
				} else {
					clearSelectedImage()
				}
				captureClientEvent({
					level: 'error',
					type: 'chat-image-upload-failure',
					message: error?.message || 'image upload failed',
					context: {
						mode: currentMode.value,
						session_id: currentSessionId.value,
					},
				})
			} finally {
				isImageUploading.value = false
			}
		},
	})
}

const removeImage = () => {
	clearSelectedImage()
}

const consumePostLoginFreshChatFlag = () => {
	try {
		const shouldCreateFreshChat = uni.getStorageSync(POST_LOGIN_FRESH_CHAT_KEY) === '1'
		if (shouldCreateFreshChat) {
			uni.removeStorageSync(POST_LOGIN_FRESH_CHAT_KEY)
		}
		return shouldCreateFreshChat
	} catch (error) {
		return false
	}
}

const ensureFreshEntrySession = () => {
	const currentSession = sessions.value.find((item) => item.id === currentSessionId.value)
	if (!currentSession || (currentSession.messages && currentSession.messages.length > 0)) {
		startNewChat({ forceCreate: true })
	}
	inputMsg.value = ''
	clearSelectedImage()
	scrollTop.value = 0
}

const fetchCoachCases = async () => {
	try {
		const response = await new Promise((resolve, reject) => {
			uni.request({
				url: resolveApiUrl('/api/upload/coach-cases'),
				method: 'GET',
				header: {
					Authorization: `Bearer ${auth.token}`,
				},
				success: resolve,
				fail: reject,
			})
		})

		if (response.statusCode >= 400) {
			throw new Error(`coach cases request failed: ${response.statusCode}`)
		}

		coachCases.value = Array.isArray(response.data)
			? response.data
			: Array.isArray(response.data?.cases)
				? response.data.cases
				: []
	} catch (error) {
		coachCases.value = []
	}
}

const fetchPublicSettings = async () => {
	try {
		const response = await new Promise((resolve, reject) => {
			uni.request({
				url: resolveApiUrl('/api/settings/public'),
				method: 'GET',
				success: resolve,
				fail: reject,
			})
		})

		if (response.statusCode >= 400) return
		if (response.data?.ai_welcome_message) {
			welcomeMsg.value = response.data.ai_welcome_message
		}
	} catch (error) {}
}

onMounted(() => {
	if (!auth.isAuthenticated) {
		uni.reLaunch({ url: '/pages/login/login' })
		return
	}

	const shouldFreshChat = consumePostLoginFreshChatFlag()
	const initialMode = shouldFreshChat ? 'general' : getInitialChatMode()
	currentMode.value = ''
	switchMode(initialMode)
	fetchCoachCases()
	fetchPublicSettings()
	fetchCurrentNotices()
	if (shouldFreshChat) {
		ensureFreshEntrySession()
	}
})

onUnmounted(() => {
	if (scrollBottomTimer) {
		clearTimeout(scrollBottomTimer)
		scrollBottomTimer = null
	}
})

watch(messages, (value) => {
	console.info('[chat-debug] messages-watch', {
		length: value.length,
		roles: value.slice(-4).map((item) => item.role),
	})
}, { deep: true })

</script>

<style scoped>
.general-mode {
	--bg-primary: #f5f7fb;
	--bg-secondary: #ffffff;
	--accent-color: #f59e0b;
	--text-primary: #0f172a;
	--text-secondary: #64748b;
	--border-light: rgba(226, 232, 240, 0.92);
}

.coach-mode {
	--bg-primary: #f1fbf6;
	--bg-secondary: #ffffff;
	--accent-color: #10b981;
	--text-primary: #0f172a;
	--text-secondary: #64748b;
	--border-light: rgba(211, 233, 221, 0.92);
}

.expert-mode {
	--bg-primary: #f4f8ff;
	--bg-secondary: #ffffff;
	--accent-color: #3b82f6;
	--text-primary: #0f172a;
	--text-secondary: #64748b;
	--border-light: rgba(219, 234, 254, 0.96);
}

.gradient-text {
	color: var(--accent-color);
}

.coach-mode .new-chat-btn,
.coach-mode .sidebar-settings-btn,
.coach-mode .sidebar-admin-btn,
.coach-mode .user-avatar-sidebar {
	color: var(--accent-color);
}

.coach-mode .session-item.active {
	border-color: var(--accent-color);
}

.expert-mode .new-chat-btn,
.expert-mode .sidebar-settings-btn,
.expert-mode .sidebar-admin-btn,
.expert-mode .user-avatar-sidebar {
	color: var(--accent-color);
}

.expert-mode .session-item.active {
	border-color: var(--accent-color);
}

.app-layout {
	display: flex;
	flex-direction: column;
	min-height: 100vh;
	width: 100%;
	background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, var(--bg-primary) 100%);
	overflow: hidden;
}

.glass-panel {
	background: rgba(255, 255, 255, 0.94);
	backdrop-filter: blur(24rpx);
	border: 1px solid rgba(255, 255, 255, 0.7);
}

.sidebar-overlay {
	position: fixed;
	inset: 0;
	background: rgba(15, 23, 42, 0.26);
	backdrop-filter: blur(6rpx);
	z-index: 1000;
	opacity: 0;
	pointer-events: none;
	transition: opacity 0.2s ease;
}

.sidebar-overlay.show {
	opacity: 1;
	pointer-events: auto;
}

.sidebar {
	position: fixed;
	top: 0;
	left: 0;
	bottom: 0;
	width: 560rpx;
	max-width: 82vw;
	padding: calc(108rpx + env(safe-area-inset-top)) 28rpx 28rpx;
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	transform: translateX(-100%);
	transition: transform 0.24s ease;
	z-index: 1001;
	box-shadow: 24rpx 0 54rpx rgba(15, 23, 42, 0.08);
	pointer-events: none;
}

.sidebar.show {
	transform: translateX(0);
	pointer-events: auto;
}

.sidebar-header {
	display: flex;
}

.new-chat-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
	width: 100%;
	height: 88rpx;
	border-radius: 28rpx;
	background: #0f172a;
	color: #ffffff;
	font-size: 28rpx;
	font-weight: 700;
}

.new-chat-plus {
	font-size: 36rpx;
	line-height: 1;
}

.new-chat-btn::after,
.delete-btn::after,
.sidebar-settings-btn::after,
.sidebar-admin-btn::after,
.logout-link-sidebar::after,
.zen-send-btn::after,
.quit-combat-btn::after {
	border: none;
}

.session-list {
	flex: 1;
	min-height: 0;
}

.session-item {
	display: flex;
	align-items: center;
	gap: 12rpx;
	padding: 20rpx 22rpx;
	margin-bottom: 12rpx;
	border-radius: 24rpx;
	border: 1px solid transparent;
}

.session-item-shell {
	background: rgba(255, 255, 255, 0.7);
}

.session-item.active {
	border-color: rgba(37, 99, 235, 0.2);
	background: rgba(37, 99, 235, 0.08);
}

.session-title {
	flex: 1;
	font-size: 24rpx;
	color: var(--text-primary);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.delete-btn {
	margin: 0;
	width: 52rpx;
	height: 52rpx;
	border-radius: 50%;
	background: rgba(239, 68, 68, 0.08);
	color: #dc2626;
	font-size: 28rpx;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	padding: 0;
}

.sidebar-footer {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.sidebar-settings-btn,
.sidebar-admin-btn {
	margin: 0;
	height: 80rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 24rpx;
	background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
	color: #ffffff;
	font-size: 30rpx;
	line-height: 1;
	text-align: center;
	font-weight: 700;
}

.sidebar-settings-btn {
	background: linear-gradient(135deg, #2563eb 0%, #5046e5 100%);
}

.settings-overlay {
	position: fixed;
	inset: 0;
	z-index: 70;
	background: rgba(15, 23, 42, 0.46);
	display: flex;
	align-items: flex-end;
	justify-content: center;
	padding: 32rpx 24rpx calc(32rpx + env(safe-area-inset-bottom));
}

.settings-sheet {
	width: 100%;
	max-width: 720rpx;
	background: rgba(255, 255, 255, 0.98);
	border-radius: 32rpx;
	padding: 28rpx;
	box-shadow: 0 24rpx 60rpx rgba(15, 23, 42, 0.18);
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}

.settings-sheet-header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 24rpx;
}

.settings-sheet-title {
	display: block;
	font-size: 34rpx;
	font-weight: 800;
	color: #0f172a;
}

.settings-sheet-desc {
	display: block;
	margin-top: 8rpx;
	font-size: 24rpx;
	line-height: 1.5;
	color: #64748b;
}

.settings-sheet-close {
	font-size: 44rpx;
	line-height: 1;
	color: #64748b;
	padding: 4rpx 8rpx;
}

.settings-section {
	display: flex;
	flex-direction: column;
	gap: 14rpx;
}

.settings-section-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #0f172a;
}

.settings-section-desc {
	font-size: 22rpx;
	line-height: 1.5;
	color: #64748b;
}

.length-option-list {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
}

.length-option-btn {
	margin: 0;
	padding: 20rpx 22rpx;
	border-radius: 24rpx;
	background: #f8fafc;
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 8rpx;
	border: 2rpx solid transparent;
}

.length-option-btn.active {
	background: rgba(80, 70, 229, 0.08);
	border-color: rgba(80, 70, 229, 0.25);
}

.length-option-main {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.length-option-icon {
	font-size: 28rpx;
}

.length-option-label {
	font-size: 28rpx;
	font-weight: 700;
	color: #0f172a;
}

.length-option-desc {
	font-size: 22rpx;
	line-height: 1.5;
	color: #64748b;
}

.settings-input {
	width: 100%;
	min-height: 84rpx;
	border-radius: 22rpx;
	background: #f8fafc;
	padding: 0 24rpx;
	font-size: 28rpx;
	color: #0f172a;
	box-sizing: border-box;
}

.settings-submit-btn {
	margin: 8rpx 0 0;
	height: 86rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 24rpx;
	background: linear-gradient(135deg, #2563eb 0%, #5046e5 100%);
	color: #ffffff;
	font-size: 28rpx;
	font-weight: 700;
}

.sidebar-user-info {
	display: flex;
	align-items: center;
	gap: 16rpx;
	padding: 18rpx;
}

.sidebar-account-card {
	background: rgba(255, 255, 255, 0.92);
	border-radius: 24rpx;
}

.user-avatar-sidebar {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	background: #0f172a;
	color: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 28rpx;
	font-weight: 800;
}

.user-details {
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.user-name-sidebar {
	font-size: 24rpx;
	font-weight: 700;
	color: var(--text-primary);
}

.logout-link-sidebar {
	margin: 0;
	padding: 0;
	background: transparent;
	color: #ef4444;
	font-size: 22rpx;
	line-height: 1.3;
	text-align: left;
}

.chat-container {
	flex: 1;
	display: flex;
	flex-direction: column;
	min-height: 100vh;
}

.chat-nav {
	padding: 16rpx 20rpx 12rpx;
	padding-top: calc(84rpx + env(safe-area-inset-top));
	display: flex;
	align-items: center;
	justify-content: space-between;
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	z-index: 40;
	gap: 12rpx;
}

.nav-shell {
	background: rgba(255, 255, 255, 0.97);
	border-bottom: 1px solid rgba(148, 163, 184, 0.08);
}

.nav-left {
	display: flex;
	align-items: center;
	justify-content: flex-start;
	width: 72rpx;
	position: relative;
	left: auto;
	top: auto;
	transform: none;
	flex-shrink: 0;
}

.nav-btn-hamburg {
	margin: 0;
	width: 72rpx;
	height: 72rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 20rpx;
	background: rgba(255, 255, 255, 0.98);
	padding: 0;
	flex-shrink: 0;
}

.nav-btn-hamburg::after {
	border: none;
}

.nav-btn-hamburg::before {
	content: '≡';
	font-size: 42rpx;
	font-weight: 700;
	line-height: 1;
	color: #475569;
}

.nav-btn-text {
	font-size: 0;
	color: transparent;
	line-height: 1;
}

.nav-right-spacer {
	display: block;
	width: 112rpx;
	min-width: 112rpx;
	flex-shrink: 0;
}

.mode-selector {
	background: rgba(255, 255, 255, 0.86);
	box-shadow: inset 0 0 0 1rpx rgba(226, 232, 240, 0.95);
}

.mode-selector-pill {
	display: flex;
	flex: 1;
	align-items: center;
	padding: 6rpx;
	border-radius: 999rpx;
	gap: 4rpx;
	width: auto;
	min-width: 0;
	max-width: none;
	margin: 0;
}

.mode-tab {
	display: flex;
	align-items: center;
	justify-content: center;
	min-width: 0;
	flex: 1;
	padding: 14rpx 10rpx;
	border-radius: 999rpx;
	transition: all 0.2s ease;
}

.mode-btn {
	justify-content: center;
}

.mode-btn.active {
	color: var(--accent-color);
}

.tab-active-general,
.tab-active-coach,
.tab-active-expert {
	background: #ffffff;
	box-shadow: 0 8rpx 22rpx rgba(15, 23, 42, 0.08);
}

.tab-text {
	font-size: 26rpx;
	font-weight: 700;
	color: #334155;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.mode-btn.active .tab-text {
	color: var(--accent-color);
}

.tab-divider {
	display: none;
}

.main-body-wrapper {
	flex: 1;
	display: flex;
	flex-direction: column;
	min-height: 0;
	position: relative;
	padding-top: calc(132rpx + env(safe-area-inset-top));
}

.chat-main {
	flex: 1;
	min-height: 0;
}

.welcome-screen {
	padding-bottom: 120rpx;
}

.welcome-stage {
	width: 100%;
}

.zen-welcome-stage {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 28rpx 24rpx 200rpx;
}

.welcome-content {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	width: 100%;
	max-width: 760rpx;
	max-width: 920rpx;
}

.welcome-centered {
	align-items: center;
	text-align: center;
}

.mode-stage-offset {
	padding-top: 76rpx;
}

.welcome-panel {
	width: 100%;
	max-width: 920rpx;
	padding: 40rpx 28rpx 28rpx;
	border-radius: 40rpx;
	background: rgba(255, 255, 255, 0.9);
	box-sizing: border-box;
}

.zen-title,
.zen-subtitle {
	display: block;
	width: 100%;
}

.zen-avatar-breathe {
	width: 140rpx;
	height: 140rpx;
	border-radius: 50%;
	background: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 28rpx;
	box-shadow: 0 20rpx 50rpx rgba(15, 23, 42, 0.08);
}
/* --- Coach Quiz Premium Redesign for Uniapp --- */
.coach-quiz-picker-premium {
	width: 100%;
	background: #ffffff;
	border-radius: 36rpx;
	padding: 40rpx;
	box-shadow: 0 20rpx 40rpx rgba(16, 185, 129, 0.08);
}

.picker-back-btn {
	width: 140rpx;
	height: 64rpx;
	line-height: 64rpx;
	background: #f1f5f9;
	border-radius: 999rpx;
	font-size: 24rpx;
	font-weight: 700;
	color: #64748b;
	margin: 0 0 40rpx 0;
}

.picker-title-pnl {
	margin-bottom: 48rpx;
}

.p-title {
	display: block;
	font-size: 44rpx;
	font-weight: 800;
	color: #0f172a;
	margin-bottom: 12rpx;
}

.p-subtitle {
	font-size: 26rpx;
	color: #64748b;
}

.count-grid-modern {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 20rpx;
	margin-bottom: 32rpx;
}

.count-card-item {
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	border-radius: 28rpx;
	padding: 32rpx 10rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8rpx;
	margin: 0;
}

.c-num {
	font-size: 40rpx;
	font-weight: 800;
	color: #10b981;
}

.c-unit {
	font-size: 24rpx;
	color: #64748b;
}

.picker-status-box {
	text-align: center;
	font-size: 24rpx;
	color: #10b981;
	padding: 20rpx;
}

.coach-quiz-panel-premium {
	background: #ffffff;
	border-radius: 40rpx;
	padding: 40rpx;
	box-shadow: 0 30rpx 60rpx rgba(0,0,0,0.08);
}

.quiz-panel-head {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 40rpx;
}

.tag-primary {
	padding: 8rpx 20rpx;
	background: #10b981;
	color: #ffffff;
	border-radius: 12rpx;
	font-size: 22rpx;
	font-weight: 700;
	margin-right: 12rpx;
}

.tag-secondary {
	padding: 8rpx 20rpx;
	background: #f1f5f9;
	color: #64748b;
	border-radius: 12rpx;
	font-size: 22rpx;
	font-weight: 700;
}

.quiz-panel-progress {
	font-size: 26rpx;
	font-weight: 700;
	color: #94a3b8;
}

.quiz-panel-question {
	margin-bottom: 48rpx;
}

.question-text {
	font-size: 38rpx;
	line-height: 1.5;
	font-weight: 800;
	color: #0f172a;
}

.quiz-panel-options {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	margin-bottom: 40rpx;
}

.quiz-panel-option-btn {
	margin: 0;
	background: #ffffff;
	border: 1px solid #e2e8f0;
	border-radius: 24rpx;
	padding: 28rpx 32rpx;
	display: flex;
	align-items: center;
	gap: 20rpx;
	text-align: left;
}

.opt-prefix {
	width: 44rpx;
	height: 44rpx;
	background: #f1f5f9;
	border-radius: 12rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24rpx;
	font-weight: 800;
	color: #64748b;
	flex-shrink: 0;
}

.opt-label {
	flex: 1;
	font-size: 30rpx;
	color: #334155;
	line-height: 1.4;
}

.opt-status {
	width: 32rpx;
	height: 32rpx;
}

.quiz-panel-option-btn.correct {
	background: #f0fdf4;
	border-color: #22c55e;
}
.quiz-panel-option-btn.correct .opt-prefix { background: #22c55e; color: #ffffff; }
.opt-ico-correct { color: #22c55e; font-weight: 800; }

.quiz-panel-option-btn.wrong {
	background: #fef2f2;
	border-color: #ef4444;
}
.quiz-panel-option-btn.wrong .opt-prefix { background: #ef4444; color: #ffffff; }
.opt-ico-wrong { color: #ef4444; font-weight: 800; }

.quiz-panel-feedback {
	border-radius: 24rpx;
	padding: 32rpx;
	margin-bottom: 40rpx;
	animation: slideInDown 0.3s ease;
}

.quiz-panel-feedback.is-correct { background: #f0fdf4; border: 1px solid #bbf7d0; }
.quiz-panel-feedback.is-wrong { background: #fef2f2; border: 1px solid #fecaca; }

.feedback-head-row {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-bottom: 12rpx;
}

.fb-title {
	font-size: 28rpx;
	font-weight: 800;
}

.fb-ans {
	display: block;
	font-size: 26rpx;
	font-weight: 700;
	margin-bottom: 8rpx;
}

.fb-expl {
	font-size: 24rpx;
	line-height: 1.6;
	opacity: 0.8;
}

.quiz-panel-actions {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.quiz-btn-nav {
	margin: 0;
	height: 90rpx;
	line-height: 90rpx;
	border-radius: 20rpx;
	font-size: 28rpx;
	font-weight: 700;
}

.quiz-btn-nav.ghost {
	background: #f1f5f9;
	color: #64748b;
	padding: 0 40rpx;
}

.quiz-btn-nav.primary {
	background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
	color: #ffffff;
	flex: 1;
	margin-left: 20rpx;
}

.ico-next { margin-left: 12rpx; }

/* Summary Premium */
.coach-quiz-summary-premium {
	text-align: center;
	padding: 64rpx 40rpx;
}

.summary-visual {
	width: 160rpx;
	height: 160rpx;
	background: #fef3c7;
	border-radius: 50rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin: 0 auto 40rpx;
	box-shadow: 0 20rpx 40rpx rgba(245, 158, 11, 0.15);
}

.summary-emoji {
	font-size: 80rpx;
}

.summary-title-main {
	display: block;
	font-size: 40rpx;
	font-weight: 800;
	color: #0f172a;
	margin-bottom: 48rpx;
}

.summary-score-row {
	display: flex;
	align-items: center;
	justify-content: center;
	background: #f8fafc;
	border-radius: 32rpx;
	padding: 40rpx 0;
	margin-bottom: 48rpx;
}

.score-card {
	flex: 1;
	display: flex;
	flex-direction: column;
}

.score-val {
	font-size: 48rpx;
	font-weight: 800;
	color: #10b981;
}

.score-lab {
	font-size: 22rpx;
	color: #94a3b8;
	font-weight: 700;
}

.score-line {
	width: 1px;
	height: 60rpx;
	background: #e2e8f0;
}

.summary-note {
	font-size: 26rpx;
	color: #64748b;
	margin-bottom: 64rpx;
	padding: 0 40rpx;
	line-height: 1.6;
}

.premium-actions-stack {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}

.quiz-primary-stack-btn {
	background: linear-gradient(135deg, #10b981 0%, #059669 100%);
	color: #ffffff;
	border-radius: 24rpx;
	height: 100rpx;
	line-height: 100rpx;
	font-size: 30rpx;
	font-weight: 800;
}

.quiz-ghost-stack-btn {
	background: transparent;
	color: #64748b;
	font-size: 28rpx;
}

/* Base Styles Refinement */

.zen-level-up-container {
	width: 100%;
	background: #ffffff;
	border-radius: 36rpx;
	padding: 36rpx 28rpx;
	box-sizing: border-box;
	box-shadow: 0 18rpx 40rpx rgba(15, 23, 42, 0.05);
}

.zen-level-header {
	margin-bottom: 28rpx;
	padding-bottom: 24rpx;
	border-bottom: 1px solid var(--border-light);
}

.coach-step-pill {
	display: inline-flex;
	align-items: center;
	padding: 10rpx 18rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.76);
	border: 1px solid var(--border-light);
	font-size: 22rpx;
	font-weight: 700;
	color: #365f4d;
	margin-bottom: 16rpx;
}

.zen-level-text {
	display: block;
	font-size: 22rpx;
	font-weight: 800;
	color: var(--accent-color);
	letter-spacing: 3rpx;
	margin-bottom: 10rpx;
}

.zen-level-desc {
	font-size: 40rpx;
	line-height: 1.2;
	font-weight: 800;
	color: var(--text-primary);
}

.zen-breadcrumbs {
	display: flex;
	flex-wrap: wrap;
	gap: 12rpx;
	margin-bottom: 24rpx;
}

.coach-selection-summary {
	display: flex;
	flex-wrap: wrap;
	justify-content: center;
	gap: 12rpx;
	margin-bottom: 10rpx;
}

.zen-breadcrumb {
	padding: 10rpx 18rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.94);
	border: 1px solid var(--border-light);
	font-size: 22rpx;
	color: #365f4d;
}

.coach-selection-chip {
	padding: 10rpx 18rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.86);
	border: 1px solid var(--border-light);
	font-size: 22rpx;
	color: #365f4d;
}

.coach-selection-chip-button {
	margin: 0;
	line-height: 1.4;
}

.coach-selection-chip-button::after {
	border: none;
}

.arrow {
	margin-left: 10rpx;
	color: #94a3b8;
}

.zen-level-grid {
	display: flex;
	flex-direction: column;
	gap: 18rpx;
}

.slide-in {
	animation: slideInRight 0.28s ease;
}

@keyframes slideInRight {
	from { opacity: 0; transform: translateX(20rpx); }
	to { opacity: 1; transform: translateX(0); }
}

.zen-level-card {
	display: flex;
	align-items: center;
	gap: 22rpx;
	padding: 26rpx 24rpx;
	border-radius: 28rpx;
	background: #f8fafc;
	border: 1px solid var(--border-light);
}

.zen-level-card-button {
	width: 100%;
	margin: 0;
	text-align: left;
}

.zen-level-card-button::after {
	border: none;
}

.zen-card-huge-icon,
.zen-card-huge-emoji {
	width: 82rpx;
	text-align: center;
	font-size: 54rpx;
	font-weight: 800;
	color: var(--text-primary);
}

.zen-level-info {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}

.zen-level-title {
	font-size: 30rpx;
	font-weight: 800;
	color: var(--text-primary);
}

.zen-level-desc-mini {
	font-size: 24rpx;
	line-height: 1.45;
	color: var(--text-secondary);
}

.message-list {
	padding: 0 24rpx 520rpx;
}

.message-tail-spacer {
	height: 240rpx;
}

.message-wrapper {
	display: flex;
	gap: 16rpx;
	margin-bottom: 28rpx;
	margin-bottom: 26rpx;
}

.message-wrapper.user {
	flex-direction: row-reverse;
}

.avatar {
	width: 72rpx;
	height: 72rpx;
	flex-shrink: 0;
}

.xiaoyi-avatar {
	width: 64rpx;
	height: 64rpx;
	border-radius: 50%;
}

.user-avatar {
	width: 64rpx;
	height: 64rpx;
	border-radius: 50%;
}

.xiaoyi-avatar,
.user-avatar {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
}

.user-avatar {
	display: flex;
	align-items: center;
	justify-content: center;
	background: #0f172a;
	color: #ffffff;
	font-size: 26rpx;
	font-weight: 700;
}

.message-body {
	flex: 1;
}

.message-content {
	max-width: 76%;
	border-radius: 22rpx;
	padding: 26rpx 30rpx;
	border-radius: 30rpx;
	font-size: 30rpx;
	line-height: 1.66;
}

.mp-message-rich {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
}

.mp-message-block {
	display: block;
}

.mp-message-line {
	display: flex;
	align-items: flex-start;
	gap: 8rpx;
}

.mp-message-line-text {
	flex: 1;
	font-size: 30rpx;
	line-height: 1.7;
	color: inherit;
	word-break: break-word;
}

.mp-message-prefix {
	flex-shrink: 0;
	font-size: 30rpx;
	line-height: 1.7;
	font-weight: 700;
	color: inherit;
}

.mp-message-block.is-heading .mp-message-line-text {
	font-size: 34rpx;
	line-height: 1.55;
	font-weight: 800;
}

.mp-message-block.is-ordered-item .mp-message-line-text,
.mp-message-block.is-bullet-item .mp-message-line-text {
	line-height: 1.75;
}

.mp-message-divider {
	width: 100%;
	height: 2rpx;
	margin: 8rpx 0;
	background: rgba(148, 163, 184, 0.32);
}

.assistant .message-content {
	background: #ffffff;
	color: var(--text-primary);
	box-shadow: 0 10rpx 32rpx rgba(15, 23, 42, 0.05);
	border-radius: 30rpx 30rpx 30rpx 12rpx;
}

.user .message-content {
	margin-left: auto;
	background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
	color: #ffffff;
	box-shadow: 0 18rpx 36rpx rgba(79, 70, 229, 0.18);
	border-radius: 30rpx 30rpx 12rpx 30rpx;
}

:deep(.markdown-body) {
	display: block;
	word-break: break-word;
}

:deep(.markdown-body p) {
	margin-bottom: 12rpx;
}

:deep(.markdown-body p:last-child) {
	margin-bottom: 0;
}

:deep(.markdown-body table) {
	width: 100%;
	border-collapse: collapse;
	margin-top: 16rpx;
}

:deep(.markdown-body th),
:deep(.markdown-body td) {
	border: 1px solid rgba(203, 213, 225, 0.9);
	padding: 8rpx;
}

.chat-message-image {
	width: 100%;
	max-width: 360rpx;
	border-radius: 22rpx;
	margin-bottom: 16rpx;
}

.cursor-blink {
	display: inline-block;
	width: 6rpx;
	height: 28rpx;
	margin-left: 6rpx;
	background: currentColor;
	animation: blink 1s step-end infinite;
}

@keyframes blink {
	50% { opacity: 0; }
}

.combat-intel-panel {
	position: absolute;
	top: 12rpx;
	right: -620rpx;
	bottom: 18rpx;
	width: 500rpx;
	border-radius: 32rpx;
	padding: 26rpx;
	transition: right 0.28s ease;
	z-index: 30;
	pointer-events: none;
}

.combat-intel-shell {
	background: rgba(255, 255, 255, 0.96);
	border: 1px solid rgba(211, 233, 221, 0.95);
	box-shadow: -24rpx 0 54rpx rgba(25, 103, 74, 0.1);
}

.combat-intel-panel.show {
	right: 18rpx;
	pointer-events: auto;
}

.panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 20rpx;
	font-size: 30rpx;
	font-weight: 800;
	color: var(--text-primary);
}

.panel-close {
	font-size: 38rpx;
	color: #64748b;
	padding: 10rpx;
}

.panel-content {
	height: 100%;
}

.intel-section {
	margin-bottom: 20rpx;
	padding: 18rpx 20rpx;
	background: rgba(255, 255, 255, 0.96);
	border-radius: 22rpx;
	border: 1px solid var(--border-light);
}

.intel-section-highlight {
	background: rgba(15, 159, 114, 0.08);
}

.intel-label {
	display: block;
	font-size: 22rpx;
	color: #64748b;
	margin-bottom: 10rpx;
}

.intel-text {
	display: block;
	font-size: 26rpx;
	line-height: 1.6;
	color: var(--text-primary);
}

.intel-text-block {
	margin-bottom: 10rpx;
}

.quit-combat-btn {
	margin: 24rpx 0 0;
	height: 84rpx;
	line-height: 84rpx;
	border-radius: 24rpx;
	background: #ef4444;
	color: #ffffff;
	font-size: 26rpx;
	font-weight: 700;
}

.mp-chat-footer {
	position: fixed;
	left: 0;
	right: 0;
	bottom: calc(128rpx + env(safe-area-inset-bottom));
	padding: 0 20rpx;
	z-index: 25;
}

.mp-composer-shell {
	background: rgba(255, 255, 255, 0.98);
	border-radius: 36rpx;
	padding: 12rpx 16rpx;
	box-shadow: 0 14rpx 32rpx rgba(15, 23, 42, 0.08);
	border: 1px solid rgba(15, 23, 42, 0.04);
}

.mp-composer-shell.has-image {
	background: rgba(239, 246, 255, 0.96);
	border-color: rgba(37, 99, 235, 0.24);
}

.mp-composer-shell.is-focused {
	transform: translateY(-4rpx);
}

.mp-composer-main {
	display: flex;
	align-items: center;
	gap: 10rpx;
}

.mp-composer-input {
	flex: 1;
	height: 72rpx;
	line-height: 72rpx;
}

.mp-send-btn[disabled] {
	opacity: 1;
}

.zen-footer-wrapper {
	position: fixed;
	left: 0;
	right: 0;
	bottom: calc(128rpx + env(safe-area-inset-bottom));
	padding: 0 20rpx;
	z-index: 25;
}

.chat-footer {
	position: fixed;
	left: 0;
	right: 0;
	bottom: calc(128rpx + env(safe-area-inset-bottom));
	padding: 0 20rpx;
}

.zen-floating-pill {
	background: rgba(255, 255, 255, 0.98);
	backdrop-filter: blur(30rpx);
	border-radius: 36rpx;
	padding: 12rpx 16rpx;
	box-shadow: 0 14rpx 32rpx rgba(15, 23, 42, 0.08);
	border: 1px solid rgba(15, 23, 42, 0.04);
}

.input-shell {
	width: 100%;
}

.input-container.has-image {
	background: rgba(239, 246, 255, 0.96);
	border-color: rgba(37, 99, 235, 0.24);
}

.input-container.is-focused {
	transform: translateY(-4rpx);
}

.zen-image-preview-area {
	position: relative;
	width: 150rpx;
	height: 150rpx;
	margin: 8rpx 0 20rpx;
}

.image-preview-frame {
	overflow: hidden;
	border-radius: 24rpx;
}

.zen-image-preview {
	width: 150rpx;
	height: 150rpx;
	border-radius: 24rpx;
}

.image-preview-meta {
	position: absolute;
	left: 10rpx;
	bottom: 10rpx;
}

.image-preview-chip {
	padding: 8rpx 14rpx;
	border-radius: 999rpx;
	background: rgba(15, 23, 42, 0.72);
	color: #ffffff;
	font-size: 20rpx;
}

.zen-remove-image-btn {
	position: absolute;
	top: -10rpx;
	right: -10rpx;
	width: 40rpx;
	height: 40rpx;
	border-radius: 50%;
	background: #0f172a;
	color: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24rpx;
}

.zen-input-row {
	display: flex;
	align-items: center;
	gap: 10rpx;
}

.zen-upload-btn {
	width: 56rpx;
	height: 56rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(148, 163, 184, 0.12);
	flex-shrink: 0;
}

.upload-pic-btn.has-attachment {
	background: rgba(37, 99, 235, 0.12);
}

.upload-pic-mark {
	font-size: 34rpx;
	line-height: 1;
	color: #64748b;
}

.zen-input-box {
	flex: 1;
	min-height: 40rpx;
	max-height: 220rpx;
	font-size: 28rpx;
	color: var(--text-primary);
	font-weight: 500;
}

.zen-input-box-mp {
	height: 56rpx;
	line-height: 56rpx;
}

.zen-send-area {
	display: flex;
	align-items: center;
	flex-shrink: 0;
}

.zen-send-btn {
	margin: 0;
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0;
	background: #e2e8f0;
}

.zen-send-btn.active {
	background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
	box-shadow: 0 24rpx 50rpx rgba(37, 99, 235, 0.14);
}

.zen-send-btn.stop {
	background: #ef4444;
}

.icon-send {
	display: block;
	font-size: 30rpx;
	font-weight: 800;
	line-height: 1;
	color: #94a3b8;
}

.icon-send-image {
	width: 30rpx;
	height: 30rpx;
	display: block;
	opacity: 0.72;
}

.zen-send-btn.active .icon-send,
.zen-send-btn.stop .icon-send {
	color: #ffffff;
}

.zen-send-btn.active .icon-send-image {
	opacity: 1;
}

.composer-status-row {
	display: flex;
	flex-direction: column;
	gap: 10rpx;
	margin-top: 14rpx;
	padding: 0 12rpx;
}

.composer-status-chip {
	padding: 12rpx 18rpx;
	border-radius: 999rpx;
	font-size: 22rpx;
	line-height: 1.4;
}

.composer-status-chip.image-ready {
	background: rgba(239, 246, 255, 0.96);
	color: #2563eb;
}

.composer-status-chip.generating {
	background: rgba(255, 247, 237, 0.96);
	color: #ea580c;
}

.zen-bottom-nav {
	position: fixed;
	left: 24rpx;
	right: 24rpx;
	bottom: calc(8rpx + env(safe-area-inset-bottom));
	height: 108rpx;
	padding: 0 22rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.92);
	backdrop-filter: blur(20rpx);
	display: flex;
	align-items: center;
	justify-content: space-between;
	box-shadow: 0 12rpx 40rpx rgba(15, 23, 42, 0.08);
	border: 1px solid rgba(15, 23, 42, 0.04);
	z-index: 24;
}

.zen-nav-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 6rpx;
	flex: 1;
	min-width: 0;
}

.zen-nav-icon-wrapper {
	width: 58rpx;
	height: 58rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.zen-nav-icon-image {
	width: 34rpx;
	height: 34rpx;
	display: block;
	opacity: 0.5;
}

.zen-nav-icon {
	position: relative;
}

.zen-nav-badge {
	position: absolute;
	top: -2rpx;
	right: -4rpx;
	width: 14rpx;
	height: 14rpx;
	border-radius: 50%;
	background: #ef4444;
	box-shadow: 0 0 0 4rpx #ffffff;
}

.zen-nav-item.active .zen-nav-icon-image {
	opacity: 1;
}

.zen-nav-label {
	font-size: 22rpx;
	font-weight: 700;
	color: #64748b;
}

.zen-nav-item.active .zen-nav-label {
	color: #0f172a;
}

.notice-center-overlay {
	position: fixed;
	inset: 0;
	background: rgba(15, 23, 42, 0.32);
	backdrop-filter: blur(8rpx);
	z-index: 50;
	display: flex;
	align-items: flex-end;
	justify-content: center;
	padding: 0 24rpx calc(132rpx + env(safe-area-inset-bottom));
	box-sizing: border-box;
}

.notice-center-sheet {
	width: 100%;
	max-width: 860rpx;
	max-height: 60vh;
	background: rgba(255, 255, 255, 0.98);
	border-radius: 36rpx;
	box-shadow: 0 18rpx 60rpx rgba(15, 23, 42, 0.18);
	padding: 28rpx 24rpx;
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.notice-center-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.notice-center-title {
	font-size: 34rpx;
	font-weight: 800;
	color: #0f172a;
}

.notice-center-close {
	font-size: 40rpx;
	line-height: 1;
	color: #64748b;
	padding: 8rpx;
}

.notice-center-tabs {
	display: flex;
	gap: 12rpx;
}

.notice-center-tab {
	flex: 1;
	height: 72rpx;
	border-radius: 999rpx;
	background: #f8fafc;
	color: #64748b;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24rpx;
	font-weight: 700;
}

.notice-center-tab.active {
	background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
	color: #2563eb;
}

.notice-center-scroll {
	max-height: 44vh;
	min-height: 220rpx;
}

.notice-center-empty {
	padding: 36rpx 16rpx;
	text-align: center;
	font-size: 24rpx;
	color: #94a3b8;
}

.notice-center-card {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	padding: 22rpx 20rpx;
	border-radius: 24rpx;
	background: #f8fafc;
	margin-bottom: 16rpx;
}

.notice-center-date {
	font-size: 22rpx;
	color: #94a3b8;
}

.notice-center-content {
	font-size: 26rpx;
	line-height: 1.65;
	color: #0f172a;
	white-space: pre-wrap;
	word-break: break-word;
}

@media screen and (min-width: 768px) {
	.app-layout {
		flex-direction: row;
	}

	.sidebar-overlay {
		display: none;
	}

	.sidebar {
		position: static;
		transform: none;
		width: 320px;
		max-width: none;
		min-height: 100vh;
		padding: 24px;
		pointer-events: auto;
	}

	.chat-container {
		min-height: 100vh;
	}

	.chat-nav {
		padding: 24px 32px;
		position: static;
	}

	.main-body-wrapper {
		padding-top: 0;
	}

	.nav-left {
		width: auto;
	}

	.nav-right-spacer {
		display: none;
	}

	.nav-btn-hamburg {
		display: none;
	}

	.mode-selector-pill {
		position: static;
	}

	.welcome-content,
	.welcome-panel {
		max-width: 860rpx;
	}

	.zen-suggestion-grid {
		max-width: 920rpx;
	}

	.combat-intel-panel {
		right: 18rpx;
	}

	.zen-footer-wrapper {
		position: static;
		padding: 0 32px 32px;
		margin-top: auto;
		pointer-events: auto;
	}

	.zen-bottom-nav {
		display: none;
	}
}
</style>
