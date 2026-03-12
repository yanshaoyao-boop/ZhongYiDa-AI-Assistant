const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  `color="selectedImage ? '#2563eb' : '#64748b'"`,
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue upload icon state polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
