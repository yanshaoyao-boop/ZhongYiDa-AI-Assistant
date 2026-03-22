<template>
	<aside :class="['combat-intel-panel', 'glass-panel', { 'show-mobile': showMobile }]">
		<div class="panel-header">
			<Zap class="icon-zap" size="20" />
			<h3>实战情报中心</h3>
			<button class="panel-close-mobile" @click="$emit('close')"><X size="20" /></button>
		</div>
		
		<div class="intel-scroll">
			<div class="intel-section">
				<label>🎯 当前目标</label>
				<p class="mission-goal">{{ currentScenario ? currentScenario.name : '未选择' }}</p>
			</div>

			<div v-if="currentScenario?.persona" class="intel-section">
				<label>👤 客户情报 (Persona)</label>
				<p class="persona-brief">{{ currentScenario.persona }}</p>
			</div>

			<div v-if="currentScenario?.cargo_details" class="intel-section cargo-intel">
				<label>📦 隐藏货盘参数 (关键底牌)</label>
				<div class="cargo-grid-mini">
					<div class="cargo-item"><span>品名:</span> {{ currentScenario.cargo_details.item }}</div>
					<div class="cargo-item"><span>件数:</span> {{ currentScenario.cargo_details.qty }} CTNS</div>
					<div class="cargo-item"><span>规格:</span> {{ currentScenario.cargo_details.size_cm }} CM</div>
					<div class="cargo-item"><span>重量:</span> {{ currentScenario.cargo_details.gw_kg }} KG</div>
					<div class="cargo-item"><span>目的地:</span> {{ currentScenario.cargo_details.destination }}</div>
				</div>
				<div v-if="currentScenario.cargo_details.hidden_issue" class="intel-warning">
					⚠️ 陷阱提示：{{ currentScenario.cargo_details.hidden_issue }}
				</div>
			</div>

			<div class="intel-section">
				<label>⚔️ 必杀技 / 通关条件</label>
				<ul class="success-list">
					<li 
						v-for="(item, idx) in successCriteria" 
						:key="idx" 
						class="success-item"
					>
						{{ item }}
					</li>
				</ul>
			</div>

			<button 
				v-if="currentScenario" 
				class="quit-combat-btn" 
				@click="$emit('quit')"
			>
				结束对练并评价
			</button>
		</div>
	</aside>
</template>

<script setup>
import { Zap, X } from 'lucide-vue-next'

defineProps({
	showMobile: {
		type: Boolean,
		default: false
	},
	currentScenario: {
		type: Object,
		default: null
	},
	successCriteria: {
		type: Array,
		default: () => []
	}
})

defineEmits(['close', 'quit'])
</script>

<style scoped>
.combat-intel-panel {
	position: fixed;
	top: 100px;
	right: 16px;
	width: 280px;
	max-height: calc(100vh - 200px);
	background: rgba(255, 255, 255, 0.9);
	backdrop-filter: blur(20px);
	border-radius: 20px;
	padding: 24px 0;
	display: flex;
	flex-direction: column;
	box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
	border: 1px solid rgba(0, 0, 0, 0.04);
	z-index: 50;
	transform: translateX(120%);
	transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.combat-intel-panel.show-mobile {
	transform: translateX(0);
}

@media screen and (min-width: 1200px) {
	.combat-intel-panel {
		position: sticky;
		top: 24px;
		right: 0;
		transform: translateX(0);
		max-height: 100vh;
		min-width: 280px;
		z-index: 10;
		margin-left: 24px;
	}
	.panel-close-mobile {
		display: none;
	}
}

.panel-header {
	display: flex;
	align-items: center;
	padding: 0 24px 16px;
	border-bottom: 1px solid rgba(0, 0, 0, 0.05);
	margin-bottom: 20px;
	gap: 12px;
}

.icon-zap {
	color: #eab308;
}

h3 {
	margin: 0;
	font-size: 16px;
	font-weight: 700;
	color: #1e293b;
	flex: 1;
}

.panel-close-mobile {
	background: transparent;
	border: none;
	color: #94a3b8;
	cursor: pointer;
}

.intel-scroll {
	flex: 1;
	overflow-y: auto;
	padding: 0 24px;
}

.intel-section {
	margin-bottom: 24px;
}

label {
	display: block;
	font-size: 11px;
	font-weight: 700;
	color: #94a3b8;
	text-transform: uppercase;
	margin-bottom: 8px;
	letter-spacing: 0.5px;
}

.mission-goal {
	font-size: 15px;
	color: #1e293b;
	font-weight: 600;
	line-height: 1.4;
}

.persona-brief {
	font-size: 14px;
	color: #475569;
	line-height: 1.5;
	background: rgba(37, 99, 235, 0.04);
	padding: 10px;
	border-radius: 10px;
}

.cargo-grid-mini {
	display: flex;
	flex-direction: column;
	gap: 6px;
	background: #f8fafc;
	padding: 12px;
	border-radius: 12px;
	border: 1px solid rgba(0, 0, 0, 0.02);
}

.cargo-item {
	font-size: 12px;
	color: #475569;
}
.cargo-item span {
	font-weight: 600;
	color: #64748b;
	margin-right: 4px;
}

.intel-warning {
	margin-top: 10px;
	font-size: 12px;
	color: #ef4444;
	font-weight: 600;
	background: rgba(239, 68, 68, 0.05);
	padding: 8px;
	border-radius: 8px;
}

.success-list {
	list-style: none;
	padding: 0;
	margin: 0;
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.success-item {
	font-size: 13px;
	color: #1e293b;
	background: #ffffff;
	padding: 10px 14px;
	border-radius: 10px;
	border: 1px solid rgba(0, 0, 0, 0.04);
	line-height: 1.4;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}
.success-item::before {
	content: '✓';
	color: #10b981;
	font-weight: bold;
	margin-right: 8px;
}

.quit-combat-btn {
	width: 100%;
	height: 48px;
	background: #ef4444;
	color: #ffffff;
	font-size: 14px;
	font-weight: 700;
	border-radius: 14px;
	border: none;
	cursor: pointer;
	margin-top: 12px;
	transition: all 0.2s;
	box-shadow: 0 8px 16px -4px rgba(239, 68, 68, 0.15);
}
.quit-combat-btn:hover {
	transform: translateY(-2px);
	background: #dc2626;
	box-shadow: 0 12rpx 24rpx rgba(239, 68, 68, 0.2);
}
</style>
