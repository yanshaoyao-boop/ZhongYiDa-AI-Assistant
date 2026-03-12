const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="welcome-content welcome-panel welcome-centered"',
  'class="coach-selection-shell"',
  '.welcome-panel {',
  'background: rgba(255, 255, 255, 0.9);',
  '.welcome-centered {',
  'border-radius: 36rpx;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue welcome stage polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
