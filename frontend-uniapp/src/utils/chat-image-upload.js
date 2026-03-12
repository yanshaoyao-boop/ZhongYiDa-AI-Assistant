import { resolveApiUrl } from './api'

const parseUploadResponse = (value) => {
	if (!value) return {}
	if (typeof value === 'string') {
		try {
			return JSON.parse(value)
		} catch (error) {
			return {}
		}
	}
	return value
}

export const uploadChatImage = ({
	filePath,
	token,
	uploadFileImpl,
	urlResolver = resolveApiUrl,
} = {}) => {
	const uploader = uploadFileImpl || uni.uploadFile

	return new Promise((resolve, reject) => {
		uploader({
			url: urlResolver('/api/upload/chat-image'),
			filePath,
			name: 'file',
			header: {
				Authorization: `Bearer ${token}`,
			},
			success: (response) => {
				const payload = parseUploadResponse(response?.data)
				if (response?.statusCode >= 400 || !payload.image_upload_id) {
					reject(new Error(payload.detail || payload.message || `image upload failed (${response?.statusCode || 'unknown'})`))
					return
				}
				resolve(payload)
			},
			fail: (error) => {
				reject(new Error(error?.errMsg || 'image upload failed'))
			},
		})
	})
}
