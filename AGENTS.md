# pdf-darker — Agent Context File

This file documents the complete architecture, patterns, and design decisions of **pdf-darker**, a TypeScript-based PDF dark mode converter with both a TUI (terminal) and web UI.

Every AI agent must read this file before making changes. It contains the rules, architecture, and conventions.

---

## 1. Project Identity

**Purpose:** Convert PDF files to dark mode with perfect rendering fidelity. Text remains selectable, links stay clickable, forms remain functional.

**Stack:** TypeScript 5.9+, pnpm workspaces, Ink 7.1 (TUI), React 19 + Vite 6 (web UI), MuPDF.js WASM (PDF engine)

**Repository:** `/Users/raymond/Workspace/side/pdf-darker`

---

## 2. Non-Negotiable Rules

### 2.1 Code Rules
- **No comments in code.** Write self-documenting code with clear variable/function names. Logic explanations belong in docs/.
- **All tests must pass** before an agent says DONE. Run `pnpm test`.
- **Every function must have a corresponding test** for the happy path and at least one edge case.
- **No `any` types.** Use strict TypeScript with proper interfaces.
- **Files under 300 lines.** Split large files into modules.
- **ESM only.** All `import`/`export`, no `require()`.
- **No unused imports or variables.** The linter (`tsc --noEmit`) must pass.

### 2.2 Commit Convention
```
<type>(<scope>): <short description>

<optional body>
```

Types:
- `feat` — new feature (core, tui, ui, docs)
- `fix` — bug fix
- `test` — adding or updating tests
- `docs` — documentation only
- `refactor` — code change that neither fixes nor adds
- `chore` — build, deps, CI

Scopes: `core`, `tui`, `ui`, `shared`, `root`

Examples:
```
feat(core): add image luminance inversion for dark mode
fix(tui): handle missing output path argument
test(core): cover empty PDF edge case
docs: update AGENTS.md with new package structure
```

### 2.3 Agent Workflow
1. Read AGENTS.md (this file) to understand full context
2. Read the specific package docs (ARCHITECTURE.md, ALGORITHM.md)
3. Make changes following the rules
4. Run `pnpm test` — all tests must pass
5. Only then say DONE

---

## 3. Directory Structure

```
pdf-darker/
├── package.json                       # Root: scripts, bin, devDeps
├── pnpm-workspace.yaml                # Workspace definition
├── tsconfig.base.json                 # Shared TS config
├── vitest.config.ts                   # Test configuration
├── AGENTS.md                          # THIS FILE
├── README.md                          # Quick start
├── ARCHITECTURE.md                    # Architecture deep-dive
├── ALGORITHM.md                       # Dark mode algorithm
├── RULES.md                           # Coding rules & conventions
├── .gitignore
├── scripts/
│   └── generate-fixtures.mjs          # Test PDF generator
├── tests/
│   ├── core/
│   │   └── converter.test.ts          # Core engine tests
│   ├── fixtures/                      # Test PDF files (generated)
│   └── output/                        # Test output (gitignored)
├── packages/
│   ├── core/                          # @pdf-darker/core
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── src/
│   │       ├── index.ts               # Public exports
│   │       ├── types.ts               # Internal types
│   │       ├── analyzer.ts            # Color analysis engine
│   │       └── converter.ts           # Dark mode conversion engine
│   ├── tui/                           # @pdf-darker/tui (Ink TUI)
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── src/
│   │       ├── index.tsx              # CLI entry
│   │       ├── app.tsx                # Root component
│   │       └── components/
│   │           ├── ProgressBar.tsx
│   │           ├── FileSelector.tsx
│   │           └── ResultSummary.tsx
│   ├── ui/                            # @pdf-darker/ui (Web UI)
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   ├── tsconfig.server.json
│   │   └── src/
│   │       ├── index.html
│   │       ├── main.tsx
│   │       ├── App.tsx                # React web app
│   │       └── server.ts              # HTTP server for conversion
│   └── shared/                        # @pdf-darker/shared
│       ├── package.json
│       ├── tsconfig.json
│       └── src/
│           └── index.ts               # Shared types & constants
```

---

## 4. Package Architecture

### 4.1 Layer Dependencies
```
@pdf-darker/shared  (types, constants — zero deps)
        ↑
@pdf-darker/core    (converter, analyzer — depends on shared + mupdf)
        ↑
┌───────┴───────┐
@pdf-darker/tui  @pdf-darker/ui
(Ink TUI)        (React Web + HTTP server)
```

### 4.2 Core Package (`@pdf-darker/core`)

**Dependency:** `mupdf` (official MuPDF WASM — same C engine as PyMuPDF)

