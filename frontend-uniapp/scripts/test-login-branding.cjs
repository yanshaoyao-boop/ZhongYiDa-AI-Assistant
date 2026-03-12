const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'login', 'login.vue'),
  'utf8'
);

if (!source.includes('/static/zyd_logo.png')) {
  console.error('Expected login.vue to use /static/zyd_logo.png.');
  process.exit(1);
}

if (source.includes('/static/logo.png')) {
  console.error('login.vue should no longer use /static/logo.png.');
  process.exit(1);
}
