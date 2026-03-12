const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="chat-nav nav-shell glass-panel"',
  'class="sidebar-user-info sidebar-account-card"',
  '.nav-shell {',
  '.sidebar-account-card {',
  '.session-item-shell {',
  ':deep(.markdown-body) {',
  '.assistant .message-content {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue nav/sidebar baseline is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
