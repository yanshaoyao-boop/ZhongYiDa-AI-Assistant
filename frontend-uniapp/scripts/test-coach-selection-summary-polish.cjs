const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="coach-selection-summary"',
  'v-if="currentCoachSelections.length"',
  'const currentCoachSelections = computed(() => {',
  '.coach-selection-summary {',
  '.coach-selection-chip {',
  'selectedRegion.value',
  'selectedPersona.value',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue coach selection summary polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
