const fs = require('node:fs');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..');
const source = fs.readFileSync(
  path.resolve(projectRoot, 'src', 'pages', 'chat', 'chat.vue'),
  'utf8'
);

const requiredSnippets = [
  "const XIAOYI_AVATAR_SRC = '/static/xiaoyi_character.png'",
  '<image :src="XIAOYI_AVATAR_SRC" mode="aspectFit" class="zen-avatar-img" />',
  '<image v-if="msg.role === \'assistant\'" :src="XIAOYI_AVATAR_SRC" class="xiaoyi-avatar" />',
  "const CHAT_NAV_ICON_SRC = '/static/nav_chat.png'",
  "const ADMIN_NAV_ICON_SRC = '/static/nav_admin.png'",
  '<image class="zen-nav-icon-image" :class="{ active: currentTab === \'chat\' }" :src="CHAT_NAV_ICON_SRC" mode="aspectFit" />',
  '<image class="zen-nav-icon-image" :class="{ active: currentTab === \'admin\' }" :src="ADMIN_NAV_ICON_SRC" mode="aspectFit" />',
  '.zen-nav-icon-image {',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue is missing the avatar/nav icon refresh:\n' + missing.join('\n'));
  process.exit(1);
}

const requiredFiles = [
  path.resolve(projectRoot, 'static', 'xiaoyi_character.png'),
  path.resolve(projectRoot, 'static', 'nav_chat.png'),
  path.resolve(projectRoot, 'static', 'nav_admin.png'),
];

const missingFiles = requiredFiles.filter((file) => !fs.existsSync(file));

if (missingFiles.length > 0) {
  console.error('missing static avatar/nav icon files:\n' + missingFiles.join('\n'));
  process.exit(1);
}
