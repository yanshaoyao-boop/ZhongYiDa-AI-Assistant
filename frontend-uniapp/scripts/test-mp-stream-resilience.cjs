const fs = require('node:fs');
const path = require('node:path');

const importModule = async (filePath) => {
  let source = fs.readFileSync(filePath, 'utf8');

  if (filePath.endsWith('mp-stream-chat.js')) {
    const decoderPath = path.resolve(path.dirname(filePath), 'chunk-decoder.js');
    const decoderSource = fs.readFileSync(decoderPath, 'utf8');
    const decoderUrl = `data:text/javascript;charset=utf-8,${encodeURIComponent(decoderSource)}`;
    const apiUrl = `data:text/javascript;charset=utf-8,${encodeURIComponent('export const resolveApiUrl = (value) => value;')}`;
    source = source
      .replace("'./chunk-decoder'", JSON.stringify(decoderUrl))
      .replace('"./chunk-decoder"', JSON.stringify(decoderUrl))
      .replace("'./api'", JSON.stringify(apiUrl))
      .replace('"./api"', JSON.stringify(apiUrl));
  }

  return import(`data:text/javascript;charset=utf-8,${encodeURIComponent(source)}`);
};

(async () => {
  const utilityPath = path.resolve(__dirname, '..', 'src', 'utils', 'mp-stream-chat.js');
  const chatPath = path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue');

  let utilityModule;
  try {
    utilityModule = await importModule(utilityPath);
  } catch (error) {
    console.error('Expected mp-stream-chat.js to exist and be importable.');
    process.exit(1);
  }

  const { createMpStreamChatController } = utilityModule;
  if (typeof createMpStreamChatController !== 'function') {
    console.error('Expected createMpStreamChatController to be exported.');
    process.exit(1);
  }

  const chatSource = fs.readFileSync(chatPath, 'utf8');
  const requiredChatSnippets = [
    "from '@/utils/mp-stream-chat'",
    'createMpStreamChatController',
    'requestTask.abort()',
  ];

  const missingChatSnippets = requiredChatSnippets.filter((snippet) => !chatSource.includes(snippet));
  if (missingChatSnippets.length > 0) {
    console.error('chat.vue is missing mp stream resilience integration:\n' + missingChatSnippets.join('\n'));
    process.exit(1);
  }

  const encoder = new TextEncoder();

  let attempts = 0;
  const retryEvents = [];
  const retryController = createMpStreamChatController({
    requestImpl: (options) => {
      attempts += 1;
      let chunkHandler = null;
      const task = {
        abort: () => {},
        onChunkReceived: (handler) => {
          chunkHandler = handler;
        },
        onHeadersReceived: () => {},
      };
      setTimeout(() => {
        if (attempts === 1) {
          options.fail?.({ errMsg: 'request:fail timeout' });
          options.complete?.();
          return;
        }
        options.success?.({ statusCode: 200 });
        setTimeout(() => chunkHandler?.({ data: encoder.encode('ok').buffer }), 0);
        setTimeout(() => options.complete?.(), 5);
      }, 0);
      return task;
    },
    buildRequestOptions: () => ({
      url: '/api/chat/stream',
      method: 'POST',
    }),
    chunkTimeoutMs: 20,
    retryLimit: 1,
    onRetry: (meta) => retryEvents.push(meta.attempt),
  });

  let retryText = '';
  await retryController.start({
    onText: (text) => {
      retryText += text;
    },
  });

  if (attempts !== 2 || retryEvents.length !== 1 || retryText !== 'ok') {
    console.error('Expected mp stream controller to retry once before succeeding.');
    process.exit(1);
  }

  let timeoutAbortCount = 0;
  const timeoutController = createMpStreamChatController({
    requestImpl: () => {
      const task = {
        abort: () => {
          timeoutAbortCount += 1;
        },
        onChunkReceived: () => {},
        onHeadersReceived: () => {},
      };
      return task;
    },
    buildRequestOptions: () => ({
      url: '/api/chat/stream',
      method: 'POST',
    }),
    chunkTimeoutMs: 10,
    retryLimit: 0,
  });

  let timedOut = false;
  try {
    await timeoutController.start({
      onText: () => {},
    });
  } catch (error) {
    timedOut = error?.code === 'STREAM_TIMEOUT';
  }

  if (!timedOut || timeoutAbortCount !== 1) {
    console.error('Expected mp stream controller to abort and reject on stalled chunks.');
    process.exit(1);
  }
})().catch((error) => {
  console.error(error?.stack || error?.message || String(error));
  process.exit(1);
});
