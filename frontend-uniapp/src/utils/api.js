const API_BASE_STORAGE_KEY = 'zyd_api_base_url'

const trimTrailingSlash = (value = '') => value.replace(/\/+$/, '')

const readStoredApiBase = () => {
	try {
		return trimTrailingSlash(uni.getStorageSync(API_BASE_STORAGE_KEY) || '')
	} catch (error) {
		return ''
	}
}

const readEnvApiBase = () => trimTrailingSlash(import.meta.env.VITE_API_BASE_URL || '')
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
	const normalizedPath = path.startsWith('/') ? path : `/${path}`
	const apiBase = getApiBase()
	return apiBase ? `${apiBase}${normalizedPath}` : normalizedPath
}

export const ensureApiBaseConfigured = () => {
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
	const normalizedValue = trimTrailingSlash(String(value || '').trim())
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
