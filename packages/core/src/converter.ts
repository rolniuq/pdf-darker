import * as fs from 'node:fs';
import type { DarkModeOptions, ConversionResult, ConversionProgress } from '@pdf-darker/shared';
import type * as MuPDF from 'mupdf';
import type { TextSpan } from './types.js';
import { Analyzer } from './analyzer.js';

export class Converter {
  private analyzer = new Analyzer();

  async convert(
    inputPath: string,
    outputPath: string,
    options: DarkModeOptions,
    onProgress?: (progress: ConversionProgress) => void,
  ): Promise<ConversionResult> {
    const startTime = Date.now();

    let inputBytes = 0;
    try {
      inputBytes = fs.statSync(inputPath).size;
    } catch {
      return {
        success: false,
        inputPath,
        outputPath,
        pageCount: 0,
        durationMs: Date.now() - startTime,
        fileSizeBefore: 0,
        fileSizeAfter: 0,
        error: `Cannot access input file: ${inputPath}`,
      };
    }

    const mupdf = await this.loadMuPDF();

    let sourceDoc: MuPDF.PDFDocument | null = null;

    try {
      const data = fs.readFileSync(inputPath);
      sourceDoc = new mupdf.PDFDocument(data.buffer);
      const pageCount = sourceDoc.countPages();

      onProgress?.({ page: 0, totalPages: pageCount, phase: 'analyzing', percent: 0 });

      const scale = options.dpi / 72;

      const outBuffer = new mupdf.Buffer();
      const writer = new mupdf.DocumentWriter(outBuffer, 'pdf', '');

      for (let i = 0; i < pageCount; i++) {
        onProgress?.({
          page: i + 1,
          totalPages: pageCount,
          phase: 'processing',
          percent: Math.round(((i + 1) / pageCount) * 100),
        });

        const sourcePage = sourceDoc.loadPage(i) as MuPDF.PDFPage;
        this.processPage(mupdf, sourcePage, writer, scale, options);
        sourcePage.destroy();
      }

      onProgress?.({ page: pageCount, totalPages: pageCount, phase: 'saving', percent: 95 });
      writer.close();

      fs.writeFileSync(outputPath, Buffer.from(outBuffer.asUint8Array()));
      outBuffer.destroy();

      const outputBytes = fs.statSync(outputPath).size;
      const duration = Date.now() - startTime;

      return {
        success: true,
        inputPath,
        outputPath,
        pageCount,
        durationMs: duration,
        fileSizeBefore: inputBytes,
        fileSizeAfter: outputBytes,
      };
    } catch (err) {
      const duration = Date.now() - startTime;
      return {
        success: false,
        inputPath,
        outputPath,
        pageCount: sourceDoc?.countPages() ?? 0,
        durationMs: duration,
        fileSizeBefore: inputBytes,
        fileSizeAfter: 0,
        error: err instanceof Error ? err.message : String(err),
      };
    } finally {
      sourceDoc?.destroy();
    }
  }

  private processPage(
    mupdf: typeof MuPDF,
    sourcePage: MuPDF.PDFPage,
    writer: MuPDF.DocumentWriter,
    scale: number,
    options: DarkModeOptions,
  ): void {
    const bounds = sourcePage.getBounds();
    const pageW = bounds[2] - bounds[0];
    const pageH = bounds[3] - bounds[1];

    const matrix: MuPDF.Matrix = [scale, 0, 0, scale, 0, 0];

    const pixmap = sourcePage.toPixmap(matrix, mupdf.ColorSpace.DeviceRGB, false, true);
    pixmap.invertLuminance();
    pixmap.gamma(1.15);
    const pngBytes = pixmap.asPNG();
    pixmap.destroy();

    const img = new mupdf.Image(pngBytes);
    const imgW = img.getWidth();
    const imgH = img.getHeight();

    const device = writer.beginPage([0, 0, pageW, pageH]);

    const imgCtm: MuPDF.Matrix = [pageW / imgW, 0, 0, pageH / imgH, 0, 0];
    device.fillImage(img, imgCtm, 1.0);

    if (options.preserveText) {
      this.drawHiddenTextLayer(mupdf, sourcePage, device, pageW, pageH);
    }

    writer.endPage();
    img.destroy();
  }

  private drawHiddenTextLayer(
    mupdf: typeof MuPDF,
    sourcePage: MuPDF.PDFPage,
    device: MuPDF.Device,
    pageW: number,
    pageH: number,
  ): void {
    const stext = sourcePage.toStructuredText('preserve-whitespace');
    const textSpans: TextSpan[] = [];

    stext.walk({
      onChar(
        char: string,
        origin: MuPDF.Point,
        _font: MuPDF.Font,
        size: number,
        quad: MuPDF.Quad,
        color: MuPDF.Color,
        bidi: number,
      ) {
        textSpans.push({
          text: char,
          origin: [origin[0], origin[1]],
          fontName: _font.getName(),
          fontSize: size,
          color,
          quad,
          bidi,
        });
      },
    });

    stext.destroy();

    if (textSpans.length === 0) return;

    const ctm: MuPDF.Matrix = [1, 0, 0, 1, 0, 0];
    const whiteSpace: MuPDF.Color = [0.05, 0.05, 0.05];

    let currentFont: MuPDF.Font | null = null;
    let currentFontSize = 0;
    let batchText = '';
    let batchX = 0;
    let batchY = 0;

    for (const span of textSpans) {
      const font = this.getFont(mupdf, span.fontName);
      if (font === null) continue;

      const needFlush =
        currentFont !== font ||
        Math.abs(currentFontSize - span.fontSize) > 0.01 ||
        batchText.length > 100;

      if (needFlush && batchText.length > 0) {
        this.flushText(mupdf, device, currentFont!, currentFontSize, batchText, batchX, batchY, ctm, whiteSpace);
        batchText = '';
      }

      if (batchText.length === 0) {
        batchX = span.origin[0];
        batchY = pageH - span.origin[1];
      }

      currentFont = font;
      currentFontSize = span.fontSize;
      batchText += span.text;
    }

    if (batchText.length > 0 && currentFont) {
      this.flushText(mupdf, device, currentFont, currentFontSize, batchText, batchX, batchY, ctm, whiteSpace);
    }
  }

  private getFont(mupdf: typeof MuPDF, name: string): MuPDF.Font | null {
    const stdFonts = [
      'Times-Roman', 'Times-Bold', 'Times-Italic', 'Times-BoldItalic',
      'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique', 'Helvetica-BoldOblique',
      'Courier', 'Courier-Bold', 'Courier-Oblique', 'Courier-BoldOblique',
      'Symbol', 'ZapfDingbats',
    ];

    for (const std of stdFonts) {
      try {
        const font = new mupdf.Font(std);
        return font;
      } catch {
        continue;
      }
    }

    try {
      const font = new mupdf.Font('Helvetica');
      return font;
    } catch {
      return null;
    }
  }

  private flushText(
    mupdf: typeof MuPDF,
    device: MuPDF.Device,
    font: MuPDF.Font,
    size: number,
    text: string,
    x: number,
    y: number,
    ctm: MuPDF.Matrix,
    color: MuPDF.Color,
  ): void {
    try {
      const trm: MuPDF.Matrix = [size, 0, 0, size, x, y];
      const textObj = new mupdf.Text();
      textObj.showString(font, trm, text, 0);
      device.fillText(textObj, ctm, mupdf.ColorSpace.DeviceRGB, color, 1.0);
      textObj.destroy();
    } catch {
      // silently skip text that can't be rendered
    }
  }

  private async loadMuPDF(): Promise<typeof MuPDF> {
    return await import('mupdf');
  }
}
