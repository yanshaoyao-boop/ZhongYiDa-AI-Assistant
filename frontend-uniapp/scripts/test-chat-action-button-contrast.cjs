const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  `class="zen-send-btn"`,
  `>↑</text>`,
  `>■</text>`,
  `.icon-send {`,
  `.zen-send-btn.active .icon-send,`,
  `.zen-send-btn.stop .icon-send {`,
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue action button contrast polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
