const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '.chat-nav {',
  'justify-content: space-between;',
  '.nav-left {',
  'position: relative;',
  '.nav-right-spacer {',
  'display: block;',
  '.mode-selector-pill {',
  'width: auto;',
  'min-width: 0;',
  '.zen-footer-wrapper {',
  'bottom: calc(128rpx + env(safe-area-inset-bottom));',
  '.zen-floating-pill {',
  'padding: 12rpx 16rpx;',
  '.zen-send-btn {',
  'width: 72rpx;',
  'height: 72rpx;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue mini-program shell regression is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
