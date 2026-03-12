const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="cat-desc"',
  'class="coach-helper-chip"',
  "presetMsg('常见物流基础名词讲解')",
  '.cat-desc {',
  '.coach-helper-chip {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue coach baseline UI is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
