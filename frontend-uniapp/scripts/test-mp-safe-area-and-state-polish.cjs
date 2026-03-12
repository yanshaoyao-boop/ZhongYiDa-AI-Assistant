const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');

const checks = [
  {
    file: path.join(root, 'src', 'pages', 'chat', 'chat.vue'),
    snippets: [
      'safe-area-inset-bottom',
      '.chat-footer {',
    ],
  },
  {
    file: path.join(root, 'src', 'pages', 'admin', 'admin.vue'),
    snippets: [
      'safe-area-inset-bottom',
      '.mp-admin-page {',
    ],
  },
  {
    file: path.join(root, 'src', 'pages', 'admin', 'chat-logs.vue'),
    snippets: [
      'safe-area-inset-bottom',
      'class="mp-state-title"',
      'class="mp-state-hint"',
    ],
  },
  {
    file: path.join(root, 'src', 'pages', 'admin', 'lab.vue'),
    snippets: [
      'safe-area-inset-bottom',
      '.mp-lab-page {',
    ],
  },
  {
    file: path.join(root, 'src', 'pages', 'admin', 'staff.vue'),
    snippets: [
      'safe-area-inset-bottom',
      'class="mp-staff-state-title"',
      'class="mp-staff-state-hint"',
    ],
  },
];

const missing = [];

for (const check of checks) {
  const source = fs.readFileSync(check.file, 'utf8');
  const absent = check.snippets.filter((snippet) => !source.includes(snippet));

  if (absent.length > 0) {
    missing.push(`${path.basename(check.file)}:\n${absent.join('\n')}`);
  }
}

if (missing.length > 0) {
  console.error('mini-program safe-area/state polish is missing required pieces:\n' + missing.join('\n\n'));
  process.exit(1);
}
