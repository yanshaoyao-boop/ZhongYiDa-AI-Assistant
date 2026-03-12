import { resolveApiUrl } from './api'

const CLIENT_LOG_QUEUE_KEY = 'zyd_client_log_queue'
const CLIENT_LOG_ENDPOINT = '/api/client-logs'
const MAX_QUEUE_SIZE = 50

let transportRequest = null
let flushPromise = null

const safeJson = (value) => {
  try {
    return JSON.parse(JSON.stringify(value))
  } catch (error) {
    return {
      serializationError: error?.message || 'serialization failed',
    }
  }
}

const nowIso = () => new Date().toISOString()

const readQueue = () => {
  try {
    const raw = uni.getStorageSync(CLIENT_LOG_QUEUE_KEY)
    if (!raw) return []
    if (Array.isArray(raw)) return raw
    return JSON.parse(raw)
  } catch (error) {
    return []
  }
}

const writeQueue = (entries) => {
  try {
    uni.setStorageSync(CLIENT_LOG_QUEUE_KEY, JSON.stringify(entries.slice(-MAX_QUEUE_SIZE)))
  } catch (error) {}
}

const getCurrentPagePath = () => {
  try {
    const pages = getCurrentPages()
    return pages[pages.length - 1]?.route ? `/${pages[pages.length - 1].route}` : ''
  } catch (error) {
    return ''
  }
}

const createEntry = (entry = {}) => ({
  level: entry.level || 'error',
  type: entry.type || 'app-error',
  message: String(entry.message || 'unknown error'),
  page: entry.page || getCurrentPagePath(),
  context: safeJson(entry.context || {}),
  timestamp: entry.timestamp || nowIso(),
})

export const persistClientLog = (entry) => {
  const queue = readQueue()
  queue.push(createEntry(entry))
  writeQueue(queue)
}

export const flushClientLogs = () => {
  if (!transportRequest) {
    return Promise.resolve(false)
  }

  if (flushPromise) {
    return flushPromise
  }

  const entries = readQueue()
  if (!entries.length) {
    return Promise.resolve(true)
  }

  flushPromise = new Promise((resolve) => {
    transportRequest({
      url: resolveApiUrl(CLIENT_LOG_ENDPOINT),
      method: 'POST',
      header: {
        'content-type': 'application/json',
      },
      data: { entries },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          writeQueue([])
          resolve(true)
          return
        }
        resolve(false)
      },
      fail: () => resolve(false),
      complete: () => {
        flushPromise = null
      },
    })
  })

  return flushPromise
}

const shouldSkipLogging = (url = '') => String(url || '').includes(CLIENT_LOG_ENDPOINT)

const reportClientLog = (entry) => {
  persistClientLog(entry)
  void flushClientLogs()
}

export const captureClientEvent = (entry = {}) => {
  reportClientLog({
    level: entry.level || 'info',
    type: entry.type || 'client-event',
    message: entry.message || entry.type || 'client event',
    page: entry.page,
    context: entry.context || {},
    timestamp: entry.timestamp,
  })
}

const normalizeRequestUrl = (options = {}) => {
  if (typeof options === 'string') return options
  return options.url || ''
}

const wrapRequestOptions = (options, originalRequest) => {
  if (!options || typeof options !== 'object') {
    return options
  }

  const requestUrl = normalizeRequestUrl(options)
  if (shouldSkipLogging(requestUrl)) {
    return options
  }

  const startedAt = Date.now()
  const originalSuccess = options.success
  const originalFail = options.fail

  return {
    ...options,
    success: (res) => {
      if (res?.statusCode >= 400) {
        reportClientLog({
          level: 'warn',
          type: 'request-error',
          message: `request failed (${res.statusCode})`,
          context: {
            url: requestUrl,
            method: options.method || 'GET',
            duration_ms: Date.now() - startedAt,
            status_code: res.statusCode,
          },
        })
      }
      if (typeof originalSuccess === 'function') {
        originalSuccess(res)
      }
    },
    fail: (error) => {
      reportClientLog({
        level: 'error',
        type: 'request-fail',
        message: error?.errMsg || 'request failed',
        context: {
          url: requestUrl,
          method: options.method || 'GET',
          duration_ms: Date.now() - startedAt,
        },
      })
      if (typeof originalFail === 'function') {
        originalFail(error)
      }
    },
  }
}

const createLoggedRequest = (originalRequest) => (options) => {
  return originalRequest(wrapRequestOptions(options, originalRequest))
}

export const captureAppError = (error, context = {}) => {
  captureClientEvent({
    level: 'error',
    type: 'app-error',
    message: error?.message || String(error || 'app error'),
    context,
  })
}

export const captureUnhandledRejection = (event) => {
  const reason = event?.reason
  captureClientEvent({
    level: 'error',
    type: 'unhandled-rejection',
    message: reason?.message || String(reason || 'unhandled rejection'),
    context: {
      reason: safeJson(reason),
    },
  })
}

export const installGlobalErrorLogging = () => {
  if (typeof uni === 'undefined' || typeof uni.request !== 'function') {
    return
  }

  if (!transportRequest) {
    const originalRequest = uni.request.bind(uni)
    transportRequest = originalRequest
    uni.request = createLoggedRequest(originalRequest)
  }

  void flushClientLogs()
}
