const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '.sidebar {',
  'box-shadow: 24rpx 0 54rpx rgba(15, 23, 42, 0.08);',
  '.session-item-shell {',
  'background: rgba(255, 255, 255, 0.7);',
  '.nav-shell {',
  'background: rgba(255, 255, 255, 0.97);',
  '.chat-nav {',
  'padding: 16rpx 20rpx 12rpx;',
  '.sidebar-account-card {',
  'background: rgba(255, 255, 255, 0.92);',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue nav/sidebar polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
