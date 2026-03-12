const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'renderMpMessageBlocks(msg.content)',
  'const sanitizeMpInlineText = (text) => {',
  ".replace(/\\*\\*(.*?)\\*\\*/g, '$1')",
  ".replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '$1')",
  "const orderedMatch = line.match(/^(\\d+)\\.\\s+(.+)$/)",
  "const bulletMatch = line.match(/^[-*+]\\s+(.+)$/)",
  "if (/^([-*_])\\1{2,}$/.test(line)) {",
  ".mp-message-rich {",
  '.mp-message-divider {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing the MP markdown lite renderer pieces:\\n' + missing.join('\\n'));
  process.exit(1);
}
