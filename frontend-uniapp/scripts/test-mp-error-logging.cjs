const fs = require('node:fs');
const path = require('node:path');

const appSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'App.vue'),
  'utf8'
);

const mainSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'main.js'),
  'utf8'
);

const loggerSource = fs.readFileSync(
  path.resolve(__dirname, '..', 'src', 'utils', 'error-logger.js'),
  'utf8'
);

const requiredAppSnippets = [
  'onError(error)',
  'onUnhandledRejection(event)',
];

const requiredMainSnippets = [
  "import { installGlobalErrorLogging } from './utils/error-logger'",
  'installGlobalErrorLogging()',
];

const requiredLoggerSnippets = [
  "const CLIENT_LOG_ENDPOINT = '/api/client-logs'",
  'CLIENT_LOG_QUEUE_KEY',
  'persistClientLog',
  'flushClientLogs',
  'uni.request = createLoggedRequest(originalRequest)',
];

const missing = [
  ...requiredAppSnippets
    .filter((snippet) => !appSource.includes(snippet))
    .map((snippet) => `App.vue: ${snippet}`),
  ...requiredMainSnippets
    .filter((snippet) => !mainSource.includes(snippet))
    .map((snippet) => `main.js: ${snippet}`),
  ...requiredLoggerSnippets
    .filter((snippet) => !loggerSource.includes(snippet))
    .map((snippet) => `error-logger.js: ${snippet}`),
];

if (missing.length > 0) {
  console.error('mini-program error logging is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
