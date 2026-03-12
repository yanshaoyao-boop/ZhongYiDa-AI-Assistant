const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'const coachCases = ref([])',
  'const fetchCoachCases = async () =>',
  "resolveApiUrl('/api/upload/coach-cases')",
  'coachCases.value.filter',
  'currentScenario.value = randomCase',
  'fetchCoachCases()',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue coach mode is missing required data wiring:\n' + missing.join('\n'));
  process.exit(1);
}
