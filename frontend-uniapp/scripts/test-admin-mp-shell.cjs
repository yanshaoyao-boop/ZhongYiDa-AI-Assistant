const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'admin', 'admin.vue'),
  'utf8'
);

const requiredSnippets = [
  '<!-- #ifndef H5 -->',
  'class="mp-admin-page"',
  'class="mp-entry-card"',
  'v-for="entry in adminEntries"',
  'handleEntryTap(entry)',
  "url: '/pages/admin/chat-logs'",
  "url: '/pages/admin/lab'",
  'auth.userName',
];

const forbiddenSnippets = [
  '<view class="not-supported">',
  '后台管理系统仅支持在 PC 浏览器访问',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));
const forbidden = forbiddenSnippets.filter((snippet) => source.includes(snippet));

if (missing.length > 0 || forbidden.length > 0) {
  if (missing.length > 0) {
    console.error('admin.vue mp shell is missing required pieces:\n' + missing.join('\n'));
  }
  if (forbidden.length > 0) {
    console.error('admin.vue still contains forbidden mp placeholder pieces:\n' + forbidden.join('\n'));
  }
  process.exit(1);
}
