const crypto = require('crypto');
const http = require('http');
const fs = require('fs');
const os = require('os');
const path = require('path');

const OPCODES = { TEXT: 0x01, CLOSE: 0x08, PING: 0x09, PONG: 0x0A };
const WS_MAGIC = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';

function computeAcceptKey(key) {
  return crypto.createHash('sha1').update(key + WS_MAGIC).digest('base64');
}

function encodeFrame(opcode, payload) {
  const fin = 0x80;
  const length = payload.length;
  let header;
  if (length < 126) {
    header = Buffer.from([fin | opcode, length]);
  } else if (length < 65536) {
    header = Buffer.alloc(4);
    header[0] = fin | opcode;
    header[1] = 126;
    header.writeUInt16BE(length, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = fin | opcode;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(length), 2);
  }
  return Buffer.concat([header, payload]);
}

function decodeFrame(buffer) {
  if (buffer.length < 2) return null;
  const opcode = buffer[0] & 0x0F;
  const masked = (buffer[1] & 0x80) !== 0;
  let payloadLen = buffer[1] & 0x7F;
  let offset = 2;
  if (!masked) throw new Error('client frames must be masked');
  if (payloadLen === 126) {
    if (buffer.length < 4) return null;
    payloadLen = buffer.readUInt16BE(2);
    offset = 4;
  } else if (payloadLen === 127) {
    if (buffer.length < 10) return null;
    payloadLen = Number(buffer.readBigUInt64BE(2));
    offset = 10;
  }
  const dataOffset = offset + 4;
  const totalLen = dataOffset + payloadLen;
  if (buffer.length < totalLen) return null;
  const mask = buffer.slice(offset, dataOffset);
  const payload = Buffer.alloc(payloadLen);
  for (let index = 0; index < payloadLen; index += 1) {
    payload[index] = buffer[dataOffset + index] ^ mask[index % 4];
  }
  return { opcode, payload, bytesConsumed: totalLen };
}

const PORT = Number(process.env.FORGE_VISUAL_COMPANION_PORT || (49152 + Math.floor(Math.random() * 16383)));
const HOST = process.env.FORGE_VISUAL_COMPANION_HOST || '127.0.0.1';
const URL_HOST = process.env.FORGE_VISUAL_COMPANION_URL_HOST || (HOST === '127.0.0.1' ? 'localhost' : HOST);
const SESSION_DIR = process.env.FORGE_VISUAL_COMPANION_DIR || path.join(os.tmpdir(), 'forge-visual-companion');
const CONTENT_DIR = path.join(SESSION_DIR, 'content');
const STATE_DIR = path.join(SESSION_DIR, 'state');
let ownerPid = process.env.FORGE_VISUAL_COMPANION_OWNER_PID ? Number(process.env.FORGE_VISUAL_COMPANION_OWNER_PID) : null;

const MIME_TYPES = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml'
};

