const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '.mode-selector {',
  'background: rgba(255, 255, 255, 0.86);',
  'box-shadow: inset 0 0 0 1rpx rgba(226, 232, 240, 0.95);',
  '.mode-selector-pill {',
  'width: auto;',
  'min-width: 0;',
  '.mode-btn {',
  'min-width: 0;',
  'justify-content: center;',
  '.mode-btn.active {',
  'color: var(--accent-color);',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue mode selector polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
