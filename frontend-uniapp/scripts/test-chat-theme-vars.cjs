const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '.general-mode {',
  '.expert-mode {',
  '.coach-mode {',
  '--bg-primary:',
  '--bg-secondary:',
  '--accent-color:',
  '--text-primary:',
  '--border-color:',
  '.glass-panel {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing required mobile theme foundations:\n' + missing.join('\n'));
  process.exit(1);
}
