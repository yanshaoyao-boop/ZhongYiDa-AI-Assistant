const http = require('node:http');
const { getSmokeBaseCandidates } = require('./smoke-config.cjs');

const username = process.env.SMOKE_USERNAME || '123456';
const password = process.env.SMOKE_PASSWORD || '123456';

const requestText = (url, options = {}) => new Promise((resolve, reject) => {
  const target = new URL(url);
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
      resolve({ statusCode: res.statusCode || 0, body: data });
    });
  });

  req.on('error', reject);
  if (options.body) req.write(options.body);
  req.end();
});

(async () => {
  const loginBody = `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`;
  const candidates = getSmokeBaseCandidates();
  let lastError = null;

  for (const baseUrl of candidates) {
    try {
      const loginResponse = await requestText(`${baseUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Content-Length': Buffer.byteLength(loginBody),
        },
        body: loginBody,
      });

      if (loginResponse.statusCode !== 200) {
        lastError = new Error(`Login failed at ${baseUrl}: ${loginResponse.statusCode} ${loginResponse.body}`);
        continue;
      }

      const loginPayload = JSON.parse(loginResponse.body);
      const coachResponse = await requestText(`${baseUrl}/api/upload/coach-cases`, {
        headers: {
          'Authorization': `Bearer ${loginPayload.access_token}`,
        },
      });

      if (coachResponse.statusCode !== 200) {
        lastError = new Error(`Expected coach cases endpoint to succeed at ${baseUrl}, got ${coachResponse.statusCode}: ${coachResponse.body}`);
        continue;
      }

      let payload;
      try {
        payload = JSON.parse(coachResponse.body);
      } catch (error) {
        lastError = new Error(`Expected coach cases endpoint to return JSON at ${baseUrl}, got: ${coachResponse.body.slice(0, 200)}`);
        continue;
      }

      if (!Array.isArray(payload)) {
        lastError = new Error(`Expected coach cases endpoint to return an array at ${baseUrl}.`);
        continue;
      }

      if (payload.length === 0) {
        lastError = new Error(`Expected coach cases endpoint to contain at least one case at ${baseUrl}.`);
        continue;
      }

      console.log(`coach cases smoke passed with ${baseUrl}`);
      return;
    } catch (error) {
      lastError = error;
    }
  }

  console.error(lastError ? lastError.message : 'Coach cases smoke failed without a detailed error.');
  process.exit(1);
})();
