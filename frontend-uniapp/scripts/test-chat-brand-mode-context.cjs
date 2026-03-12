const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'const currentBrandMode = computed(() => {',
  'general: { label:',
  'coach: { label:',
  'expert: { label:',
  "const welcomeMsg = ref('",
  '.mode-btn.active .tab-text {',
  'color: var(--accent-color);',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue brand mode context is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
