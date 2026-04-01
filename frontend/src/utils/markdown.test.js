import test from 'node:test'
import assert from 'node:assert/strict'

import { renderMarkdown, renderMarkdownToHtml } from './markdown.js'

test('renders markdown without throwing in the local runtime', () => {
  const html = renderMarkdown('核心结论：**ONT8**')

  assert.equal(typeof html, 'string')
  assert.match(html, /ONT8/)
})

test('renders markdown tables into the chat table wrapper', () => {
  const html = renderMarkdown([
    '| 渠道 | 价格 |',
    '| --- | --- |',
    '| 明日之星华东ONT8 | 8.2/KG |',
  ].join('\n'))

  assert.match(html, /chat-table-wrap/)
  assert.match(html, /chat-markdown-table/)
  assert.match(html, /明日之星华东ONT8/)
})

test('removes duplicated ordered-list markers inside list item content', () => {
  const html = renderMarkdownToHtml([
    '1. 1. [Quote]',
    '- Supports live internal quote lookup.',
    '2. 2. [Address]',
    '- Supports remote-area checks.',
  ].join('\n'))

  assert.match(html, /<ol>/)
  assert.doesNotMatch(html, /<li>\s*<\/li>/)
  assert.doesNotMatch(html, /<ol start="2">\s*<li>\s*<ol start="2">/)
  assert.match(html, /<li>\[Quote\]<\/li>/)
  assert.match(html, /<li>\[Address\]<\/li>/)
})
