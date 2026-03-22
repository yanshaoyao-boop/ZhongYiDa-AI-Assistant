const fs = require('node:fs');
const path = require('node:path');

const importModule = async (filePath) => {
  const source = fs.readFileSync(filePath, 'utf8');
  return import(`data:text/javascript;charset=utf-8,${encodeURIComponent(source)}`);
};

(async () => {
  const parserPath = path.resolve(__dirname, '..', 'src', 'utils', 'sse-parser.js');

  let parserModule;
  try {
    parserModule = await importModule(parserPath);
  } catch (error) {
    console.error('Expected sse-parser.js to exist and be importable.');
    process.exit(1);
  }

  const { createSseEventParser } = parserModule;
  if (typeof createSseEventParser !== 'function') {
    console.error('Expected createSseEventParser to be exported.');
    process.exit(1);
  }

  const parser = createSseEventParser();
  const firstPass = parser.push('data: {"content":"你');
  const secondPass = parser.push('好"}\n\ndata: [DONE]\n\n');

  if (firstPass.events.length !== 0) {
    console.error('Expected no complete SSE event before the line is closed.');
    process.exit(1);
  }

  if (secondPass.events.length !== 2) {
    console.error('Expected SSE parser to emit content and done events.');
    process.exit(1);
  }

  const [contentEvent, doneEvent] = secondPass.events;
  if (contentEvent.type !== 'content' || contentEvent.content !== '你好') {
    console.error('Expected SSE parser to decode JSON content payloads.');
    process.exit(1);
  }

  if (doneEvent.type !== 'done') {
    console.error('Expected SSE parser to decode [DONE] event.');
    process.exit(1);
  }

  const plainParser = createSseEventParser();
  const plainResult = plainParser.push('纯文本片段');
  if (plainResult.plainText !== '纯文本片段') {
    console.error('Expected parser to preserve plain text fallback for legacy streams.');
    process.exit(1);
  }
})().catch((error) => {
  console.error(error?.stack || error?.message || String(error));
  process.exit(1);
});
