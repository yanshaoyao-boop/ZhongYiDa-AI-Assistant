const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const adminAccessSource = fs.readFileSync(
  path.resolve(root, 'src', 'utils', 'admin-access.js'),
  'utf8'
);

const requiredSnippets = [
  'const SECTION_PERMISSION_MAP = {',
  "notices: 'edit_notices'",
  "staff: 'manage_staff'",
  "'chat-logs': 'view_logs'",
  "lab: 'edit_settings'",
  "knowledge: ['edit_knowledge', 'edit_prices', 'edit_cases']",
  'export const getStoredUserPermissions = () => {',
  'const userPermissions = options.permissions || getStoredUserPermissions()',
  'if (requiredPermission) {',
  'return requiredPermission.some((permission) => userPermissions.includes(permission))',
];

const missing = requiredSnippets.filter((snippet) => !adminAccessSource.includes(snippet));

if (missing.length > 0) {
  console.error('admin-access.js is missing permission guard pieces:\n' + missing.join('\n'));
  process.exit(1);
}
