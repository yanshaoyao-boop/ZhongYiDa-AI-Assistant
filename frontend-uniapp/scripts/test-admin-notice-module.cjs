const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'admin', 'admin.vue'),
  'utf8'
);

const requiredSnippets = [
  "key: 'notices'",
  "title: '通知管理'",
  "canAccessAdminSection('notices', role, { permissions })",
  "currentActiveTab === 'notices'",
  'v-model="noticeContent"',
  '@tap="sendNotice"',
  'v-for="notice in noticeHistory"',
  '@tap="deleteNotice(notice.id)"',
  "await requestUploadApi('/api/notices/history')",
  "await requestUploadApi('/api/notices/', {",
  'const sendNotice = async () => {',
  'const deleteNotice = async (noticeId) => {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('admin.vue is missing the notice management module:\n' + missing.join('\n'));
  process.exit(1);
}
