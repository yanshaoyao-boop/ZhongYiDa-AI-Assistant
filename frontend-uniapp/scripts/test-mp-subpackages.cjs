const fs = require('node:fs');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..');
const pagesJsonPath = path.join(projectRoot, 'src', 'pages.json');
const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf8'));

const topLevelPaths = (pagesJson.pages || []).map((page) => page.path);
const subPackages = pagesJson.subPackages || [];
if (subPackages.length > 0) {
  console.error('Expected pages.json to avoid subPackages for admin pages because tabBar pages cannot live in a split package rooted at pages/admin.');
  process.exit(1);
}

const requiredTopLevelPages = [
  'pages/admin/admin',
  'pages/admin/staff',
  'pages/admin/lab',
  'pages/admin/chat-logs',
];
const missingTopLevelPages = requiredTopLevelPages.filter((pagePath) => !topLevelPaths.includes(pagePath));

if (missingTopLevelPages.length > 0) {
  console.error('Expected admin pages to stay in the main package:\n' + missingTopLevelPages.join('\n'));
  process.exit(1);
}

if (pagesJson.tabBar) {
  console.error('Expected pages.json to omit the native tabBar because the mini-program now uses a custom bottom navigation shell.');
  process.exit(1);
}
