const fs = require('node:fs');
const path = require('node:path');

const loginSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'login', 'login.vue'),
  'utf8'
);

const chatSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const loginRequired = [
  "uni.setStorageSync('zyd_post_login_fresh_chat', '1')",
  "uni.setStorageSync('zyd_last_login_username', username.value)",
  "username.value = uni.getStorageSync('zyd_last_login_username') || ''",
];

const chatRequired = [
  "const POST_LOGIN_FRESH_CHAT_KEY = 'zyd_post_login_fresh_chat'",
  'const consumePostLoginFreshChatFlag = () => {',
  'const ensureFreshEntrySession = () => {',
  "startNewChat({ forceCreate: true })",
  'if (shouldFreshChat) {',
];

const missingLogin = loginRequired.filter((snippet) => !loginSource.includes(snippet));
const missingChat = chatRequired.filter((snippet) => !chatSource.includes(snippet));

if (missingLogin.length > 0 || missingChat.length > 0) {
  if (missingLogin.length > 0) {
    console.error('login.vue entry flow is missing required pieces:\n' + missingLogin.join('\n'));
  }
  if (missingChat.length > 0) {
    console.error('chat.vue entry flow is missing required pieces:\n' + missingChat.join('\n'));
  }
  process.exit(1);
}
