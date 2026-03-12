const fs = require('node:fs');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..');
const files = [
  path.join(projectRoot, 'src', 'pages', 'admin', 'chat-logs.vue'),
  path.join(projectRoot, 'src', 'store', 'auth.js'),
];

const violations = [];

for (const file of files) {
  const source = fs.readFileSync(file, 'utf8');
  if (source.includes('zyd_token')) {
    violations.push(path.relative(projectRoot, file));
  }
}

if (violations.length > 0) {
  console.error('Found inconsistent token storage keys:\n' + violations.join('\n'));
  process.exit(1);
}
