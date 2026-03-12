const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'login', 'login.vue'),
  'utf8'
);

const requiredSnippets = [
  'background: linear-gradient(180deg, #edf3fb 0%, #e8eef7 100%);',
  'max-width: 400px;',
  'border-radius: 28px;',
  'height: 54px;',
  'border-radius: 16px;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('login.vue is missing required baseline layout styles:\n' + missing.join('\n'));
  process.exit(1);
}
