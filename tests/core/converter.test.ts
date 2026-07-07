import { describe, it, expect, beforeAll } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { Converter } from '@pdf-darker/core';

const FIXTURES_DIR = path.resolve(import.meta.dirname, '..', 'fixtures');
const OUTPUT_DIR = path.resolve(import.meta.dirname, '..', 'output');

function ensureDir(dir: string) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

describe('Converter', () => {
  let converter: Converter;

  beforeAll(() => {
    converter = new Converter();
    ensureDir(FIXTURES_DIR);
    ensureDir(OUTPUT_DIR);
  });

  it('converts a simple PDF to dark mode', async () => {
    const inputPath = path.join(FIXTURES_DIR, 'sample-1page.pdf');
    const outputPath = path.join(OUTPUT_DIR, 'dark-sample-1page.pdf');

    const result = await converter.convert(inputPath, outputPath, {
      dpi: 150,
      quality: 90,
      preserveText: true,
      preserveForms: true,
      preserveLinks: true,
    });

    expect(result.success).toBe(true);
    expect(result.pageCount).toBeGreaterThan(0);
    expect(result.fileSizeAfter).toBeGreaterThan(0);
    expect(fs.existsSync(outputPath)).toBe(true);
  }, 30000);

  it('converts a multi-page PDF', async () => {
    const inputPath = path.join(FIXTURES_DIR, 'sample-3page.pdf');
    const outputPath = path.join(OUTPUT_DIR, 'dark-sample-3page.pdf');

    const result = await converter.convert(inputPath, outputPath, {
      dpi: 150,
      quality: 85,
      preserveText: true,
      preserveForms: true,
      preserveLinks: true,
    });

    expect(result.success).toBe(true);
    expect(result.pageCount).toBe(3);
  }, 30000);

  it('converts without text preservation', async () => {
    const inputPath = path.join(FIXTURES_DIR, 'sample-1page.pdf');
    const outputPath = path.join(OUTPUT_DIR, 'dark-sample-notext.pdf');

    const result = await converter.convert(inputPath, outputPath, {
      dpi: 150,
      quality: 90,
      preserveText: false,
      preserveForms: false,
      preserveLinks: false,
    });

    expect(result.success).toBe(true);
  }, 30000);

  it('reports progress via callback', async () => {
    const inputPath = path.join(FIXTURES_DIR, 'sample-3page.pdf');
    const outputPath = path.join(OUTPUT_DIR, 'dark-sample-progress.pdf');
    const progressUpdates: number[] = [];

    await converter.convert(inputPath, outputPath, {
      dpi: 150,
      quality: 90,
      preserveText: true,
      preserveForms: true,
      preserveLinks: true,
    }, (progress) => {
      progressUpdates.push(progress.percent);
    });

    expect(progressUpdates.length).toBeGreaterThan(0);
    expect(progressUpdates[progressUpdates.length - 1]).toBe(95);
  }, 30000);

  it('handles non-existent file gracefully', async () => {
    const result = await converter.convert('/nonexistent/file.pdf', '/tmp/out.pdf', {
      dpi: 150,
      quality: 90,
      preserveText: true,
      preserveForms: true,
      preserveLinks: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
  });
});
