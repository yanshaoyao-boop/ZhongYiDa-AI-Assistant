const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'login', 'login.vue'),
  'utf8'
);

const requiredSnippets = [
  '<text class="brand-name">小易智能助手</text>',
  '<text class="brand-slogan">链接全球机遇 · 成就每个伙伴</text>',
  'min-height: 960rpx;',
  'width: 320rpx;',
  '.brand-name {',
  'width: 100%;',
  'font-size: 56rpx;',
  'white-space: nowrap;',
  '.brand-slogan {',
  'color: #25539b;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('login.vue hero polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
