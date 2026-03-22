export const createSseEventParser = () => {
	let buffer = ''
	let sawSseFrame = false

	const buildContentEvent = (content) => ({ type: 'content', content })

	return {
		push(chunk) {
			const text = String(chunk || '')
			if (!text) {
				return { events: [], plainText: '' }
			}

			buffer += text
			const events = []

			while (buffer.includes('\n')) {
				const newlineIndex = buffer.indexOf('\n')
				const rawLine = buffer.slice(0, newlineIndex)
				buffer = buffer.slice(newlineIndex + 1)
				const line = rawLine.replace(/\r$/, '')

				if (!line) {
					// 核心修复：即使行是空的（代表一个原始换行符），也必须作为 content 发送，否则换行会丢失
					if (!sawSseFrame) {
						events.push(buildContentEvent('\n'))
					}
					continue
				}

				if (!line.startsWith('data:')) {
					if (!sawSseFrame) {
						events.push(buildContentEvent(line))
					}
					continue
				}

				sawSseFrame = true
				const payload = line.slice(5).trim()
				if (!payload) continue
				if (payload === '[DONE]') {
					events.push({ type: 'done' })
					continue
				}

				try {
					const data = JSON.parse(payload)
					if (data && typeof data.content === 'string' && data.content) {
						events.push(buildContentEvent(data.content))
					}
				} catch (error) {
					events.push(buildContentEvent(payload))
				}
			}

			if (!sawSseFrame && buffer && !buffer.startsWith('data:')) {
				const plainText = buffer
				buffer = ''
				return { events, plainText }
			}

			return { events, plainText: '' }
		},
		flush() {
			if (!buffer) {
				return { events: [], plainText: '' }
			}
			if (!sawSseFrame) {
				const plainText = buffer
				buffer = ''
				return { events: [], plainText }
			}
			buffer = ''
			return { events: [], plainText: '' }
		},
	}
}
