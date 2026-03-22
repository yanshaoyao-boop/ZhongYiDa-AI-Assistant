<template>
	<footer class="chat-footer">
		<div 
			class="input-container glass-panel" 
			:class="{'has-image': selectedImage, 'is-focused': isFocused}"
			@dragover.prevent="isDragging = true"
			@dragleave.prevent="isDragging = false"
			@drop.prevent="handleDrop"
		>
			<div v-if="selectedImage" class="image-preview-area">
				<img :src="selectedImage" alt="Preview" class="image-preview" />
				<button class="remove-image-btn" @click="$emit('removeImage')">
					<XCircle size="18" />
				</button>
			</div>

			<div class="input-box">
				<button class="upload-pic-btn" @click="$emit('triggerUpload')" title="上传图片分析">
					<Image class="icon-img" />
				</button>
				
				<textarea 
					:value="inputMsg" 
					@keydown.enter.prevent="$emit('send')"
					@paste="$emit('handlePaste', $event)"
					@input="handleInput"
					@focus="isFocused = true"
					@blur="isFocused = false"
					:placeholder="placeholder"
					rows="1"
					ref="inputRef"
					class="zen-textarea"
				></textarea>

				<button v-if="!isGenerating" class="send-btn" :disabled="!canSend" @click="$emit('send')">
					<Send class="icon-send" />
				</button>
				<button v-else class="send-btn stop-btn" @click="$emit('stop')" title="停止生成">
					<Square class="icon-send" />
				</button>
			</div>

			<!-- 拖拽提示遮罩 -->
			<div v-if="isDragging" class="drag-overlay">
				<p>松开鼠标立即上传图片</p>
			</div>
		</div>
		<p class="disclaimer">助手生成的内容可能不准确，请参考系统里的正式文档与报价。</p>
	</footer>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { Image, Send, Square, XCircle } from 'lucide-vue-next'

const props = defineProps({
	inputMsg: {
		type: String,
		default: ''
	},
	selectedImage: {
		type: String,
		default: ''
	},
	isGenerating: {
		type: Boolean,
		default: false
	},
	placeholder: {
		type: String,
		default: '发送消息、粘贴或拖入图片...'
	}
})

const emit = defineEmits(['update:inputMsg', 'send', 'stop', 'triggerUpload', 'removeImage', 'handlePaste', 'handleDrop'])

const isFocused = ref(false)
const isDragging = ref(false)
const inputRef = ref(null)

const canSend = computed(() => Boolean(props.inputMsg.trim() || props.selectedImage))

const handleInput = (e) => {
	emit('update:inputMsg', e.target.value)
	autoGrow()
}

const handleDrop = (e) => {
	isDragging.value = false
	emit('handleDrop', e)
}

const autoGrow = () => {
    nextTick(() => {
        if (!inputRef.value) return
        inputRef.value.style.height = 'auto'
        const targetHeight = Math.min(inputRef.value.scrollHeight, 220)
        inputRef.value.style.height = targetHeight + 'px'
    })
}

// 自动根据值变化调整高度
watch(() => props.inputMsg, (newVal) => {
    if (!newVal) {
        if (inputRef.value) inputRef.value.style.height = 'auto'
    } else {
        autoGrow()
    }
})

// 聚焦功能供父组件调用
defineExpose({
    focus: () => inputRef.value?.focus()
})
</script>

<style scoped>
.chat-footer {
	padding: 24px 32px 32px;
	max-width: 900px;
	margin: 0 auto;
	width: 100%;
}

@media screen and (max-width: 768px) {
	.chat-footer {
		padding: 16px 20px 24px;
	}
}

.input-container {
	position: relative;
	background: rgba(255, 255, 255, 0.9);
	border-radius: 20px;
	padding: 8px 12px;
	border: 1px solid rgba(0, 0, 0, 0.08);
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	box-shadow: 0 10px 40px rgba(0, 0, 0, 0.03);
}

.input-container.is-focused {
	background: #ffffff;
	border-color: #2563eb;
	box-shadow: 0 10px 40px rgba(37, 99, 235, 0.08);
}

.input-container.has-image {
	background: #ecfdf5;
	border-color: #10b981;
}

.input-box {
	display: flex;
	align-items: flex-end;
	gap: 12px;
}

.zen-textarea {
	flex: 1;
	min-height: 44px;
	max-height: 220px;
	background: transparent;
	border: none;
	resize: none;
	padding: 10px 4px;
	font-size: 15px;
	color: #1e293b;
	line-height: 1.5;
}
.zen-textarea:focus {
	outline: none;
}

.upload-pic-btn, .send-btn {
	width: 36px;
	height: 36px;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 10px;
	border: none;
	cursor: pointer;
	transition: all 0.2s;
	flex-shrink: 0;
}

.upload-pic-btn {
	background: transparent;
	color: #64748b;
	margin-bottom: 4px;
}
.upload-pic-btn:hover {
	background: #f1f5f9;
	color: #1e293b;
}

.send-btn {
	background: #e2e8f0;
	color: #94a3b8;
	margin-bottom: 4px;
}
.send-btn.active:not(:disabled), 
.send-btn:not(:disabled) {
	background: #2563eb;
	color: #ffffff;
	box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}

.send-btn.stop-btn {
	background: #ef4444;
	color: #ffffff;
}

.image-preview-area {
	display: flex;
	align-items: center;
	padding: 12px;
	background: #ffffff;
	border-radius: 12px;
	margin-bottom: 8px;
	position: relative;
	width: fit-content;
}

.image-preview {
	width: 60px;
	height: 60px;
	border-radius: 8px;
	object-fit: cover;
	border: 1px solid #e2e8f0;
}

.remove-image-btn {
	position: absolute;
	top: -8px;
	right: -8px;
	background: #ffffff;
	border-radius: 50%;
	padding: 2px;
	display: flex;
	color: #ef4444;
	border: 1px solid #eee;
	cursor: pointer;
}

.drag-overlay {
	position: absolute;
	inset: 0;
	background: rgba(37, 99, 235, 0.9);
	border-radius: 20px;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #ffffff;
	font-weight: 700;
	z-index: 10;
	pointer-events: none;
}

.disclaimer {
	font-size: 11px;
	color: #94a3b8;
	text-align: center;
	margin-top: 12px;
}
</style>
