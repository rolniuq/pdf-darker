# pdf-darker Architecture

## Overview

pdf-darker is a TypeScript monorepo with four packages. The core PDF engine uses **MuPDF.js** — official WebAssembly bindings for the MuPDF C library (same engine as PyMuPDF).

```
┌──────────────────────────────────────────────────┐
│                    pdf-darker                     │
│                                                   │
│  ┌──────────────────────┐  ┌───────────────────┐ │
│  │     @pdf-darker/tui  │  │  @pdf-darker/ui   │ │
│  │     (Ink + React)    │  │  (React + Vite)   │ │
│  └──────────┬───────────┘  └────────┬──────────┘ │
│             │                       │             │
│             └──────┬────────────────┘             │
│                    │                              │
│          ┌─────────▼──────────┐                   │
│          │ @pdf-darker/core   │                   │
│          │                    │                   │
│          │  ┌──────────────┐ │                   │
│          │  │   Converter  │ │  Main conversion  │
│          │  │   Analyzer   │ │  Color/text analysis│
│          │  └──────┬───────┘ │                   │
│          │         │         │                    │
│          │  ┌──────▼───────┐ │                    │
│          │  │    mupdf     │ │  WASM binary       │
│          │  │  (MuPDF.js)  │ │  (13 MB)           │
│          │  └──────────────┘ │                    │
│          └──────────────────┘                     │
│                                                   │
│  ┌──────────────────────────────────────────┐     │
│  │ @pdf-darker/shared (types + constants)   │     │
│  └──────────────────────────────────────────┘     │
└──────────────────────────────────────────────────┘
```

## Package Details

### @pdf-darker/shared

Zero-dependency package with shared TypeScript types and constants.

Key exports:
- `DarkModeOptions` — configuration interface
- `ConversionResult` — result data structure
- `ConversionProgress` — progress callback data
- `DEFAULT_DARK_MODE_OPTIONS` — sensible defaults

### @pdf-darker/core

The PDF dark mode engine. Uses `mupdf` (MuPDF.js WASM) for all PDF operations.

**File mapping:**

|File|Class|Responsibility|
|---|---|---|
|`src/converter.ts`|`Converter`|Opens PDF, iterates pages, calls render → invert → save pipeline|
|`src/analyzer.ts`|`Analyzer`|Walks structured text, analyzes color distribution, detects dark pages|
|`src/types.ts`|—|Internal types: TextSpan, PageAnalysis, ImageRegion|

**Converter workflow:**

```
Converter.convert(inputPath, outputPath, options, onProgress)
  │
  ├─ 1. Read file via fs.readFileSync
  ├─ 2. Open with new mupdf.PDFDocument(data.buffer)
  ├─ 3. For each page:
  │     ├─ Render page to Pixmap (RGB, DPI-scaled)
  │     ├─ applyDarkModeToPixmap():
  │     │   ├─ pixmap.invertLuminance() — preserves hue
  │     │   └─ pixmap.gamma(1.15) — boost midtones
  │     ├─ pixmap.asPNG() → Uint8Array
  │     ├─ new mupdf.Image(pngData) — create image object
  │     ├─ Create output page via DocumentWriter
  │     ├─ device.fillImage() — draw inverted image
  │     └─ if preserveText: drawHiddenTextLayer()
  │           └─ Walk StructuredText → draw dark gray text overlay
  ├─ 4. writer.close() → Buffer contains PDF
  └─ 5. fs.writeFileSync(outputPath, buffer)
```

### @pdf-darker/tui

Terminal user interface built with **Ink** (React for CLI).

**Entry point:** `src/index.tsx`
- Uses `meow` for CLI argument parsing
- Renders `<App>` component via Ink's `render()`
- Supports `--dpi`, `--quality`, `--no-text` flags

**Component tree:**
```
<App>
  ├── <Text> — Header
  ├── <Box> — File paths
  ├── <ProgressBar> — Animated progress (page/phase/percent)
  └── <ResultSummary> — Final result (success/fail, timing, sizes)
```

### @pdf-darker/ui

Web UI with a React frontend and a local HTTP server backend.

**Frontend** (`src/App.tsx`):
- File selection via `<input type="file">`
- DPI dropdown (150/300/600)
- Preserve text toggle
- Sends file as base64 JSON to `/convert` endpoint
- Receives converted PDF as download

**Server** (`src/server.ts`):
- Serves static files from `dist/`
- `POST /convert` — accepts base64-encoded PDF → runs Converter → returns converted PDF
- Default port 3000

**Vite dev proxy:** In dev mode, `/convert` requests are proxied to `localhost:3000`.

## Data Flow

```
User Input (CLI args or file upload)
        │
        ▼
TUI/UI package
        │
        ▼
Converter.convert()
   ├─  Analyzer.analyzePage() — optional color analysis
   └─  processPage() — render → invert → write output
        │
        ▼
Output PDF file (dark mode)
```

## Key Design Decisions

1. **MuPDF.js over pdf-lib:** MuPDF is the same C engine as PyMuPDF, giving identical rendering fidelity. pdf-lib cannot extract or modify existing text colors.

2. **Pixmap rendering + inversion:** The simplest reliable approach. Renders each page to an image, inverts luminance, embeds in new PDF. Guarantees no text/font corruption.

3. **DocumentWriter over PDFDocument for output:** DocumentWriter handles all the low-level PDF structure. We just draw on the device API.

4. **Dark gray text overlay for selectability:** Text drawn in [0.05, 0.05, 0.05] on dark background is invisible to the eye but present in the content stream. PDF viewers can still select/copy it.

5. **Ink for TUI:** Same React mental model as the web UI. Shared components possible (not yet).
