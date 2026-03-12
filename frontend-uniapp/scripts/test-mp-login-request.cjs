const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'store', 'auth.js'),
  'utf8'
);

const requiredSnippets = [
  'const buildLoginFormPayload =',
  'data: buildLoginFormPayload(username, password)',
  'timeout: 15000',
  "res.data?.detail || '登录失败，请检查账号密码'",
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('auth.js mp login branch is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
