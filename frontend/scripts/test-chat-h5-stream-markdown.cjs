const fs = require('node:fs')
const path = require('node:path')

const source = fs.readFileSync(
  path.join(__dirname, '..', 'src', 'views', 'chat', 'components', 'WebChatMessageItem.vue'),
  'utf8'
)

const requiredSnippets = [
  "import { renderMarkdown } from '@/utils/markdown'",
  "const renderedContent = computed(() => renderMarkdown(props.message?.content || ''))",
]

const forbiddenSnippets = [
  'renderPlainText',
  "if (props.message?.isTyping)",
]

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet))
const forbidden = forbiddenSnippets.filter((snippet) => source.includes(snippet))

if (missing.length > 0 || forbidden.length > 0) {
  const details = [
    ...missing.map((snippet) => `missing -> ${snippet}`),
    ...forbidden.map((snippet) => `forbidden -> ${snippet}`),
  ]
  throw new Error(`WebChatMessageItem streaming markdown regression:\n${details.join('\n')}`)
}

console.log('WebChatMessageItem keeps markdown rendering enabled during streaming')
