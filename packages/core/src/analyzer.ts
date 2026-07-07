import type * as mupdf from 'mupdf';
import type { PageAnalysis, TextSpan, ImageRegion } from './types.js';

export class Analyzer {
  analyzePage(page: mupdf.PDFPage, pageIndex: number): PageAnalysis {
    const bounds = page.getBounds();
    const stext = page.toStructuredText('preserve-whitespace');
    const textSpans: TextSpan[] = [];

    stext.walk({
      onChar(
        char: string,
        origin: [number, number],
        _font: mupdf.Font,
        size: number,
        quad: [number, number, number, number, number, number, number, number],
        color: mupdf.Color,
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

    const pageAnalysis: PageAnalysis = {
      pageIndex,
      bounds,
      textSpans,
      imageRegions: [],
      isDarkPage: this.isPageDark(textSpans),
    };

    return pageAnalysis;
  }

  private isPageDark(spans: TextSpan[]): boolean {
    if (spans.length === 0) return false;
    let lightCount = 0;
    for (const span of spans) {
      const luminance = this.colorLuminance(span.color);
      if (luminance > 0.5) lightCount++;
    }
    return lightCount / spans.length < 0.3;
  }

  colorLuminance(color: mupdf.Color): number {
    const c = color as [number, number, number];
    if (c.length < 3) return 0;
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2];
  }

  invertColor(color: mupdf.Color): mupdf.Color {
    const c = color as [number, number, number];
    if (c.length < 3) return color;
    return [1 - c[0], 1 - c[1], 1 - c[2]] as mupdf.Color;
  }

  isDarkColor(color: mupdf.Color): boolean {
    return this.colorLuminance(color) < 0.5;
  }
}
