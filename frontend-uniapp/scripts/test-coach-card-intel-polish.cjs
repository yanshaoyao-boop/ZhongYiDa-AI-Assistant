const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '.card-row {',
  'gap: 18rpx;',
  '.cat-card {',
  'max-width: 360rpx;',
  'border-radius: 28rpx;',
  'box-shadow: 0 16rpx 38rpx rgba(25, 103, 74, 0.08);',
  '.combat-intel-shell {',
  'box-shadow: -24rpx 0 54rpx rgba(25, 103, 74, 0.1);',
  '.intel-section {',
  'background: rgba(255, 255, 255, 0.96);',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue coach card/intel polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
