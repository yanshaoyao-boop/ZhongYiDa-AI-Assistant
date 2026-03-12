const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '.message-wrapper {',
  'margin-bottom: 28rpx;',
  'gap: 16rpx;',
  '.xiaoyi-avatar {',
  'width: 64rpx;',
  '.user-avatar {',
  'width: 64rpx;',
  '.message-content {',
  'max-width: 76%;',
  'border-radius: 22rpx;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue message area polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
