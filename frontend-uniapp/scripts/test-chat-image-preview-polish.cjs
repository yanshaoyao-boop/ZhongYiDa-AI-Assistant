const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="image-preview-frame"',
  '@tap="previewImage(selectedImage)"',
  'class="image-preview-meta"',
  'class="image-preview-chip"',
  '.image-preview-frame {',
  '.image-preview-meta {',
  '.image-preview-chip {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue image preview polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
