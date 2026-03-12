const fs = require('node:fs');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..');
const apiSource = fs.readFileSync(path.join(projectRoot, 'src', 'utils', 'api.js'), 'utf8');
const mainSource = fs.readFileSync(path.join(projectRoot, 'src', 'main.js'), 'utf8');

const expectations = [
  {
    ok: !apiSource.includes('http://192.168.0.100:8000'),
    message: 'Expected api.js to stop hard-coding the stale 192.168.0.100 development API fallback.',
  },
  {
    ok: apiSource.includes("const readMpDevApiBase = () => import.meta.env.DEV ? readEnvApiBase() : ''"),
    message: 'Expected api.js to reuse VITE_API_BASE_URL as the mp-weixin development fallback.',
  },
  {
    ok: apiSource.includes('export const ensureApiBaseConfigured ='),
    message: 'Expected api.js to export ensureApiBaseConfigured.',
  },
  {
    ok: mainSource.includes('ensureApiBaseConfigured()'),
    message: 'Expected main.js to bootstrap API base configuration at startup.',
  },
];

const failed = expectations.filter((item) => !item.ok).map((item) => item.message);

if (failed.length > 0) {
  console.error(failed.join('\n'));
  process.exit(1);
}
