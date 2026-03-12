const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="coach-step-pill"',
  'class="zen-level-desc" v-if="!selectedRegion"',
  'class="zen-level-desc" v-else-if="!selectedPersona"',
  'class="zen-level-desc" v-else',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue coach step dedup regression is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}

const forbiddenSnippets = [
  'class="zen-level-text">{{ currentCoachStep }}</text>',
];

const presentForbidden = forbiddenSnippets.filter((snippet) => source.includes(snippet));

if (presentForbidden.length > 0) {
  console.error('chat.vue coach step dedup regression found duplicate step labels:\n' + presentForbidden.join('\n'));
  process.exit(1);
}
