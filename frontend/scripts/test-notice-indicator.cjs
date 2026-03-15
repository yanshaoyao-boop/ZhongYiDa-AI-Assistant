const fs = require('node:fs')
const path = require('node:path')

const filePath = path.join(__dirname, '..', 'src', 'views', 'ChatView.vue')
const source = fs.readFileSync(filePath, 'utf8')

const requiredSnippets = [
  'class="mode-btn notice-btn-wrapper"',
  'class="notice-red-dot"',
  '.notice-btn-wrapper {',
  'position: relative;',
  '.notice-red-dot {',
  'animation: noticePulse',
  '@keyframes noticePulse',
]

for (const snippet of requiredSnippets) {
  if (!source.includes(snippet)) {
    throw new Error(`Missing notice indicator snippet: ${snippet}`)
  }
}

console.log('notice indicator styles look correct')
