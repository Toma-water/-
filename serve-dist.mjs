// ゼロ依存の静的ファイルサーバー
// 0.0.0.0 でリッスン → スマホからもアクセス可能
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST = path.join(__dirname, 'dist');
const PORT = 4173;
const HOST = '0.0.0.0';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.mjs':  'application/javascript; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg':  'image/svg+xml',
  '.png':  'image/png',
  '.ico':  'image/x-icon',
  '.woff': 'font/woff',
  '.woff2':'font/woff2',
};

function getLocalIPs() {
  const result = [];
  for (const [name, addrs] of Object.entries(os.networkInterfaces())) {
    for (const a of addrs ?? []) {
      if (a.family === 'IPv4' && !a.internal) result.push({ name, address: a.address });
    }
  }
  return result;
}

const server = http.createServer((req, res) => {
  let urlPath = (req.url ?? '/').split('?')[0];
  if (urlPath === '/') urlPath = '/index.html';

  const filePath = path.normalize(path.join(DIST, urlPath));

  // パストラバーサル防止
  if (!filePath.startsWith(DIST + path.sep) && filePath !== DIST) {
    res.writeHead(403); res.end('Forbidden'); return;
  }

  const ext = path.extname(filePath).toLowerCase();
  const isHtml = ext === '.html';

  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const data = fs.readFileSync(filePath);
    res.writeHead(200, {
      'Content-Type': MIME[ext] ?? 'application/octet-stream',
      'Cache-Control': isHtml ? 'no-cache' : 'max-age=31536000,immutable',
    });
    res.end(data);
    return;
  }

  // SPA フォールバック: 不明なパスは index.html を返す
  const idx = path.join(DIST, 'index.html');
  if (fs.existsSync(idx)) {
    const data = fs.readFileSync(idx);
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-cache' });
    res.end(data);
  } else {
    res.writeHead(404);
    res.end('Not found — npm run build を先に実行してください');
  }
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`\nエラー: ポート ${PORT} は既に使用中です。`);
    console.error('別のサーバーを終了してから再試行してください。\n');
  } else {
    console.error('サーバーエラー:', err);
  }
  process.exit(1);
});

server.listen(PORT, HOST, () => {
  const ips = getLocalIPs();
  console.log('\n╔══════════════════════════════════════╗');
  console.log('║   Daily Inquiry Log — サーバー起動  ║');
  console.log('╚══════════════════════════════════════╝\n');
  console.log(`  PC   :  http://localhost:${PORT}/`);
  if (ips.length === 0) {
    console.log('  スマホ: Wi-Fiに接続されていません');
  } else {
    for (const { address, name } of ips) {
      console.log(`  スマホ:  http://${address}:${PORT}/   (${name})`);
    }
  }
  console.log('\n  Ctrl+C で停止\n');
});
