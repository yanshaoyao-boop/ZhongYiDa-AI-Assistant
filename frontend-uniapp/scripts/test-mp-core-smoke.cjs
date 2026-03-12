const http = require('node:http');
const { spawnSync } = require('node:child_process');
const { getSmokeBaseCandidates } = require('./smoke-config.cjs');

const localCommands = [
  ['npm', ['run', 'test:login-chat-baseline-polish']],
  ['npm', ['run', 'test:login-hero-polish']],
  ['npm', ['run', 'test:login-api-base-override']],
  ['npm', ['run', 'test:login-chat-entry-flow']],
  ['npm', ['run', 'test:chat-mode-restore-flow']],
  ['npm', ['run', 'test:chat-page-bindings']],
  ['npm', ['run', 'test:chat-nav-sidebar-baseline']],
  ['npm', ['run', 'test:chat-message-composer-baseline']],
  ['npm', ['run', 'test:chat-mp-tail-visibility']],
  ['npm', ['run', 'test:chat-mp-plain-text-render']],
  ['npm', ['run', 'test:chat-mp-markdown-lite']],
  ['npm', ['run', 'test:chat-avatar-and-nav-icons']],
  ['npm', ['run', 'test:chat-bottom-nav-four-items']],
  ['npm', ['run', 'test:chat-mp-touch-guards']],
  ['npm', ['run', 'test:chat-mp-minimal-shell']],
  ['npm', ['run', 'test:mp-login-request']],
  ['npm', ['run', 'test:mp-no-native-tabbar']],
  ['npm', ['run', 'test:mp-chat-stream-branch']],
  ['npm', ['run', 'test:mp-stream-resilience']],
  ['npm', ['run', 'test:mp-stream-error-logging']],
  ['npm', ['run', 'test:mp-error-logging']],
  ['npm', ['run', 'test:mp-subpackages']],
  ['npm', ['run', 'test:mp-chat-image-upload-bridge']],
  ['npm', ['run', 'test:chat-scroll-entry-polish']],
  ['npm', ['run', 'test:chat-brand-mode-context']],
  ['npm', ['run', 'test:chat-action-button-contrast']],
  ['npm', ['run', 'test:chat-attachment-state-polish']],
  ['npm', ['run', 'test:chat-upload-icon-state-polish']],
  ['npm', ['run', 'test:chat-welcome-kicker-polish']],
  ['npm', ['run', 'test:chat-welcome-stage-polish']],
  ['npm', ['run', 'test:chat-mode-selector-polish']],
  ['npm', ['run', 'test:chat-mode-theme-polish']],
  ['npm', ['run', 'test:chat-mp-shell-regression']],
  ['npm', ['run', 'test:chat-nav-sidebar-polish']],
  ['npm', ['run', 'test:chat-message-area-polish']],
  ['npm', ['run', 'test:chat-image-preview-polish']],
  ['npm', ['run', 'test:chat-image-placeholder-polish']],
  ['npm', ['run', 'test:chat-image-status-feedback']],
  ['npm', ['run', 'test:chat-expert-copy']],
  ['npm', ['run', 'test:coach-mode-data']],
  ['npm', ['run', 'test:coach-step-context-polish']],
  ['npm', ['run', 'test:coach-step-dedup']],
  ['npm', ['run', 'test:coach-selection-summary-polish']],
  ['npm', ['run', 'test:coach-card-intel-polish']],
  ['npm', ['run', 'test:mp-image-request-config']],
  ['npm', ['run', 'test:mp-image-data-url']],
  ['npm', ['run', 'test:mp-image-selection-guard']],
  ['npm', ['run', 'test:mp-safe-area-and-state-polish']],
  ['npm', ['run', 'test:admin-role-guards']],
  ['npm', ['run', 'test:admin-mp-shell']],
  ['npm', ['run', 'test:chat-logs-mp-mvp']],
  ['npm', ['run', 'test:lab-mp-state']],
  ['npm', ['run', 'test:lab-mp-mvp']],
  ['npm', ['run', 'test:staff-mp-crud']],
  ['npm', ['run', 'test:staff-mp-mvp']],
];

const integrationCommands = [
  ['npm', ['run', 'test:backend-smoke']],
  ['npm', ['run', 'test:coach-cases-endpoint']],
];

const runCommand = (command, args, extraEnv = {}) => {
  const label = `${command} ${args.join(' ')}`;
  console.log(`\n>>> ${label}`);
  const isWindows = process.platform === 'win32';
  const result = isWindows
    ? spawnSync(process.env.ComSpec || 'cmd.exe', ['/d', '/s', '/c', label], {
        stdio: 'inherit',
        env: {
          ...process.env,
          ...extraEnv,
        },
      })
    : spawnSync(command, args, {
        stdio: 'inherit',
        env: {
          ...process.env,
          ...extraEnv,
        },
      });

  if (result.error) {
    console.error(result.error.message);
  }

  if (result.status !== 0) {
    console.error(`\nmp core smoke failed at: ${label}`);
    process.exit(result.status || 1);
  }
};

const canReachBaseUrl = (baseUrl) => new Promise((resolve) => {
  const target = new URL(`${baseUrl}/api/auth/login`);
  const req = http.request({
    hostname: target.hostname,
    port: target.port,
    path: target.pathname,
    method: 'POST',
    timeout: 2500,
  }, (res) => {
    resolve(true);
    res.resume();
  });

  req.on('timeout', () => {
    req.destroy();
    resolve(false);
  });
  req.on('error', () => resolve(false));
  req.end('username=probe&password=probe');
});

(async () => {
  for (const [command, args] of localCommands) {
    runCommand(command, args);
  }

  const candidates = getSmokeBaseCandidates();
  let reachableBaseUrl = '';

  for (const baseUrl of candidates) {
    /* eslint-disable no-await-in-loop */
    if (await canReachBaseUrl(baseUrl)) {
      reachableBaseUrl = baseUrl;
      break;
    }
  }

  if (reachableBaseUrl) {
    console.log(`\n>>> integration smoke using ${reachableBaseUrl}`);
    for (const [command, args] of integrationCommands) {
      runCommand(command, args, { SMOKE_API_BASE_URL: reachableBaseUrl });
    }
  } else {
    console.log('\n>>> integration smoke skipped: no reachable backend candidate');
  }

  runCommand('npm', ['run', 'build:mp-weixin']);
  console.log('\nmp core smoke passed.');
})();
