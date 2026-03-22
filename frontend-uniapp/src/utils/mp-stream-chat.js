import { createUtf8ChunkDecoder } from './chunk-decoder'
import { resolveApiUrl } from './api'

const DEFAULT_CHUNK_TIMEOUT_MS = 20000

const createError = (code, message, extras = {}) => ({
	code,
	message,
	...extras,
})

const isAbortMessage = (value = '') => String(value).toLowerCase().includes('abort')

const isRetryableMessage = (value = '') => {
	const message = String(value).toLowerCase()
	return message.includes('timeout')
		|| message.includes('network')
		|| message.includes('reset')
		|| message.includes('fail')
}

const hasUniRequest = () => typeof uni !== 'undefined' && typeof uni.request === 'function'

export const createMpStreamChatController = (config = {}) => {
	const {
		buildRequestOptions,
		requestImpl,
		fetchImpl,
		urlResolver = resolveApiUrl,
		chunkTimeoutMs = DEFAULT_CHUNK_TIMEOUT_MS,
		retryLimit = 0,
		onRetry,
	} = config

	let isAborted = false
	let activeRequestTask = null
	let activeAbortController = null
	let timeoutId = null
	let activeReject = null

	const clearChunkTimeout = () => {
		if (timeoutId) {
			clearTimeout(timeoutId)
			timeoutId = null
		}
	}

	const resetActiveHandles = () => {
		activeRequestTask = null
		activeAbortController = null
		activeReject = null
		clearChunkTimeout()
	}

	const cancelActiveRequest = () => {
		if (activeRequestTask && typeof activeRequestTask.abort === 'function') {
			activeRequestTask.abort()
		}
		if (activeAbortController) {
			activeAbortController.abort()
		}
	}

	const armChunkTimeout = (reject) => {
		clearChunkTimeout()
		if (!Number.isFinite(chunkTimeoutMs) || chunkTimeoutMs <= 0) {
			return
		}

		timeoutId = setTimeout(() => {
			if (isAborted) return
			cancelActiveRequest()
			reject(createError('STREAM_TIMEOUT', 'Stream timed out'))
		}, chunkTimeoutMs)
	}

	const getRequestOptions = () => {
		const options = buildRequestOptions ? buildRequestOptions() : {}
		return {
			...options,
			url: urlResolver(options.url || ''),
		}
	}

	const runUniRequestAttempt = (options, callbacks) => new Promise((resolve, reject) => {
		const { onStatus, onText } = callbacks
		const decoder = createUtf8ChunkDecoder()
		let settled = false
		let receivedChunk = false
		let timedOut = false

		const resolveOnce = (result) => {
			if (settled) return
			settled = true
			const tail = decoder.flush()
			if (tail && onText) onText(tail)
			resetActiveHandles()
			resolve(result)
		}

		const rejectOnce = (error) => {
			if (settled) return
			settled = true
			resetActiveHandles()
			reject(error)
		}

		activeReject = rejectOnce
		armChunkTimeout((error) => {
			timedOut = true
			rejectOnce(error)
		})

		const requester = requestImpl || uni.request
		activeRequestTask = requester({
			url: options.url,
			method: options.method || 'POST',
			enableChunked: true,
			header: options.header,
			data: options.data,
			success: (response) => {
				if (typeof onStatus === 'function') {
					onStatus(response.statusCode)
				}
				if ((response?.statusCode || 0) >= 400) {
					rejectOnce(createError('REQUEST_FAILED', `HTTP ${response.statusCode}`, {
						retryable: false,
						receivedChunk,
					}))
				}
			},
			fail: (error) => {
				if (timedOut) return
				if (isAborted || isAbortMessage(error?.errMsg)) {
					rejectOnce(createError('STREAM_ABORTED', 'Stream aborted', { cause: error }))
					return
				}
				rejectOnce(createError('REQUEST_FAILED', error?.errMsg || 'Request failed', {
					cause: error,
					retryable: isRetryableMessage(error?.errMsg),
					receivedChunk,
				}))
			},
			complete: () => {
				resolveOnce({ receivedChunk })
			},
		})

		if (activeRequestTask && typeof activeRequestTask.onChunkReceived === 'function') {
			activeRequestTask.onChunkReceived((event) => {
				if (settled || isAborted) return
				receivedChunk = true
				armChunkTimeout((error) => {
					timedOut = true
					rejectOnce(error)
				})
				const text = decoder.push(event.data)
				if (text && typeof onText === 'function') {
					onText(text)
				}
			})
		}
	})

	const runFetchAttempt = (options, callbacks) => new Promise(async (resolve, reject) => {
		const { onStatus, onText } = callbacks
		const resolvedFetch = fetchImpl || (typeof fetch === 'function' ? fetch.bind(globalThis) : null)
		if (!resolvedFetch) {
			reject(createError('REQUEST_FAILED', 'Fetch API is unavailable'))
			return
		}

		const decoder = createUtf8ChunkDecoder()
		let settled = false
		let receivedChunk = false
		let timedOut = false

		const resolveOnce = (result) => {
			if (settled) return
			settled = true
			const tail = decoder.flush()
			if (tail && typeof onText === 'function') {
				onText(tail)
			}
			resetActiveHandles()
			resolve(result)
		}

		const rejectOnce = (error) => {
			if (settled) return
			settled = true
			resetActiveHandles()
			reject(error)
		}

		activeReject = rejectOnce
		activeAbortController = new AbortController()
		armChunkTimeout((error) => {
			timedOut = true
			rejectOnce(error)
		})

		try {
			const response = await resolvedFetch(options.url, {
				method: options.method || 'POST',
				headers: options.header,
				body: options.data ? JSON.stringify(options.data) : undefined,
				signal: activeAbortController.signal,
			})

			if (typeof onStatus === 'function') {
				onStatus(response.status)
			}

			if (!response.ok) {
				rejectOnce(createError('REQUEST_FAILED', `HTTP ${response.status}`, {
					retryable: false,
					receivedChunk,
				}))
				return
			}

			if (!response.body) {
				rejectOnce(createError('REQUEST_FAILED', 'No response body', {
					retryable: false,
					receivedChunk,
				}))
				return
			}

			const reader = response.body.getReader()
			while (!settled) {
				const { value, done } = await reader.read()
				if (done) break
				receivedChunk = true
				armChunkTimeout((error) => {
					timedOut = true
					rejectOnce(error)
				})
				const text = decoder.push(value)
				if (text && typeof onText === 'function') {
					onText(text)
				}
			}

			resolveOnce({ receivedChunk })
		} catch (error) {
			if (timedOut) return
			if (isAborted || error?.name === 'AbortError') {
				rejectOnce(createError('STREAM_ABORTED', 'Stream aborted', { cause: error }))
				return
			}
			rejectOnce(createError('REQUEST_FAILED', error?.message || 'Request failed', {
				cause: error,
				retryable: isRetryableMessage(error?.message),
				receivedChunk,
			}))
		}
	})

	return {
		async start(callbacks = {}) {
			let attempt = 0

			while (attempt <= retryLimit) {
				const options = getRequestOptions()

				try {
					if (requestImpl || hasUniRequest()) {
						return await runUniRequestAttempt(options, callbacks)
					}
					return await runFetchAttempt(options, callbacks)
				} catch (error) {
					const canRetry = !isAborted
						&& error?.code !== 'STREAM_ABORTED'
						&& error?.code !== 'STREAM_TIMEOUT'
						&& error?.retryable
						&& !error?.receivedChunk
						&& attempt < retryLimit

					if (!canRetry) {
						throw error
					}

					attempt += 1
					if (typeof onRetry === 'function') {
						onRetry({ attempt, error })
					}
				}
			}
		},

		abort() {
			if (isAborted) return
			isAborted = true
			cancelActiveRequest()
			if (typeof activeReject === 'function') {
				activeReject(createError('STREAM_ABORTED', 'Stream aborted'))
			} else {
				resetActiveHandles()
			}
		},
	}
}
