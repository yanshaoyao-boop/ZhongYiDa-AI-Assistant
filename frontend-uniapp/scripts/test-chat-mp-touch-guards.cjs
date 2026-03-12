const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '.sidebar {',
  'pointer-events: none;',
  '.sidebar.show {',
  'pointer-events: auto;',
  '.combat-intel-panel {',
  '.combat-intel-panel.show {',
  '@input="handleComposerInput"',
  'const handleComposerInput = (event) => {',
  "inputMsg.value = event?.detail?.value || ''",
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing required mini-program touch guards:\n' + missing.join('\n'));
  process.exit(1);
}
