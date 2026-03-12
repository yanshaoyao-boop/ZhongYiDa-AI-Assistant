const FALLBACK_IMAGE_MIME = 'image/png'
export const MAX_MP_IMAGE_SIZE = 8 * 1024 * 1024

export const inferImageMimeType = (filePath = '') => {
	const normalized = String(filePath || '').toLowerCase()
	const extension = normalized.includes('.') ? normalized.slice(normalized.lastIndexOf('.')) : ''

	switch (extension) {
		case '.jpg':
		case '.jpeg':
			return 'image/jpeg'
		case '.webp':
			return 'image/webp'
		case '.gif':
			return 'image/gif'
		default:
			return FALLBACK_IMAGE_MIME
	}
}

export const buildImageDataUrl = (filePath, base64) => {
	return `data:${inferImageMimeType(filePath)};base64,${base64}`
}

export const validateMpImageSelection = (file = {}) => {
	if (file.size > MAX_MP_IMAGE_SIZE) {
		return '图片不能超过 8MB'
	}

	return ''
}
