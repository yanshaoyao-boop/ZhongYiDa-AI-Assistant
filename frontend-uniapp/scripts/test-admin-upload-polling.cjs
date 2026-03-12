const fs = require('node:fs');
const path = require('node:path');

const uploaderSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'composables', 'useUploader.js'),
  'utf8'
);

const adminSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'pages', 'admin', 'admin.vue'),
  'utf8'
);

const requiredUploaderSnippets = [
  'response.data?.task_id',
  '/api/upload/tasks/',
  "task.status === 'success'",
  "task.status === 'error'",
];

const requiredAdminSnippets = [
  '/document?category=admin&async_mode=true',
  '/document?category=biz&async_mode=true',
];

const missing = [
  ...requiredUploaderSnippets
    .filter((snippet) => !uploaderSource.includes(snippet))
    .map((snippet) => `useUploader.js: ${snippet}`),
  ...requiredAdminSnippets
    .filter((snippet) => !adminSource.includes(snippet))
    .map((snippet) => `admin.vue: ${snippet}`),
];

if (missing.length > 0) {
  console.error('admin upload polling is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
