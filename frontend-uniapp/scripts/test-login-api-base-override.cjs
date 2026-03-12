const fs = require('node:fs');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..');
const loginSource = fs.readFileSync(path.join(projectRoot, 'src', 'pages', 'login', 'login.vue'), 'utf8');
const apiSource = fs.readFileSync(path.join(projectRoot, 'src', 'utils', 'api.js'), 'utf8');

const requiredLoginSnippets = [
  '@longpress="handleApiBaseLongPress"',
  'class="api-base-hint"',
  'class="api-base-warning"',
  'const handleApiBaseLongPress = () => {',
  'const apiBaseDisplay = computed(() => {',
  '当前地址仅开发者工具可用，真机请长按上方 Logo 改为局域网地址',
];

const requiredApiSnippets = [
  'export const setApiBase = (value) => {',
  'export const clearApiBase = () => {',
  'export const isLoopbackApiBase = (value = \'\') => {',
];

const missing = [
  ...requiredLoginSnippets
    .filter((snippet) => !loginSource.includes(snippet))
    .map((snippet) => `login.vue -> ${snippet}`),
  ...requiredApiSnippets
    .filter((snippet) => !apiSource.includes(snippet))
    .map((snippet) => `api.js -> ${snippet}`),
];

if (missing.length > 0) {
  console.error('API base override flow is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
