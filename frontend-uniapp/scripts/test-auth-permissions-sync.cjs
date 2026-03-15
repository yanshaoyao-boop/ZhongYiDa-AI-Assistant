const fs = require('node:fs');
const path = require('node:path');

const uniappRoot = path.resolve(__dirname, '..');
const authStoreSource = fs.readFileSync(
  path.resolve(uniappRoot, 'src', 'store', 'auth.js'),
  'utf8'
);
const adminAccessSource = fs.readFileSync(
  path.resolve(uniappRoot, 'src', 'utils', 'admin-access.js'),
  'utf8'
);
const webAuthSource = fs.readFileSync(
  path.resolve(uniappRoot, '..', 'frontend', 'src', 'store', 'auth.js'),
  'utf8'
);
const webAdminViewSource = fs.readFileSync(
  path.resolve(uniappRoot, '..', 'frontend', 'src', 'views', 'AdminView.vue'),
  'utf8'
);
const webChatViewSource = fs.readFileSync(
  path.resolve(uniappRoot, '..', 'frontend', 'src', 'views', 'ChatView.vue'),
  'utf8'
);
const backendAuthSource = fs.readFileSync(
  path.resolve(uniappRoot, '..', 'backend', 'routers', 'auth.py'),
  'utf8'
);

const authStoreSnippets = [
  'const normalizePermissions = (permissions) => {',
  'permissions: (state) => normalizePermissions(state.user?.permissions)',
  'hasPermission: (state) => (permission) => normalizePermissions(state.user?.permissions).includes(permission)',
  "isAdmin: (state) => Boolean(state.user?.role && state.user?.role !== 'employee')",
  "isSuperAdmin: (state) => state.user?.role === 'super_admin' || state.user?.role === 'owner'",
  'roleName: (state) => {',
  "'owner': '老板'",
  "'executive': '高管'",
  "'daily_admin': '日常管理员'",
  "'staff_admin': '人事管理员'",
  "'employee': '普通员工'",
];

const adminAccessSnippets = [
  "const isAdminRole = (role) => Boolean(role && role !== 'employee')",
  "if (section === 'admin') {",
  'return isAdminRole(role)',
  'return isAdminRole(role)',
];

const webAuthSnippets = [
  "isAdmin: (state) => state.user?.role && state.user?.role !== 'employee'",
  "isSuperAdmin: (state) => state.user?.role === 'owner' || state.user?.role === 'super_admin'",
  'roleName: (state) => {',
];

const webAdminSnippets = [
  '<span class="user-role">{{ auth.roleName }}</span>',
];

const webChatSnippets = [
  '<h2 class="welcome-name">{{ computedWelcomeMsg }}</h2>',
  'const computedWelcomeMsg = computed(() => {',
  "return `${name}，${welcomeMsg.value}`",
  "return `${name}，您好，${welcomeMsg.value}`",
  'font-size: 28px;',
  'font-size: 20px;',
  'font-size: 16px;',
];

const backendSnippets = [
  'import json',
  'permissions = json.loads(user.permissions or "[]")',
  '"permissions": permissions',
  '"branch_id": user.branch_id',
  '"department_id": user.department_id',
];

const missing = [];

for (const snippet of authStoreSnippets) {
  if (!authStoreSource.includes(snippet)) {
    missing.push(`auth.js: ${snippet}`);
  }
}

for (const snippet of adminAccessSnippets) {
  if (!adminAccessSource.includes(snippet)) {
    missing.push(`admin-access.js: ${snippet}`);
  }
}

for (const snippet of webAuthSnippets) {
  if (!webAuthSource.includes(snippet)) {
    missing.push(`frontend auth.js: ${snippet}`);
  }
}

for (const snippet of webAdminSnippets) {
  if (!webAdminViewSource.includes(snippet)) {
    missing.push(`AdminView.vue: ${snippet}`);
  }
}

for (const snippet of webChatSnippets) {
  if (!webChatViewSource.includes(snippet)) {
    missing.push(`ChatView.vue: ${snippet}`);
  }
}

if (webChatViewSource.indexOf('const auth = useAuthStore()') > webChatViewSource.indexOf('const computedWelcomeMsg = computed(() => {')) {
  missing.push('ChatView.vue: auth store should be initialized before computedWelcomeMsg');
}

for (const snippet of backendSnippets) {
  if (!backendAuthSource.includes(snippet)) {
    missing.push(`auth.py: ${snippet}`);
  }
}

if (missing.length > 0) {
  console.error('permissions sync is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
