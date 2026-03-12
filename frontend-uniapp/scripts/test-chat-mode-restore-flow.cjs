const fs = require('node:fs');
const path = require('node:path');

const chatSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  "const LAST_CHAT_MODE_KEY = 'zyd_last_chat_mode'",
  'const persistLastMode = (mode) => {',
  'const getInitialChatMode = () => {',
  "uni.setStorageSync(LAST_CHAT_MODE_KEY, mode)",
  'const shouldFreshChat = consumePostLoginFreshChatFlag()',
  "const initialMode = shouldFreshChat ? 'general' : getInitialChatMode()",
  'switchMode(initialMode)',
];

const missing = requiredSnippets.filter((snippet) => !chatSource.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue mode restore flow is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
