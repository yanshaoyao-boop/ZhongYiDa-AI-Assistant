import { ref } from 'vue'
import axios from 'axios'

const sleep = (ms) => new Promise((resolve) => {
  setTimeout(resolve, ms)
})

const buildTaskMessage = (fileName, task = {}) => {
  const progress = Number(task.total_chunks) > 0
    ? ` (${task.processed_chunks || 0}/${task.total_chunks})`
    : ''

  if (task.message) {
    return `${fileName}: ${task.message}${progress}`
  }

  return `${fileName}: processing${progress}`
}

const pollUploadTask = async (taskId, fileName) => {
  const maxAttempts = 180
  const pollIntervalMs = 1200

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const response = await axios.get(`/api/upload/tasks/${encodeURIComponent(taskId)}`)
    const task = response.data || {}

    if (task.status === 'success') {
      return task
    }

    if (task.status === 'error') {
      throw new Error(task.error || task.message || `${fileName} processing failed`)
    }

    await sleep(pollIntervalMs)
  }

  throw new Error(`${fileName} processing timed out`)
}

export function useUploader({ url, onSuccess, onError }) {
  const files = ref([])
  const uploading = ref(false)
  const message = ref('')
  const status = ref('')
  const currentIndex = ref(0)
  const isDragging = ref(false)
  const inputRef = ref(null)

  const triggerSelect = () => {
    if (inputRef.value) {
      inputRef.value.click()
    }
  }

  const onSelected = (event) => {
    const selectedFiles = Array.from(event.target.files || [])
    files.value = [...files.value, ...selectedFiles]
    if (event.target) event.target.value = ''
  }

  const onDrop = (event) => {
    isDragging.value = false
    const droppedFiles = Array.from(event.dataTransfer?.files || [])
    files.value = [...files.value, ...droppedFiles]
  }

  const upload = async () => {
    if (files.value.length === 0 || uploading.value) return

    uploading.value = true
    message.value = ''
    status.value = ''

    let successCount = 0
    const errors = []

    for (let i = 0; i < files.value.length; i += 1) {
      currentIndex.value = i
      const file = files.value[i]
      const formData = new FormData()
      formData.append('file', file)

      try {
        message.value = `${file.name}: uploading`
        const response = await axios.post(url, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })

        if (response.data?.task_id) {
          message.value = buildTaskMessage(file.name, response.data)
          const task = await pollUploadTask(response.data.task_id, file.name)
          message.value = buildTaskMessage(file.name, task)
        }

        successCount += 1
      } catch (error) {
        errors.push({ file: file.name, err: error })
      }
    }

    uploading.value = false
    files.value = []
    currentIndex.value = 0

    if (errors.length === 0) {
      message.value = onSuccess ? onSuccess(successCount) : `Uploaded ${successCount} files successfully.`
      status.value = 'success'
      return
    }

    message.value = onError
      ? onError(successCount, errors)
      : `Upload finished with errors. Success: ${successCount}, Failed: ${errors.length}.`
    status.value = 'error'
  }

  return {
    files,
    uploading,
    message,
    status,
    currentIndex,
    isDragging,
    inputRef,
    triggerSelect,
    onSelected,
    onDrop,
    upload,
  }
}
