const fs = require('node:fs');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..');
const source = fs.readFileSync(
  path.resolve(projectRoot, 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  "const NOTICE_NAV_ICON_SRC = '/static/nav_notice.png'",
  "const TOOLS_NAV_ICON_SRC = '/static/nav_tools.png'",
  "@tap=\"switchTab('notice')\"",
  "@tap=\"switchTab('tools')\"",
  '<text class="zen-nav-label">通知</text>',
  '<text class="zen-nav-label">工具</text>',
  '.zen-bottom-nav {',
  'justify-content: space-between;',
  'flex: 1;',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing the four-item bottom nav update:\n' + missing.join('\n'));
  process.exit(1);
}

const requiredFiles = [
  path.resolve(projectRoot, 'src', 'static', 'nav_chat.png'),
  path.resolve(projectRoot, 'src', 'static', 'nav_admin.png'),
  path.resolve(projectRoot, 'src', 'static', 'nav_notice.png'),
  path.resolve(projectRoot, 'src', 'static', 'nav_tools.png'),
];

const missingFiles = requiredFiles.filter((file) => !fs.existsSync(file));

if (missingFiles.length > 0) {
  console.error('missing bottom nav icon files:\n' + missingFiles.join('\n'));
  process.exit(1);
}