const WAITING_PAGE = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Forge Visual Companion</title>
<style>body { font-family: system-ui, sans-serif; padding: 2rem; max-width: 800px; margin: 0 auto; }
h1 { color: #1d1d1f; } p { color: #666; }</style></head>
<body><h1>Forge Visual Companion</h1><p>Waiting for the agent to push a screen...</p></body></html>`;

const frameTemplate = fs.readFileSync(path.join(__dirname, 'frame-template.html'), 'utf-8');
const helperScript = fs.readFileSync(path.join(__dirname, 'helper.js'), 'utf-8');
const helperInjection = '<script>\n' + helperScript + '\n</script>';
const clients = new Set();
const debounceTimers = new Map();
const IDLE_TIMEOUT_MS = 30 * 60 * 1000;
let lastActivity = Date.now();

function touchActivity() {
  lastActivity = Date.now();
}

function isFullDocument(html) {
  const trimmed = html.trimStart().toLowerCase();
  return trimmed.startsWith('<!doctype') || trimmed.startsWith('<html');
}

function injectHelper(html) {
  if (html.includes('</body>')) return html.replace('</body>', helperInjection + '\n</body>');
  return html + helperInjection;
}

function newestScreen() {
  return fs.readdirSync(CONTENT_DIR)
    .filter(file => file.endsWith('.html'))
    .map(file => {
      const filePath = path.join(CONTENT_DIR, file);
      return { filePath, mtime: fs.statSync(filePath).mtime.getTime() };
    })
    .sort((left, right) => right.mtime - left.mtime)[0]?.filePath || null;
}

function renderScreen() {
  const screen = newestScreen();
  if (!screen) return WAITING_PAGE;
  const raw = fs.readFileSync(screen, 'utf-8');
  return isFullDocument(raw) ? raw : frameTemplate.replace('<!-- CONTENT -->', raw);
}

function handleRequest(req, res) {
  touchActivity();
  if (req.method === 'GET' && req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(injectHelper(renderScreen()));
    return;
  }
  if (req.method === 'GET' && req.url.startsWith('/files/')) {
    const name = path.basename(decodeURIComponent(req.url.slice(7)));
    const filePath = path.join(CONTENT_DIR, name);
    if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME_TYPES[path.extname(filePath).toLowerCase()] || 'application/octet-stream' });
    res.end(fs.readFileSync(filePath));
    return;
  }
  res.writeHead(404);
  res.end('Not found');
}

function handleMessage(text) {
  let event;
  try {
    event = JSON.parse(text);
  } catch (error) {
    console.error('Failed to parse WebSocket message:', error.message);
    return;
  }
  touchActivity();
  console.log(JSON.stringify({ source: 'user-event', ...event }));
  if (event.choice) {
    fs.appendFileSync(path.join(STATE_DIR, 'events'), JSON.stringify(event) + '\n');
  }
}

function handleUpgrade(req, socket) {
  const key = req.headers['sec-websocket-key'];
  if (!key) {
    socket.destroy();
    return;
  }
  socket.write('HTTP/1.1 101 Switching Protocols\r\n' +
    'Upgrade: websocket\r\nConnection: Upgrade\r\n' +
    'Sec-WebSocket-Accept: ' + computeAcceptKey(key) + '\r\n\r\n');
  let buffer = Buffer.alloc(0);
  clients.add(socket);
  socket.on('data', chunk => {
    buffer = Buffer.concat([buffer, chunk]);
    while (buffer.length > 0) {
      let result;
      try {
        result = decodeFrame(buffer);
      } catch (error) {
        socket.end(encodeFrame(OPCODES.CLOSE, Buffer.alloc(0)));
        clients.delete(socket);
        return;
      }
      if (!result) break;
      buffer = buffer.slice(result.bytesConsumed);
      if (result.opcode === OPCODES.TEXT) handleMessage(result.payload.toString());
      else if (result.opcode === OPCODES.PING) socket.write(encodeFrame(OPCODES.PONG, result.payload));
      else if (result.opcode === OPCODES.CLOSE) {
        socket.end(encodeFrame(OPCODES.CLOSE, Buffer.alloc(0)));
        clients.delete(socket);
        return;
      }
    }
  });
  socket.on('close', () => clients.delete(socket));
  socket.on('error', () => clients.delete(socket));
}

function broadcast(message) {
  const frame = encodeFrame(OPCODES.TEXT, Buffer.from(JSON.stringify(message)));
  for (const client of clients) {
    try {
      client.write(frame);
    } catch (error) {
      clients.delete(client);
    }
  }
}

function ownerAlive() {
  if (!ownerPid) return true;
  try {
    process.kill(ownerPid, 0);
    return true;
  } catch (error) {
    return error.code === 'EPERM';
  }
}

function startServer() {
  fs.mkdirSync(CONTENT_DIR, { recursive: true });
  fs.mkdirSync(STATE_DIR, { recursive: true });
  const knownFiles = new Set(fs.readdirSync(CONTENT_DIR).filter(file => file.endsWith('.html')));
  const server = http.createServer(handleRequest);
  server.on('upgrade', handleUpgrade);
  const watcher = fs.watch(CONTENT_DIR, (eventType, filename) => {
    if (!filename || !filename.endsWith('.html')) return;
    if (debounceTimers.has(filename)) clearTimeout(debounceTimers.get(filename));
    debounceTimers.set(filename, setTimeout(() => {
      debounceTimers.delete(filename);
      const filePath = path.join(CONTENT_DIR, filename);
      if (!fs.existsSync(filePath)) return;
      touchActivity();
      const firstSeen = !knownFiles.has(filename);
      knownFiles.add(filename);
      if (firstSeen) {
        const eventsFile = path.join(STATE_DIR, 'events');
        if (fs.existsSync(eventsFile)) fs.unlinkSync(eventsFile);
      }
      console.log(JSON.stringify({ type: firstSeen ? 'screen-added' : 'screen-updated', file: filePath }));
      broadcast({ type: 'reload' });
    }, 100));
  });
  watcher.on('error', error => console.error('fs.watch error:', error.message));

  function shutdown(reason) {
    console.log(JSON.stringify({ type: 'server-stopped', reason }));
    const infoFile = path.join(STATE_DIR, 'server-info');
    if (fs.existsSync(infoFile)) fs.unlinkSync(infoFile);
    fs.writeFileSync(path.join(STATE_DIR, 'server-stopped'), JSON.stringify({ reason, timestamp: Date.now() }) + '\n');
    watcher.close();
    clearInterval(lifecycleCheck);
    server.close(() => process.exit(0));
  }

  const lifecycleCheck = setInterval(() => {
    if (!ownerAlive()) shutdown('owner process exited');
    else if (Date.now() - lastActivity > IDLE_TIMEOUT_MS) shutdown('idle timeout');
  }, 60 * 1000);
  lifecycleCheck.unref();
  if (ownerPid) {
    try {
      process.kill(ownerPid, 0);
    } catch (error) {
      if (error.code !== 'EPERM') ownerPid = null;
    }
  }
  server.listen(PORT, HOST, () => {
    const info = JSON.stringify({
      type: 'server-started',
      port: PORT,
      host: HOST,
      url_host: URL_HOST,
      url: 'http://' + URL_HOST + ':' + PORT,
      screen_dir: CONTENT_DIR,
      state_dir: STATE_DIR
    });
    console.log(info);
    fs.writeFileSync(path.join(STATE_DIR, 'server-info'), info + '\n');
  });
}

if (require.main === module) startServer();
module.exports = { computeAcceptKey, encodeFrame, decodeFrame, OPCODES };
