const { spawnSync } = require('node:child_process');
const path = require('node:path');

const projectDir = path.resolve(__dirname, '..');
const result = process.platform === 'win32'
  ? spawnSync('cmd.exe', ['/d', '/s', '/c', 'npm run build:mp-weixin'], {
      cwd: projectDir,
      encoding: 'utf8',
    })
  : spawnSync('npm', ['run', 'build:mp-weixin'], {
      cwd: projectDir,
      encoding: 'utf8',
    });

const output = `${result.stdout || ''}\n${result.stderr || ''}`;

process.stdout.write(output);

if (output.includes('条件编译失败')) {
  console.error('\nExpected mp-weixin build output to be free of conditional compilation failures.');
  process.exit(1);
}

if (result.status !== 0) {
  process.exit(result.status || 1);
}
