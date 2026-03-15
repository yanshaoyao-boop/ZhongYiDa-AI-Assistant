const fs = require('node:fs');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..');
const source = fs.readFileSync(
  path.resolve(projectRoot, 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  "const SEND_ICON_SRC = '/static/send.png'",
  '<image class="icon-send-image" :src="SEND_ICON_SRC" mode="aspectFit" />',
  '.icon-send-image {',
  '.chat-nav {',
  'position: fixed;',
  'top: 0;',
  '.main-body-wrapper {',
  'padding-top: calc(132rpx + env(safe-area-inset-top));',
  '@media screen and (min-width: 768px) {',
  '.chat-nav {',
  'position: static;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing the fixed nav / send icon refresh:\n' + missing.join('\n'));
  process.exit(1);
}

const requiredFiles = [
  path.resolve(projectRoot, 'src', 'static', 'send.png'),
];

const missingFiles = requiredFiles.filter((file) => !fs.existsSync(file));

if (missingFiles.length > 0) {
  console.error('missing send icon files:\n' + missingFiles.join('\n'));
  process.exit(1);
}
