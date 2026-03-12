const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="suggestion-chips suggestion-chip-shell"',
  '.suggestion-chip-shell {',
  'background: rgba(248, 250, 252, 0.78);',
  '.suggestion-chips {',
  'gap: 18rpx;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue welcome kicker polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
