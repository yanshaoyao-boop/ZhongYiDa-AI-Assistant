const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '.message-list {',
  'padding: 0 24rpx 520rpx;',
  '.message-tail-spacer {',
  'height: 240rpx;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing the MP tail visibility padding:\n' + missing.join('\n'));
  process.exit(1);
}
