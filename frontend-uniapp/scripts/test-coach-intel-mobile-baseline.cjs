const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="coach-selection coach-selection-shell"',
  'class="cat-copy"',
  "'combat-intel-shell'",
  'class="intel-section intel-section-highlight"',
  'flex-direction: row;',
  '.cat-copy {',
  '.combat-intel-shell {',
  '.intel-section-highlight {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue coach/intel mobile baseline is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
