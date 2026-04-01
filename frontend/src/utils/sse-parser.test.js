import test from 'node:test'
import assert from 'node:assert/strict'

import { createSseEventParser } from './sse-parser.js'

test('preserves line breaks for plain text markdown tables', () => {
  const parser = createSseEventParser()
  const input = [
    '结论：先看报价',
    '',
    '| 渠道 | 单价 |',
    '| --- | --- |',
    '| ONT8快船 | 9.5 |',
    '| ONT8普船 | 4.3 |',
    '',
  ].join('\n')

  const pushed = parser.push(input)
  const flushed = parser.flush()
  const combined = [
    ...pushed.events.filter((event) => event.type === 'content').map((event) => event.content),
    pushed.plainText,
    flushed.plainText,
  ].join('')

  assert.equal(combined, input)
})
