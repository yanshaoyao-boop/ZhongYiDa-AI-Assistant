const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  '.gradient-text {',
  'color: var(--accent-color);',
  '.coach-mode .new-chat-btn,',
  '.coach-mode .sidebar-admin-btn,',
  '.coach-mode .user-avatar-sidebar {',
  '.coach-mode .session-item.active {',
  '.expert-mode .new-chat-btn,',
  '.expert-mode .sidebar-admin-btn,',
  '.expert-mode .user-avatar-sidebar {',
  '.expert-mode .session-item.active {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue mode theme polish is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
