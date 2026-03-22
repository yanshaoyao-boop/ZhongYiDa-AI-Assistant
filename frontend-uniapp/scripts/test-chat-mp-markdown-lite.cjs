const fs = require('node:fs');
const path = require('node:path');

const pageSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const messageItemSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'components', 'ChatMessageItem.vue'),
  'utf8'
);

const pageSnippets = [
  'renderMpMessageBlocks(msg.content)',
  'const sanitizeMpInlineText = (text) => {',
  ".replace(/\\*\\*(.*?)\\*\\*/g, '$1')",
  ".replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '$1')",
  "const orderedMatch = line.match(/^(\\d+)\\.\\s+(.+)$/)",
  "const bulletMatch = line.match(/^[-*+]\\s+(.+)$/)",
  "if (/^([-*_])\\1{2,}$/.test(line)) {",
];

const messageItemSnippets = [
  '<view class="mp-message-rich">',
  'class="mp-message-divider"',
  '.mp-message-rich {',
  '.mp-message-divider {',
];

const missing = [
  ...pageSnippets
    .filter((snippet) => !pageSource.includes(snippet))
    .map((snippet) => `chat.vue: ${snippet}`),
  ...messageItemSnippets
    .filter((snippet) => !messageItemSource.includes(snippet))
    .map((snippet) => `ChatMessageItem.vue: ${snippet}`),
];

if (missing.length > 0) {
  console.error('MP markdown lite renderer pieces are missing:\\n' + missing.join('\\n'));
  process.exit(1);
}
