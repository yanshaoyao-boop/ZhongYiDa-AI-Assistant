const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="welcome-stage"',
  'class="message-body message-content"',
  'class="input-shell input-container"',
  'max-width: 920rpx;',
  'max-width: 860rpx;',
  'background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);',
  'box-shadow: 0 24rpx 50rpx rgba(37, 99, 235, 0.14);',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue message/composer baseline is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
