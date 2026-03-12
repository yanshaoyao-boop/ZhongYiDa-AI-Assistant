const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  `:class="{ 'has-attachment': selectedImage }"`,
  '.input-container.has-image {',
  '.upload-pic-btn.has-attachment {',
  'border-color: rgba(37, 99, 235, 0.24);',
  'background: rgba(239, 246, 255, 0.96);',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue attachment state polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
