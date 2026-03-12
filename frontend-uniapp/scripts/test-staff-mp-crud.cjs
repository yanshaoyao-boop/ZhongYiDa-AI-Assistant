const fs = require('node:fs');
const path = require('node:path');

const source = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'admin', 'staff.vue'),
  'utf8'
);

const requiredSnippets = [
  'class="mp-staff-toolbar"',
  '@tap="openCreateUserEditor"',
  '@tap="openStructureManager"',
  'class="mp-staff-editor-card"',
  'class="mp-editor-grid"',
  'class="mp-staff-action danger"',
  "requestStaff('/api/staff/users', {",
  "method: 'POST'",
  "requestStaff(`/api/staff/users/${editingUserId.value}`, {",
  "method: 'PATCH'",
  "method: 'DELETE'",
  "requestStaff('/api/staff/branches', {",
  "requestStaff('/api/staff/departments', {",
  'const showUserEditor = ref(false)',
  'const showStructureManager = ref(false)',
  'const editorMode = ref(',
];

const forbiddenSnippets = [
  'openUserModal = () => {}',
  'openOrgModal = () => {}',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));
const forbidden = forbiddenSnippets.filter((snippet) => source.includes(snippet));

if (missing.length > 0 || forbidden.length > 0) {
  if (missing.length > 0) {
    console.error('staff.vue mp CRUD integration is missing required pieces:\n' + missing.join('\n'));
  }
  if (forbidden.length > 0) {
    console.error('staff.vue still contains placeholder CRUD handlers:\n' + forbidden.join('\n'));
  }
  process.exit(1);
}
