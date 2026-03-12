const fs = require('node:fs');
const path = require('node:path');

const importModule = async (filePath) => {
  let source = fs.readFileSync(filePath, 'utf8');

  if (filePath.endsWith('chat-image-upload.js')) {
    const apiUrl = `data:text/javascript;charset=utf-8,${encodeURIComponent('export const resolveApiUrl = (value) => value;')}`;
    source = source
      .replace("'./api'", JSON.stringify(apiUrl))
      .replace('"./api"', JSON.stringify(apiUrl));
  }

  return import(`data:text/javascript;charset=utf-8,${encodeURIComponent(source)}`);
};

(async () => {
  const uploadUtilPath = path.resolve(__dirname, '..', 'src', 'utils', 'chat-image-upload.js');
  const chatPath = path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'chat.vue');

  let uploadModule;
  try {
    uploadModule = await importModule(uploadUtilPath);
  } catch (error) {
    console.error('Expected chat-image-upload.js to exist and be importable.');
    process.exit(1);
  }

  const { uploadChatImage } = uploadModule;
  if (typeof uploadChatImage !== 'function') {
    console.error('Expected uploadChatImage to be exported.');
    process.exit(1);
  }

  const payload = await uploadChatImage({
    filePath: '/tmp/receipt.jpg',
    token: 'demo-token',
    uploadFileImpl: (options) => {
      if (options.url !== '/api/upload/chat-image') {
        throw new Error(`Unexpected upload URL: ${options.url}`);
      }
      if (options.name !== 'file') {
        throw new Error(`Unexpected upload field: ${options.name}`);
      }
      if (options.header?.Authorization !== 'Bearer demo-token') {
        throw new Error('Expected Authorization header to include bearer token.');
      }
      options.success?.({
        statusCode: 200,
        data: JSON.stringify({
          image_upload_id: 'img-123',
          filename: 'receipt.jpg',
        }),
      });
      options.complete?.();
      return {};
    },
  });

  if (payload.image_upload_id !== 'img-123') {
    console.error('Expected uploadChatImage to resolve parsed upload payload.');
    process.exit(1);
  }

  const chatSource = fs.readFileSync(chatPath, 'utf8');
  const requiredChatSnippets = [
    "from '@/utils/chat-image-upload'",
    'const selectedImageUploadId = ref(',
    'await uploadChatImage({',
    'image_upload_id: currentImageUploadId',
    "selectedImageUploadId.value = ''",
  ];

  const missing = requiredChatSnippets.filter((snippet) => !chatSource.includes(snippet));
  if (missing.length > 0) {
    console.error('chat.vue is missing mini-program image upload bridge pieces:\n' + missing.join('\n'));
    process.exit(1);
  }
})().catch((error) => {
  console.error(error?.stack || error?.message || String(error));
  process.exit(1);
});
