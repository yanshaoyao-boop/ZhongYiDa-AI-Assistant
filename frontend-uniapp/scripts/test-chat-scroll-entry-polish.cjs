const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  ':scroll-into-view="scrollIntoViewTarget"',
  'const scrollIntoViewTarget = ref(\'\')',
  'id="chat-bottom-anchor"',
  "scrollIntoViewTarget.value = 'chat-bottom-anchor'",
  ':cursor-spacing="24"',
  ':show-confirm-bar="false"',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue scroll/entry polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
