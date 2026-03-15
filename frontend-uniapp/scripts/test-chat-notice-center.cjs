const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  "const NOTICE_SEEN_STORAGE_KEY = 'zyd_notice_last_seen_id'",
  "const showNoticeCenter = ref(false)",
  "const noticeTab = ref('current')",
  'const hasUnreadNotices = ref(false)',
  "const openNoticeCenter = async () => {",
  "const fetchCurrentNotices = async ({ markAsRead = false } = {}) => {",
  "const fetchNoticeHistory = async () => {",
  "if (tab === 'notice') {",
  'openNoticeCenter()',
  'class="zen-nav-badge"',
  '<text class="notice-center-title">重要通知</text>',
  "@tap=\"noticeTab = 'current'\"",
  "@tap=\"noticeTab = 'history'\"",
  "v-for=\"notice in displayNotices\"",
  'class="notice-center-overlay"',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing the notice center pieces:\n' + missing.join('\n'));
  process.exit(1);
}
