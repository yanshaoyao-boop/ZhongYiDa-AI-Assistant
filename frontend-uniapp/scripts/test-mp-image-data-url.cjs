const fs = require('node:fs');
const path = require('node:path');

const utilSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'utils', 'image-data-url.js'),
  'utf8'
);

const utilRequired = [
  'export const inferImageMimeType = (filePath = \'\') => {',
  "case '.jpg':",
  "case '.jpeg':",
  "case '.webp':",
  "return `data:${inferImageMimeType(filePath)};base64,${base64}`",
];

const missing = utilRequired
  .filter((snippet) => !utilSource.includes(snippet))
  .map((snippet) => `image-data-url.js: ${snippet}`);

if (missing.length > 0) {
  console.error('mp image data url utility is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
