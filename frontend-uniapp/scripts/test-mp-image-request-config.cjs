const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'createMpStreamChatController({',
  'header: {',
  'Authorization: `Bearer ${auth.token}`',
  "'content-type': 'application/json'",
  'image_upload_id: currentImageUploadId',
  'image_base64: currentImageBase64',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue mp request config is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
