const fs = require('node:fs');
const path = require('node:path');

const utilSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'utils', 'image-data-url.js'),
  'utf8'
);

const chatSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const utilRequired = [
  'export const MAX_MP_IMAGE_SIZE = 8 * 1024 * 1024',
  'export const validateMpImageSelection = (file = {}) => {',
  'if (file.size > MAX_MP_IMAGE_SIZE) {',
  "return '图片不能超过 8MB'",
];

const chatRequired = [
  "import { validateMpImageSelection } from '@/utils/image-data-url'",
  'const selectedTempFile = res.tempFiles?.[0] || {}',
  'const imageValidationError = validateMpImageSelection(selectedTempFile)',
  "title: imageValidationError",
];

const missing = [
  ...utilRequired.filter((snippet) => !utilSource.includes(snippet)).map((snippet) => `image-data-url.js: ${snippet}`),
  ...chatRequired.filter((snippet) => !chatSource.includes(snippet)).map((snippet) => `chat.vue: ${snippet}`),
];

if (missing.length > 0) {
  console.error('mp image selection guard is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
