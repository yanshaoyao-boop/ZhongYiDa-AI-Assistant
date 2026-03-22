const fs = require('node:fs')
const path = require('node:path')

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
)

const requiredSnippets = [
  'const sanitizeMpInlineText = (text) => {',
  ".replace(/\\*\\*(.*?)\\*\\*/g, '$1')",
  ".replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '$1')",
  "const orderedMatch = line.match(/^(\\d+)\\.\\s+(.+)$/)",
  "const bulletMatch = line.match(/^[-*+]\\s+(.+)$/)",
  "const tableRowMatch = line.match(/^\\|(.+)\\|$/)",
  "if (/^([-*_])\\1{2,}$/.test(line)) {",
]

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet))

if (missing.length > 0) {
  throw new Error(`chat.vue MP markdown polish is missing:\n${missing.join('\n')}`)
}

console.log('chat.vue MP markdown polish snippets look correct')
