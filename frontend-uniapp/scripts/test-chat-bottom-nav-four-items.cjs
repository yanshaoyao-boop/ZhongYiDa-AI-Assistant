const fs = require('node:fs');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..');
const source = fs.readFileSync(
  path.resolve(projectRoot, 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  "const CHAT_NAV_ICON_SRC = '/static/nav_chat.png'",
  "const NOTICE_NAV_ICON_SRC = '/static/nav_notice.png'",
  "const ADMIN_NAV_ICON_SRC = '/static/nav_admin.png'",
  "@tap=\"switchTab('chat')\"",
  "@tap=\"switchTab('notice')\"",
  "@tap=\"switchTab('admin')\"",
  '.zen-bottom-nav {',
  '.zen-nav-item {',
  'flex: 1;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing the three-item bottom nav baseline:\n' + missing.join('\n'));
  process.exit(1);
}

const forbiddenSnippets = [
  'TOOLS_NAV_ICON_SRC',
  "switchTab('tools')",
  "currentTab === 'tools'",
];

const unexpected = forbiddenSnippets.filter((snippet) => source.includes(snippet));

if (unexpected.length > 0) {
  console.error('chat.vue should not contain tools module snippets in mp nav:\n' + unexpected.join('\n'));
  process.exit(1);
}

const requiredFiles = [
  path.resolve(projectRoot, 'src', 'static', 'nav_chat.png'),
  path.resolve(projectRoot, 'src', 'static', 'nav_admin.png'),
  path.resolve(projectRoot, 'src', 'static', 'nav_notice.png'),
];

const missingFiles = requiredFiles.filter((file) => !fs.existsSync(file));

if (missingFiles.length > 0) {
  console.error('missing bottom nav icon files:\n' + missingFiles.join('\n'));
  process.exit(1);
}
