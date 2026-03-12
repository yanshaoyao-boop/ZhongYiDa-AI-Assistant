const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '<!-- #ifdef MP-WEIXIN -->',
  '<view class="mp-message-rich">',
  'renderMpMessageBlocks(msg.content)',
  '<!-- #ifndef MP-WEIXIN -->',
  '<rich-text class="markdown-body" :nodes="renderMarkdown(msg.content)"></rich-text>',
  '.mp-message-line-text {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing the MP message render fallback:\n' + missing.join('\n'));
  process.exit(1);
}
