const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="composer-status-row"',
  "v-if=\"selectedImage || isGenerating\"",
  'class="composer-status-chip image-ready"',
  'class="composer-status-chip generating"',
  '已附加图片，可直接发送或继续补充文字',
  '正在生成回复，可点击停止按钮中断',
  '.composer-status-row {',
  '.composer-status-chip.image-ready {',
  '.composer-status-chip.generating {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue image/status feedback is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
