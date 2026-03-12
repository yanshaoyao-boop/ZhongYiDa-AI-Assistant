const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '<!-- #ifdef MP-WEIXIN -->',
  'class="zen-card zen-card-button"',
  'class="mp-chat-footer"',
  'class="mp-composer-shell"',
  'class="mp-composer-main"',
  'v-model="inputMsg"',
  'const canSendMessage = computed(() => Boolean(inputMsg.value.trim() || selectedImage.value))',
  ":class=\"{ active: canSendMessage }\"",
  ':disabled="!canSendMessage"',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing the MP minimal interaction shell:\n' + missing.join('\n'));
  process.exit(1);
}
