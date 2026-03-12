const fs = require('node:fs');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..');
const files = [
  path.join(projectRoot, 'src', 'store', 'auth.js'),
  path.join(projectRoot, 'src', 'pages', 'chat', 'chat.vue'),
];

const forbiddenSnippets = [
  "const BASE_URL = ''",
  "const API_BASE = ''",
];

const violations = [];

for (const file of files) {
  const source = fs.readFileSync(file, 'utf8');
  for (const snippet of forbiddenSnippets) {
    if (source.includes(snippet)) {
      violations.push(`${path.relative(projectRoot, file)} -> ${snippet}`);
    }
  }
}

if (violations.length > 0) {
  console.error('Found hard-coded empty API base definitions:\n' + violations.join('\n'));
  process.exit(1);
}
