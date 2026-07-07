import type { Color, Rect } from 'mupdf';

export interface TextSpan {
  text: string;
  origin: [number, number];
  fontName: string;
  fontSize: number;
  color: Color;
  quad: [number, number, number, number, number, number, number, number];
  bidi: number;
}

export interface PageAnalysis {
  pageIndex: number;
  bounds: Rect;
  textSpans: TextSpan[];
  imageRegions: ImageRegion[];
  isDarkPage: boolean;
}

export interface ImageRegion {
  index: number;
  bbox: Rect;
  width: number;
  height: number;
}
