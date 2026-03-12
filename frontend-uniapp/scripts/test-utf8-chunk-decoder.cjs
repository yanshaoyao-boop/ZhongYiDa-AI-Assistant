const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const modulePath = path.resolve(__dirname, '..', 'src', 'utils', 'chunk-decoder.js');
  const moduleSource = fs.readFileSync(modulePath, 'utf8');
  const dataUrl = `data:text/javascript;charset=utf-8,${encodeURIComponent(moduleSource)}`;

  let decoderModule;
  try {
    decoderModule = await import(dataUrl);
  } catch (error) {
    console.error('Expected chunk-decoder.js to exist and be importable.');
    process.exit(1);
  }

  const { createUtf8ChunkDecoder } = decoderModule;
  if (typeof createUtf8ChunkDecoder !== 'function') {
    console.error('Expected createUtf8ChunkDecoder to be exported.');
    process.exit(1);
  }

  const encoder = new TextEncoder();
  const bytes = encoder.encode('你好，世界');
  const first = bytes.slice(0, 2);
  const second = bytes.slice(2, 7);
  const third = bytes.slice(7);

  const decoder = createUtf8ChunkDecoder();
  const parts = [
    decoder.push(first.buffer),
    decoder.push(second.buffer),
    decoder.push(third.buffer),
    decoder.flush(),
  ];

  const text = parts.join('');
  if (text !== '你好，世界') {
    console.error(`Expected decoded text to equal "你好，世界", got "${text}".`);
    process.exit(1);
  }
})();
