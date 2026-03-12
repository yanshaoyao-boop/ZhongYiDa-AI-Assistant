const toUint8Array = (chunk) => {
	if (chunk instanceof Uint8Array) return chunk
	if (chunk instanceof ArrayBuffer) return new Uint8Array(chunk)
	if (ArrayBuffer.isView(chunk)) {
		return new Uint8Array(chunk.buffer, chunk.byteOffset, chunk.byteLength)
	}
	return new Uint8Array(0)
}

const concatUint8Arrays = (first, second) => {
	if (first.length === 0) return second
	if (second.length === 0) return first

	const merged = new Uint8Array(first.length + second.length)
	merged.set(first)
	merged.set(second, first.length)
	return merged
}

const getUtf8SequenceLength = (byte) => {
	if ((byte & 0x80) === 0) return 1
	if ((byte & 0xe0) === 0xc0) return 2
	if ((byte & 0xf0) === 0xe0) return 3
	if ((byte & 0xf8) === 0xf0) return 4
	return 1
}

const splitCompleteUtf8Bytes = (bytes) => {
	if (bytes.length === 0) {
		return { complete: bytes, pending: new Uint8Array(0) }
	}

	let index = bytes.length - 1
	while (index >= 0 && (bytes[index] & 0xc0) === 0x80) {
		index -= 1
	}

	if (index < 0) {
		return { complete: new Uint8Array(0), pending: bytes }
	}

	const sequenceLength = getUtf8SequenceLength(bytes[index])
	const availableLength = bytes.length - index

	if (availableLength < sequenceLength) {
		return {
			complete: bytes.slice(0, index),
			pending: bytes.slice(index),
		}
	}

	return {
		complete: bytes,
		pending: new Uint8Array(0),
	}
}

const decodeUtf8Bytes = (bytes) => {
	let result = ''
	for (let index = 0; index < bytes.length;) {
		const byte = bytes[index]

		if ((byte & 0x80) === 0) {
			result += String.fromCharCode(byte)
			index += 1
			continue
		}

		if ((byte & 0xe0) === 0xc0) {
			const codePoint = ((byte & 0x1f) << 6) | (bytes[index + 1] & 0x3f)
			result += String.fromCharCode(codePoint)
			index += 2
			continue
		}

		if ((byte & 0xf0) === 0xe0) {
			const codePoint = ((byte & 0x0f) << 12) | ((bytes[index + 1] & 0x3f) << 6) | (bytes[index + 2] & 0x3f)
			result += String.fromCharCode(codePoint)
			index += 3
			continue
		}

		const codePoint = ((byte & 0x07) << 18)
			| ((bytes[index + 1] & 0x3f) << 12)
			| ((bytes[index + 2] & 0x3f) << 6)
			| (bytes[index + 3] & 0x3f)

		const normalized = codePoint - 0x10000
		result += String.fromCharCode(
			0xd800 + (normalized >> 10),
			0xdc00 + (normalized & 0x3ff)
		)
		index += 4
	}
	return result
}

export const createUtf8ChunkDecoder = () => {
	const textDecoder = typeof TextDecoder !== 'undefined' ? new TextDecoder('utf-8') : null
	let pendingBytes = new Uint8Array(0)

	const decode = (bytes, stream) => {
		if (bytes.length === 0) return ''
		if (textDecoder) {
			return textDecoder.decode(bytes, { stream })
		}
		return decodeUtf8Bytes(bytes)
	}

	return {
		push(chunk) {
			const merged = concatUint8Arrays(pendingBytes, toUint8Array(chunk))
			const { complete, pending } = splitCompleteUtf8Bytes(merged)
			pendingBytes = pending
			return decode(complete, true)
		},
		flush() {
			const tail = pendingBytes
			pendingBytes = new Uint8Array(0)
			return decode(tail, false)
		},
	}
}
