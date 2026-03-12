const fs = require('node:fs');
const path = require('node:path');

const importModule = async (filePath) => {
  let source = fs.readFileSync(filePath, 'utf8');

  if (filePath.endsWith('error-logger.js')) {
    const apiUrl = `data:text/javascript;charset=utf-8,${encodeURIComponent('export const resolveApiUrl = (value) => value;')}`;
    source = source
      .replace("'./api'", JSON.stringify(apiUrl))
      .replace('"./api"', JSON.stringify(apiUrl));
  }

  return import(`data:text/javascript;charset=utf-8,${encodeURIComponent(source)}`);
};

(async () => {
  const loggerPath = path.resolve(__dirname, '..', 'src', 'utils', 'error-logger.js');
  const chatPath = path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue');

  global.getCurrentPages = () => [{ route: 'pages/chat/chat' }];

  const storage = new Map();
  global.uni = {
    getStorageSync: (key) => storage.get(key) || '',
    setStorageSync: (key, value) => storage.set(key, value),
    request: () => {},
  };

  let loggerModule;
  try {
    loggerModule = await importModule(loggerPath);
  } catch (error) {
    console.error('Expected error-logger.js to be importable for stream logging.');
    process.exit(1);
  }

  const { captureClientEvent } = loggerModule;
  if (typeof captureClientEvent !== 'function') {
    console.error('Expected captureClientEvent to be exported from error-logger.js.');
    process.exit(1);
  }

  captureClientEvent({
    level: 'warn',
    type: 'chat-stream-timeout',
    message: 'stream timed out',
    context: {
      mode: 'general',
      retryCount: 1,
    },
  });

  const queueRaw = storage.get('zyd_client_log_queue');
  if (!queueRaw) {
    console.error('Expected captureClientEvent to persist a log entry.');
    process.exit(1);
  }

  const queue = JSON.parse(queueRaw);
  const lastEntry = queue[queue.length - 1];
  if (lastEntry?.type !== 'chat-stream-timeout' || lastEntry?.context?.retryCount !== 1) {
    console.error('Expected persisted stream log entry to include type and context.');
    process.exit(1);
  }

  const chatSource = fs.readFileSync(chatPath, 'utf8');
  const requiredChatSnippets = [
    "from '@/utils/error-logger'",
    'captureClientEvent',
    "type: 'chat-stream-retry'",
    "type: 'chat-stream-timeout'",
    "type: 'chat-stream-failure'",
  ];

  const missingChatSnippets = requiredChatSnippets.filter((snippet) => !chatSource.includes(snippet));
  if (missingChatSnippets.length > 0) {
    console.error('chat.vue is missing stream error logging integration:\n' + missingChatSnippets.join('\n'));
    process.exit(1);
  }
})().catch((error) => {
  console.error(error?.stack || error?.message || String(error));
  process.exit(1);
});
