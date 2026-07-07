export interface DarkModeOptions {
  dpi: number;
  quality: number;
  preserveText: boolean;
  preserveForms: boolean;
  preserveLinks: boolean;
}

export const DEFAULT_DARK_MODE_OPTIONS: DarkModeOptions = {
  dpi: 300,
  quality: 95,
  preserveText: true,
  preserveForms: true,
  preserveLinks: true,
};

export interface ConversionResult {
  success: boolean;
  inputPath: string;
  outputPath: string;
  pageCount: number;
  durationMs: number;
  fileSizeBefore: number;
  fileSizeAfter: number;
  error?: string;
}

export interface ConversionProgress {
  page: number;
  totalPages: number;
  phase: 'analyzing' | 'processing' | 'saving';
  percent: number;
}
