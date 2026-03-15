const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="zen-welcome-stage expert-stage welcome-centered mode-stage-offset"',
  'class="zen-welcome-stage coach-stage welcome-centered mode-stage-offset"',
  '.mode-stage-offset {',
  'padding-top: 76rpx;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue mode welcome offset regression is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}

const forbiddenSnippets = [
  '供应链优化分析',
  '我有一个关于供应链优化的复杂问题',
];

const presentForbidden = forbiddenSnippets.filter((snippet) => source.includes(snippet));

if (presentForbidden.length > 0) {
  console.error('chat.vue expert stage still contains removed expert shortcut content:\n' + presentForbidden.join('\n'));
  process.exit(1);
}
