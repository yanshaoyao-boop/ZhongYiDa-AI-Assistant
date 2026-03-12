const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'admin', 'lab.vue'),
  'utf8'
);

const requiredSnippets = [
  'const loading = ref(false)',
  "const syncStatus = ref('idle')",
  "const lastSyncedAt = ref('')",
  'const hasPendingChanges = computed(() =>',
  'class="mp-sync-banner"',
  'class="mp-sync-banner__meta"',
  ":disabled=\"saving || loading || !hasPendingChanges\"",
  'loading.value = true',
  "syncStatus.value = 'dirty'",
  "syncStatus.value = 'saved'",
  'lastSyncedAt.value = formatSyncTime(new Date())',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('lab.vue mp state integration is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
