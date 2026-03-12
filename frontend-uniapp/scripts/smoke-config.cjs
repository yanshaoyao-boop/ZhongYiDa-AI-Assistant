const fs = require('node:fs');
const path = require('node:path');

const readEnvLocalBaseUrl = () => {
  const envLocalPath = path.resolve(__dirname, '..', '.env.local');
  if (!fs.existsSync(envLocalPath)) {
    return '';
  }

  const source = fs.readFileSync(envLocalPath, 'utf8');
  const match = source.match(/^\s*VITE_API_BASE_URL\s*=\s*(.+)\s*$/m);
  return match ? match[1].trim() : '';
};

const getSmokeBaseCandidates = () => {
  const candidates = [
    process.env.SMOKE_API_BASE_URL || '',
    readEnvLocalBaseUrl(),
    'http://127.0.0.1:8000',
  ].filter(Boolean);

  return [...new Set(candidates)];
};

const getSmokeBaseUrl = () => {
  return getSmokeBaseCandidates()[0];
};

module.exports = {
  getSmokeBaseCandidates,
  getSmokeBaseUrl,
};
