import * as http from 'node:http';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';
import { Converter } from '@pdf-darker/core';

import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_DIR = path.resolve(__dirname, '..', 'dist');
const PORT = parseInt(process.env.PORT || '3000', 10);

const MIME: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.json': 'application/json',
};

const MAX_FILE_SIZE_BYTES = 30 * 1024 * 1024;

const converter = new Converter();

function sendJSON(res: http.ServerResponse, status: number, data: unknown) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
}

async function handleConvert(req: http.IncomingMessage, res: http.ServerResponse) {
  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk as Buffer);
  const body = Buffer.concat(chunks);

  let params: {
    fileData: string;
    fileName: string;
    dpi: number;
    preserveText: boolean;
  };

  try {
    params = JSON.parse(body.toString());
  } catch {
    return sendJSON(res, 400, { error: 'Invalid JSON' });
  }

  const decodedSize = Math.round((params.fileData.length * 3) / 4);
  if (decodedSize > MAX_FILE_SIZE_BYTES) {
    return sendJSON(res, 413, {
      error: `File too large (${Math.round(decodedSize / 1024 / 1024)} MB). Maximum is ${MAX_FILE_SIZE_BYTES / 1024 / 1024} MB.`,
    });
  }

  const inputPath = path.join(os.tmpdir(), `pdf-darker-in-${Date.now()}.pdf`);
  const outputPath = path.join(os.tmpdir(), `pdf-darker-out-${Date.now()}.pdf`);

  try {
    fs.writeFileSync(inputPath, Buffer.from(params.fileData, 'base64'));

    const result = await converter.convert(inputPath, outputPath, {
      dpi: params.dpi || 300,
      quality: 95,
      preserveText: params.preserveText === true,
      preserveForms: true,
      preserveLinks: true,
    });

    if (result.success) {
      const pdfData = fs.readFileSync(outputPath);
      res.writeHead(200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="dark-${params.fileName || 'output.pdf'}"`,
        'X-Result': JSON.stringify(result),
      });
      res.end(pdfData);
    } else {
      sendJSON(res, 500, result);
    }
  } finally {
    try { fs.unlinkSync(inputPath); } catch { /* ignore */ }
    try { fs.unlinkSync(outputPath); } catch { /* ignore */ }
  }
}

function serveStatic(req: http.IncomingMessage, res: http.ServerResponse) {
  const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
  let filePath = url.pathname === '/' ? '/index.html' : url.pathname;
  const fullPath = path.join(DIST_DIR, filePath);

  try {
    const data = fs.readFileSync(fullPath);
    const ext = path.extname(fullPath);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  } catch {
    res.writeHead(404);
    res.end('Not found');
  }
}

export function createServer(): http.Server {
  return http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);

    if (req.method === 'POST' && url.pathname === '/convert') {
      return handleConvert(req, res);
    }

    if ((req.method === 'GET' || req.method === 'HEAD') && url.pathname === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ status: 'ok' }));
    }

    return serveStatic(req, res);
  });
}

const isMainModule = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMainModule) {
  createServer().listen(PORT, () => {
    console.log(`PDF Darker server: http://localhost:${PORT}`);
  });
}
