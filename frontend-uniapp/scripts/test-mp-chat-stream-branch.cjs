const fs = require('node:fs');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(projectRoot, 'src', 'pages', 'chat', 'chat.vue'), 'utf8');

const requiredSnippets = [
  "from '@/utils/mp-stream-chat'",
  'createMpStreamChatController',
  'requestTask = createMpStreamChatController',
  'await requestTask.start',
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error('chat.vue mp stream branch is missing required pieces:\n' + missing.join('\n'));
  process.exit(1);
}
