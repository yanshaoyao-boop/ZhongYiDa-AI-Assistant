const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');

const checks = [
  {
    file: path.join(root, 'src', 'utils', 'admin-access.js'),
    snippets: [
      'const SUPER_ADMIN_ONLY_SECTIONS = new Set([\'chat-logs\', \'lab\'])',
      'export const canAccessAdminSection = (section, role) => {',
      'export const ensureAdminPageAccess = (section, options = {}) => {',
      "uni.showToast({ title: '当前账号无权访问该页面', icon: 'none' })",
    ],
  },
  {
    file: path.join(root, 'src', 'pages', 'admin', 'admin.vue'),
    snippets: [
      'const adminEntries = computed(() => {',
      "auth.isSuperAdmin ? 'super_admin' : auth.isAdmin ? 'branch_admin' : ''",
      "canAccessAdminSection('chat-logs', role)",
      "canAccessAdminSection('lab', role)",
      "canAccessAdminSection('staff', role)",
      "ensureAdminPageAccess('admin'",
    ],
  },
  {
    file: path.join(root, 'src', 'pages', 'admin', 'chat-logs.vue'),
    snippets: [
      "ensureAdminPageAccess('chat-logs'",
    ],
  },
  {
    file: path.join(root, 'src', 'pages', 'admin', 'lab.vue'),
    snippets: [
      "ensureAdminPageAccess('lab'",
    ],
  },
  {
    file: path.join(root, 'src', 'pages', 'admin', 'staff.vue'),
    snippets: [
      "ensureAdminPageAccess('staff'",
    ],
  },
];

const failures = [];

for (const check of checks) {
  const source = fs.readFileSync(check.file, 'utf8');
  const missing = check.snippets.filter((snippet) => !source.includes(snippet));
  if (missing.length > 0) {
    failures.push(`${path.basename(check.file)}:\n${missing.join('\n')}`);
  }
}

if (failures.length > 0) {
  console.error('admin role guards are missing required pieces:\n' + failures.join('\n\n'));
  process.exit(1);
}
