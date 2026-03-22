const fs = require('node:fs')
const path = require('node:path')

const chatViewSource = fs.readFileSync(path.join(__dirname, '..', 'src', 'views', 'ChatView.vue'), 'utf8')
const messageItemSource = fs.readFileSync(
  path.join(__dirname, '..', 'src', 'views', 'chat', 'components', 'WebChatMessageItem.vue'),
  'utf8'
)

const requiredChatViewSnippets = [
  "const openToolsCenter = () => {",
  "router.push('/tools')",
  "const personalizedWelcomeMsg = computed(() =>",
  'auth.userName',
  ':welcome-msg="personalizedWelcomeMsg"',
  'const getMessageById = (id) =>',
]

const requiredMessageItemSnippets = [
  "import { computed } from 'vue'",
  "import { renderMarkdown",
  'message.isTyping',
  'computed(() =>',
]

const missing = [
  ...requiredChatViewSnippets
    .filter((snippet) => !chatViewSource.includes(snippet))
    .map((snippet) => `ChatView.vue -> ${snippet}`),
  ...requiredMessageItemSnippets
    .filter((snippet) => !messageItemSource.includes(snippet))
    .map((snippet) => `WebChatMessageItem.vue -> ${snippet}`),
]

if (chatViewSource.includes(':rendered-content="renderMarkdown(msg.content)"')) {
  missing.push('ChatView.vue -> should stop rendering markdown inline in the parent v-for')
}

if (chatViewSource.includes('aiMsg.content +=')) {
  missing.push('ChatView.vue -> should not mutate the raw aiMsg object during streaming')
}

if (missing.length > 0) {
  throw new Error(`H5 chat/tool integration is missing expected pieces:\n${missing.join('\n')}`)
}

console.log('H5 chat tools/welcome/streaming snippets look correct')
