import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import * as http from 'node:http';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { createServer } from '@pdf-darker/ui/server.js';

const FIXTURES_DIR = path.resolve(import.meta.dirname, '..', 'fixtures');

function fetch(
  server: http.Server,
  urlPath: string,
  options?: { method?: string; body?: string; headers?: Record<string, string> },
): Promise<{ status: number; headers: http.IncomingHttpHeaders; body: Buffer }> {
  return new Promise((resolve, reject) => {
    const addr = server.address();
    if (!addr || typeof addr === 'string') {
      return reject(new Error('Server not listening'));
    }
    const req = http.request(
      {
        hostname: '127.0.0.1',
        port: addr.port,
        path: urlPath,
        method: options?.method || 'GET',
        headers: options?.headers || { 'Content-Type': 'application/json' },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on('data', (chunk: Buffer) => chunks.push(chunk));
        res.on('end', () => {
          resolve({
            status: res.statusCode || 0,
            headers: res.headers,
            body: Buffer.concat(chunks),
          });
        });
      },
    );
    req.on('error', reject);
    if (options?.body) req.write(options.body);
    req.end();
  });
}

describe('UI Server', () => {
  let server: http.Server;

  beforeAll(async () => {
    server = createServer();
    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
  });

  afterAll(() => {
    server.close();
  });

  it('serves health endpoint', async () => {
    const res = await fetch(server, '/health');
    expect(res.status).toBe(200);
    expect(JSON.parse(res.body.toString())).toEqual({ status: 'ok' });
  });

  it('returns 404 for unknown path', async () => {
    const res = await fetch(server, '/nonexistent');
    expect(res.status).toBe(404);
    expect(res.body.toString()).toBe('Not found');
  });

  it('rejects invalid JSON on convert', async () => {
    const res = await fetch(server, '/convert', {
      method: 'POST',
      body: 'not-json',
    });
    expect(res.status).toBe(400);
    const data = JSON.parse(res.body.toString());
    expect(data.error).toBe('Invalid JSON');
  });

  it('converts a PDF to dark mode via endpoint', async () => {
    const inputPath = path.join(FIXTURES_DIR, 'sample-1page.pdf');
    const pdfData = fs.readFileSync(inputPath);
    const base64 = pdfData.toString('base64');

    const res = await fetch(server, '/convert', {
      method: 'POST',
      body: JSON.stringify({
        fileData: base64,
        fileName: 'test.pdf',
        dpi: 150,
        preserveText: true,
      }),
    });

    expect(res.status).toBe(200);
    expect(res.headers['content-type']).toBe('application/pdf');
    expect(res.headers['content-disposition']).toContain('dark-test.pdf');
    expect(res.body.slice(0, 5).toString()).toBe('%PDF-');
    expect(res.body.slice(-6).toString().trim()).toMatch(/%%EOF/);
    expect(res.body.length).toBeGreaterThan(1000);
  }, 30000);

  it('rejects oversized files', async () => {
    const fakeBase64 = 'A'.repeat(50_000_000);
    const res = await fetch(server, '/convert', {
      method: 'POST',
      body: JSON.stringify({
        fileData: fakeBase64,
        fileName: 'huge.pdf',
        dpi: 150,
        preserveText: true,
      }),
    });

    expect(res.status).toBe(413);
    const data = JSON.parse(res.body.toString());
    expect(data.error).toContain('too large');
  });

  it('handles OPTIONS preflight request', async () => {
    const res = await fetch(server, '/convert', { method: 'OPTIONS' });
    expect(res.status).toBe(204);
  });
});
