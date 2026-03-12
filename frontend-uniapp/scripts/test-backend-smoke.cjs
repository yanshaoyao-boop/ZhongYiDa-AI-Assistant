const http = require('node:http');
const { getSmokeBaseCandidates } = require('./smoke-config.cjs');

const username = process.env.SMOKE_USERNAME || '123456';
const password = process.env.SMOKE_PASSWORD || '123456';

const requestJson = (url, options = {}) => new Promise((resolve, reject) => {
  const target = new URL(url);
  const body = options.body || null;
  const req = http.request({
    hostname: target.hostname,
    port: target.port,
    path: target.pathname + target.search,
    method: options.method || 'GET',
    headers: options.headers || {},
  }, (res) => {
    let data = '';
    res.setEncoding('utf8');
    res.on('data', (chunk) => {
      data += chunk;
    });
    res.on('end', () => {
      resolve({
        statusCode: res.statusCode || 0,
        body: data,
      });
    });
  });

  req.on('error', reject);
  if (body) req.write(body);
  req.end();
});

(async () => {
  const loginBody = `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`;
  const candidates = getSmokeBaseCandidates();
  let lastError = null;

  for (const baseUrl of candidates) {
    try {
      const loginResponse = await requestJson(`${baseUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Content-Length': Buffer.byteLength(loginBody),
        },
        body: loginBody,
      });

      if (loginResponse.statusCode !== 200) {
        lastError = new Error(`Expected login to succeed at ${baseUrl}, got ${loginResponse.statusCode}: ${loginResponse.body}`);
        continue;
      }

      let loginPayload;
      try {
        loginPayload = JSON.parse(loginResponse.body);
      } catch (error) {
        lastError = new Error(`Expected login response to be JSON at ${baseUrl}, got: ${loginResponse.body}`);
        continue;
      }

      if (!loginPayload.access_token) {
        lastError = new Error(`Expected login response to include access_token at ${baseUrl}.`);
        continue;
      }

      const chatBody = JSON.stringify({
        message: '你好',
        mode: 'general',
        history: [],
      });

      const chatResponse = await requestJson(`${baseUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${loginPayload.access_token}`,
          'Content-Length': Buffer.byteLength(chatBody),
        },
        body: chatBody,
      });

      if (chatResponse.statusCode !== 200) {
        lastError = new Error(`Expected chat stream to succeed at ${baseUrl}, got ${chatResponse.statusCode}: ${chatResponse.body}`);
        continue;
      }

      if (!chatResponse.body || !chatResponse.body.trim()) {
        lastError = new Error(`Expected chat stream body to contain assistant output at ${baseUrl}, got empty response.`);
        continue;
      }

      console.log(`backend smoke passed with ${baseUrl}`);
      return;
    } catch (error) {
      lastError = error;
    }
  }

  console.error(lastError ? lastError.message : 'Backend smoke failed without a detailed error.');
  process.exit(1);
})();
