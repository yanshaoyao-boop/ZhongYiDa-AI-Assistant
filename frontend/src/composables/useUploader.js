import { ref } from 'vue'
import axios from 'axios'

/**
 * 通用文件上传组合式函数
 * @param {Object} options
 * @param {string} options.url - 上传接口路径
 * @param {Function} options.onSuccess - (successCount, errorMessages, responseData[]) => string  返回自定义成功消息
 * @param {Function} [options.onError] - (successCount, errorMessages) => string  返回自定义失败消息（可选）
 */
export function useUploader({ url, onSuccess, onError }) {
    const files = ref([])
    const inputRef = ref(null)
    const uploading = ref(false)
    const message = ref('')
    const status = ref('')  // 'success' | 'error' | 'warning' | ''
    const currentIndex = ref(0)
    const isDragging = ref(false)

    /** 打开文件选择框 */
    const triggerSelect = () => inputRef.value?.click()

    /** 文件选择回调 */
    const onSelected = (e) => {
        files.value = Array.from(e.target.files)
    }

    /** 拖拽放入回调 */
    const onDrop = (e) => {
        isDragging.value = false
        if (e.dataTransfer.files.length > 0) {
            files.value = Array.from(e.dataTransfer.files)
        }
    }

    /** 执行批量上传 */
    const upload = async () => {
        if (files.value.length === 0) return
        uploading.value = true
        message.value = ''
        status.value = ''

        let successCount = 0
        let errorMessages = []
        let responseDataList = []

        for (let i = 0; i < files.value.length; i++) {
            currentIndex.value = i
            const formData = new FormData()
            formData.append('file', files.value[i])
            try {
                const res = await axios.post(url, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                })
                successCount++
                responseDataList.push(res.data)
            } catch (err) {
                errorMessages.push(`${files.value[i].name}: ${err.response?.data?.detail || err.message}`)
            }
        }

        // 由调用方决定显示什么消息和状态
        if (errorMessages.length === 0) {
            status.value = 'success'
            message.value = onSuccess
                ? onSuccess(successCount, [], responseDataList)
                : `成功处理 ${successCount} 份文件。`
        } else if (successCount === 0) {
            status.value = 'error'
            message.value = onError
                ? onError(successCount, errorMessages)
                : `全部处理失败。错误: ${errorMessages.join('; ')}`
        } else {
            // 部分成功
            status.value = 'warning'
            message.value = onError
                ? onError(successCount, errorMessages)
                : `处理完成。成功: ${successCount}，失败: ${errorMessages.length}。`
        }

        files.value = []
        uploading.value = false
    }

    /** 清除消息 */
    const clearMessage = () => {
        message.value = ''
        status.value = ''
    }

    return {
        files,
        inputRef,
        uploading,
        message,
        status,
        currentIndex,
        isDragging,
        triggerSelect,
        onSelected,
        onDrop,
        upload,
        clearMessage
    }
}
