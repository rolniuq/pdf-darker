# pdf-darker

Convert PDF files to dark mode with pixel-perfect rendering and preserved text layer.

Built with **MuPDF.js** (the same C engine as PyMuPDF) — no wrong text, no wrong fonts.

## Install

```bash
npm install -g pdf-darker
```

Or use directly with pnpm:

```bash
git clone <repo>
cd pdf-darker
pnpm install
pnpm build
```

## Usage

### CLI (TUI)

```bash
# Basic conversion (output: input-dark.pdf)
pnpm convert input.pdf

# Specify output path
pnpm convert input.pdf output-dark.pdf

# With options
pnpm convert input.pdf --dpi 200 --no-text

# Or globally installed
pdf-darker input.pdf output-dark.pdf
```

### Web UI

```bash
# Start the web server on http://localhost:3000
pnpm server
```

### Programmatic API

```typescript
import { Converter } from '@pdf-darker/core';

const converter = new Converter();
const result = await converter.convert(
  'input.pdf',
  'output-dark.pdf',
  {
    dpi: 300,
    quality: 95,
    preserveText: true,
    preserveForms: true,
    preserveLinks: true,
  },
  (progress) => {
    console.log(`Page ${progress.page}/${progress.totalPages} — ${progress.phase}`);
  },
);

console.log(`Done! ${result.pageCount} pages in ${result.durationMs}ms`);
```

## Options

|Flag|Type|Default|Description|
|---|---|---|---|
|`--dpi`, `-d`|number|300|Rendering resolution|
|`--quality`, `-q`|number|95|Image quality (1–100)|
|`--no-text`|boolean|true|Disable hidden text layer|

## How It Works

1. Render each page to a high-resolution image via MuPDF
2. Apply **luminance inversion** — preserves hue while inverting brightness
3. Apply **gamma correction** — boosts midtones for readability
4. Create new PDF with inverted page images
5. Overlay **hidden text layer** — keeps text selectable and searchable

## Architecture

```
packages/
├── shared/     — Types and constants
├── core/       — PDF engine (MuPDF.js WASM)
├── tui/        — Terminal UI (Ink + React)
└── ui/         — Web UI (React + Vite + HTTP server)
```

See `ARCHITECTURE.md` and `ALGORITHM.md` for details.

## License

AGPL-3.0 (same as MuPDF.js)
