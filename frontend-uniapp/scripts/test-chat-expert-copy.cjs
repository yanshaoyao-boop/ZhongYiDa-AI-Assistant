const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '<text class="zen-title zen-title-expert">专家指导</text>',
  '请描述您遇到的模糊或复杂的问题，我会通过 1-2 轮追问帮你理清思路并提供专业建议。',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue expert welcome copy is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}

const forbiddenSnippets = [
  '适合复杂场景、模糊需求和需要决策建议的对话。',
];

const presentForbidden = forbiddenSnippets.filter((snippet) => source.includes(snippet));

if (presentForbidden.length > 0) {
  console.error('chat.vue expert welcome copy still contains removed text:\n' + presentForbidden.join('\n'));
  process.exit(1);
}
