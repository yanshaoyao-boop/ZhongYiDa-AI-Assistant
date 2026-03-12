const fs = require('node:fs');
const path = require('node:path');

const filePath = path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue');
const source = fs.readFileSync(filePath, 'utf8');

const requiredBindings = [
  'const saveSessions =',
  'const startNewChatWithClose =',
  'const goToAdmin =',
  'const requestCoachEvaluation =',
  'const currentScenario =',
  'const isIntelOpen =',
  'const formatSuccessCriteria =',
];

const missing = requiredBindings.filter((binding) => !source.includes(binding));

if (missing.length > 0) {
  console.error('chat.vue is missing required runtime bindings:\n' + missing.join('\n'));
  process.exit(1);
}
