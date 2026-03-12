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
  '.login-container::before {',
  'max-width: 372px;',
  'box-shadow: 0 24px 56px rgba(77, 102, 161, 0.12);',
  'width: 154px;',
];

const chatRequired = [
  '.welcome-content {',
  'max-width: 760rpx;',
  '.suggestion-chips {',
  'gap: 18rpx;',
  '.chip {',
  'min-height: 80rpx;',
];

const missing = [
  ...loginRequired.filter((snippet) => !loginSource.includes(snippet)).map((snippet) => `login.vue: ${snippet}`),
  ...chatRequired.filter((snippet) => !chatSource.includes(snippet)).map((snippet) => `chat.vue: ${snippet}`),
];

if (missing.length > 0) {
  console.error('login/chat baseline polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
