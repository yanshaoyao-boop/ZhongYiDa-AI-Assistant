const fs = require('node:fs');
const path = require('node:path');

const importApiModule = async (filePath) => {
  let source = fs.readFileSync(filePath, 'utf8');
  source = source
    .replace(/\/\/ #ifdef H5[\s\S]*?\/\/ #endif/g, '')
    .replace(/\/\/ #ifndef H5/g, '')
    .replace(/\/\/ #endif/g, '')
    .replace(/import\.meta\.env\.VITE_API_BASE_URL \|\| ''/g, "''")
    .replace(/import\.meta\.env\.DEV \? readEnvApiBase\(\) : ''/g, "''");

  return import(`data:text/javascript;charset=utf-8,${encodeURIComponent(source)}`);
};

(async () => {
  const apiPath = path.resolve(__dirname, '..', 'src', 'utils', 'api.js');
  const storage = new Map();

  globalThis.uni = {
    getStorageSync: (key) => storage.get(key) || '',
    setStorageSync: (key, value) => storage.set(key, value),
    removeStorageSync: (key) => storage.delete(key),
  };

  const apiModule = await importApiModule(apiPath);
  const { setApiBase, getApiBase, resolveApiUrl } = apiModule;

  setApiBase('https://www.zhongyidazhinengzhushou.cn/api');
  if (getApiBase() !== 'https://www.zhongyidazhinengzhushou.cn') {
    console.error('Expected API base to strip a trailing /api suffix.');
    process.exit(1);
  }

  const loginUrl = resolveApiUrl('/api/auth/login');
  if (loginUrl !== 'https://www.zhongyidazhinengzhushou.cn/api/auth/login') {
    console.error(`Expected normalized login URL, got: ${loginUrl}`);
    process.exit(1);
  }
})().catch((error) => {
  console.error(error?.stack || error?.message || String(error));
  process.exit(1);
});
