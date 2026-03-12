const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  `:placeholder="selectedImage ? '补充图片说明，或直接发送...' : '发送消息、粘贴或拖入图片...'"`,
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue image placeholder polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
