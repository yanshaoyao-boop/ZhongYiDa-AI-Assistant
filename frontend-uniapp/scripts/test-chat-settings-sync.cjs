const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const chatSource = fs.readFileSync(path.resolve(root, 'src', 'pages', 'chat', 'chat.vue'), 'utf8');
const authSource = fs.readFileSync(path.resolve(root, 'src', 'store', 'auth.js'), 'utf8');

const requiredChatSnippets = [
  "class=\"sidebar-settings-btn\"",
  'const showSettings = ref(false)',
  "const OUTPUT_LENGTH_KEY = 'zyd_output_length'",
  'const outputLength = ref(',
  'const setOutputLength = (value) => {',
  'buildMessageWithOutputPreference',
  "showSettings.value = true",
  'submitChangePassword',
];

const requiredAuthSnippets = [
  'async changePassword(oldPassword, newPassword) {',
  "/api/auth/change-password",
];

const missing = [];

for (const snippet of requiredChatSnippets) {
  if (!chatSource.includes(snippet)) {
    missing.push(`chat.vue: ${snippet}`);
  }
}

for (const snippet of requiredAuthSnippets) {
  if (!authSource.includes(snippet)) {
    missing.push(`auth.js: ${snippet}`);
  }
}

if (missing.length > 0) {
  console.error('miniapp settings sync is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