**Entry point:** `src/index.ts` exports:
- `Converter` — main dark mode conversion engine
- `Analyzer` — color analysis utility

**Key classes:**

|Class|File|Responsibility|
|---|---|---|
|`Converter`|`converter.ts`|Opens PDF, iterates pages, renders + inverts + saves|
|`Analyzer`|`analyzer.ts`|Extracts structured text, analyzes colors, detects dark/light pages|

### 4.3 TUI Package (`@pdf-darker/tui`)

**Dependencies:** Ink 7.1, React 19, meow (CLI parser)

**Entry:** `src/index.tsx` — meow CLI parser → renders `<App>` component

**Components:**
- `App` — orchestrator, runs conversion, displays progress + result
- `ProgressBar` — animated progress bar showing page/phase/percent
- `ResultSummary` — formatted result panel with file sizes, timing
- `FileSelector` — interactive file path input (for interactive mode)

### 4.4 UI Package (`@pdf-darker/ui`)

**Dependencies:** React 19, Vite 6 (frontend), core (backend)

**Frontend:** `src/App.tsx` — drag-and-drop file upload → sends to server → downloads result

**Server:** `src/server.ts` — HTTP server that accepts base64-encoded PDF → runs Converter → returns converted PDF

---

## 5. The Dark Mode Algorithm

See `ALGORITHM.md` for the full detailed breakdown. High-level flow:

```
Input PDF
  │
  ▼
mupdf.PDFDocument.openDocument(data)
  │
  ▼
For each page:
  │
  ├─ Render page to Pixmap (RGB, specified DPI)
  ├─ Apply invertLuminance() + gamma(1.15)
  ├─ Convert Pixmap to PNG bytes
  ├─ Create a new page in output DocumentWriter
  ├─ Draw inverted PNG image covering full page
  ├─ Walk StructuredText from original page
  │   └─ Draw hidden text overlay (dark gray, same positions)
  └─ End page
  │
  ▼
DocumentWriter.close() → Buffer holds PDF
  │
  ▼
Output dark PDF file
```

### Why this approach:
- **invertLuminance()** preserves hue while inverting brightness — gives natural dark mode look
- **gamma(1.15)** boosts midtones slightly for better readability
- **Hidden text overlay** makes text selectable/searchable (white text on white background — invisible but present in content stream)
- **MuPDF engine** ensures pixel-perfect rendering identical to the original PDF

---

## 6. Configuration

The `DarkModeOptions` interface (from `@pdf-darker/shared`):

|Option|Type|Default|Description|
|---|---|---|---|
|`dpi`|number|300|Rendering resolution (150=draft, 300=standard, 600=high)|
|`quality`|number|95|JPEG/PNG compression quality|
|`preserveText`|boolean|true|Add hidden text layer for selectability|
|`preserveForms`|boolean|true|Flatten form fields (not yet implemented)|
|`preserveLinks`|boolean|true|Preserve hyperlinks (not yet implemented)|

---

## 7. Testing

**Framework:** Vitest v3

**Run:** `pnpm test`

**Coverage:** Tests cover:
- Single-page PDF conversion
- Multi-page PDF conversion
- Text preservation toggle
- Progress callback verification
- Error handling for missing files

**Adding tests:**
- Place tests in `tests/<package>/<module>.test.ts`
- Test files use imports from workspace packages (e.g., `@pdf-darker/core`)
- Always verify `result.success === true` for happy paths
- Always test at least one error/edge case

---

## 8. Known Limitations

|Issue|Status|Notes|
|---|---|---|
|Output size larger than input|Expected|Image-based rendering; compression planned|
|Form preservation|Planned|Need to copy widget annotations|
|Link preservation|Planned|Need to copy link annotations from original pages|
|Font embedding in text layer|Partial|Uses Helvetica for hidden text; correct font mapping planned|
|Web UI requires local server|Design|Core uses Node.js `fs`; browser-only is a future enhancement|
|Undo/Redo|Not planned|CLI tool, one-shot conversion|

---

## 9. Quick Reference — Commands

```bash
pnpm build          # Build all packages
pnpm test           # Run all tests
pnpm convert <in> [out]   # CLI conversion via TUI
pnpm server         # Start web UI server on :3000
pnpm fixtures       # Regenerate test PDFs
```

---

## 10. Key Libraries

|Library|Version|Purpose|
|---|---|---|
|`mupdf`|^1.28|PDF rendering, analysis, creation (WASM)|
|`ink`|^7.1|React renderer for terminal UI|
|`react`|^19.2|UI framework (shared between TUI + web)|
|`meow`|^13.0|CLI argument parser|
|`vite`|^6.0|Frontend build tool|
|`vitest`|^3.0|Test framework|
|`typescript`|^5.9|Type checking|
