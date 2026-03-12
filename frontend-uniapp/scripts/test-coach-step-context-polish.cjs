const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="coach-step-pill"',
  'const currentCoachStep = computed(() => {',
  "return '第一步 · 选择实战航线'",
  "return '第二步 · 选择客户背景'",
  "return '第三步 · 选择练习科目'",
  '.coach-step-pill {',
  'background: rgba(255, 255, 255, 0.76);',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue coach step context polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
