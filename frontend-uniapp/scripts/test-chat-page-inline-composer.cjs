const fs = require('fs')
const path = require('path')

const chatPath = path.resolve(__dirname, '../src/pages/chat/chat.vue')
const source = fs.readFileSync(chatPath, 'utf8')

const failures = []

if (source.includes('<ChatMessageInput')) {
  failures.push('chat.vue should not render <ChatMessageInput>; the composer must be inlined for mp-weixin interaction stability.')
}

if (source.includes("import ChatMessageInput from './components/ChatMessageInput.vue'")) {
  failures.push('chat.vue should not import ChatMessageInput after inlining the composer.')
}

if (!source.includes('composerCanSend')) {
  failures.push('chat.vue should define composerCanSend for the inline composer state.')
}

if (failures.length) {
  console.error(failures.join('\n'))
  process.exit(1)
}

console.log('inline composer structure looks correct')
