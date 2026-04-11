const fs = require('node:fs');
const path = require('node:path');

const componentPaths = [
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'components', 'ChatMessageInput.vue'),
  path.resolve(__dirname, '..', 'src', 'pages', 'chat', 'components', 'ChatWelcomeScreen.vue'),
];

const brokenMarkers = ['?/text>'];

const findings = [];

for (const filePath of componentPaths) {
  const source = fs.readFileSync(filePath, 'utf8');
  for (const marker of brokenMarkers) {
    if (source.includes(marker)) {
      findings.push(`${path.basename(filePath)} contains broken template marker: ${marker}`);
    }
  }
}

if (findings.length > 0) {
  console.error(findings.join('\n'));
  process.exit(1);
}
