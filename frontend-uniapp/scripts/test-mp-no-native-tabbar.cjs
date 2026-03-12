const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages.json'),
  'utf8'
);

if (source.includes('"tabBar"')) {
  console.error('pages.json should not define a native tabBar when the mini-program uses the custom zen bottom nav.');
  process.exit(1);
}

console.log('pages.json native tabBar is disabled.');
