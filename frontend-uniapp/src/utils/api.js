const API_BASE_STORAGE_KEY = 'zyd_api_base_url'

const trimTrailingSlash = (value = '') => String(value || '').replace(/\/+$/, '')

const unwrapDuplicatedAbsoluteUrl = (value = '') => {
	let normalizedValue = String(value || '').trim()
	let duplicateIndex = normalizedValue.search(/\/https?:\/\//i)

	while (duplicateIndex >= 0) {
		normalizedValue = normalizedValue.slice(duplicateIndex + 1)
		duplicateIndex = normalizedValue.search(/\/https?:\/\//i)
	}

	return normalizedValue
}

const normalizeApiBase = (value = '') => {
	let normalizedValue = String(value || '').trim()
	if (!normalizedValue) return ''

	normalizedValue = unwrapDuplicatedAbsoluteUrl(normalizedValue)
	normalizedValue = trimTrailingSlash(normalizedValue)
	normalizedValue = normalizedValue.replace(/\/api$/i, '')

	return trimTrailingSlash(normalizedValue)
}

const readStoredApiBase = () => {
	try {
		if (typeof uni === 'undefined' || !uni.getStorageSync) return ''
		return normalizeApiBase(uni.getStorageSync(API_BASE_STORAGE_KEY) || '')
	} catch (error) {
		return ''
	}
}

const readEnvApiBase = () => normalizeApiBase(import.meta.env.VITE_API_BASE_URL || '')
const readMpDevApiBase = () => import.meta.env.DEV ? readEnvApiBase() : ''

export const getApiBase = () => {
	// #ifdef H5
	return readEnvApiBase()
	// #endif
	// #ifndef H5
	return readStoredApiBase() || readEnvApiBase() || readMpDevApiBase()
	// #endif
}

export const resolveApiUrl = (path) => {
	const rawPath = String(path || '').trim()
	if (!rawPath) return ''
	if (/^https?:\/\//i.test(rawPath)) return rawPath

	const normalizedPath = rawPath.startsWith('/') ? rawPath : `/${rawPath}`
	const apiBase = getApiBase()
	return apiBase ? `${apiBase}${normalizedPath}` : normalizedPath
}

export const ensureApiBaseConfigured = () => {
	const envBase = readEnvApiBase()
	if (envBase) {
		try {
			uni.setStorageSync(API_BASE_STORAGE_KEY, envBase)
		} catch (error) {}
		return envBase
	}

	const currentStoredBase = readStoredApiBase()
	if (currentStoredBase) {
		return currentStoredBase
	}

	const apiBase = getApiBase()
	if (apiBase) {
		try {
			uni.setStorageSync(API_BASE_STORAGE_KEY, apiBase)
		} catch (error) {
			return apiBase
		}
	}

	return apiBase
}

export const setApiBase = (value) => {
	const normalizedValue = normalizeApiBase(value)

	try {
		if (normalizedValue) {
			uni.setStorageSync(API_BASE_STORAGE_KEY, normalizedValue)
		} else {
			uni.removeStorageSync(API_BASE_STORAGE_KEY)
		}
	} catch (error) {}

	return normalizedValue
}

export const clearApiBase = () => {
	try {
		uni.removeStorageSync(API_BASE_STORAGE_KEY)
	} catch (error) {}

	return readEnvApiBase() || readMpDevApiBase()
}

export const isLoopbackApiBase = (value = '') => {
	const normalizedValue = String(value || '').trim().toLowerCase()
	return normalizedValue.includes('127.0.0.1') || normalizedValue.includes('localhost')
}

export { API_BASE_STORAGE_KEY }
