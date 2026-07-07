# pdf-darker — Coding Rules & Commit Convention

## Code Rules

### No Comments
Write self-documenting code. Use clear variable and function names. If logic is complex, explain it in the docs (ARCHITECTURE.md, ALGORITHM.md), not in code comments.

### TypeScript Strictness
- No `any` types — use proper interfaces and type annotations
- Strict mode enabled in tsconfig
- All public APIs must have type declarations
- Use `interface` over `type` where possible

### File Size
- Maximum 300 lines per file
- Split large modules into smaller, single-responsibility files

### ESM Only
- All imports use `import`/`export` syntax
- No `require()` calls
- File extensions in imports: `.js` (even for .ts source files — TypeScript convention)

### No Dead Code
- No unused imports, variables, or parameters
- The linter (`tsc --noEmit`) must pass before commits

## Test Rules

- Every function must have a corresponding test covering the happy path and at least one edge case
- All tests must pass before marking a task as DONE
- Tests go in `tests/<package>/<module>.test.ts`
- Use descriptive test names that explain the scenario being tested

## Commit Convention

Format:
```
<type>(<scope>): <short description>

<optional body>
```

### Types

|Type|When to use|
|---|---|
|`feat`|New feature (core, tui, ui, docs)|
|`fix`|Bug fix|
|`test`|Adding or updating tests|
|`docs`|Documentation only (AGENTS.md, README.md, etc.)|
|`refactor`|Code change that neither fixes a bug nor adds a feature|
|`chore`|Build process, dependency updates, CI configuration|

### Scopes

|Scope|Package|
|---|---|
|`core`|@pdf-darker/core|
|`tui`|@pdf-darker/tui|
|`ui`|@pdf-darker/ui|
|`shared`|@pdf-darker/shared|
|`root`|Root-level config, scripts, docs|

### Examples

```
feat(core): add image luminance inversion for dark mode
fix(tui): handle missing output path argument
test(core): cover empty PDF edge case
docs: update AGENTS.md with new package structure
chore(root): update mupdf to v1.28
```

## Agent Workflow

1. Read AGENTS.md for full context
2. Read ARCHITECTURE.md and ALGORITHM.md for technical details
3. Make changes following these rules
4. Run `pnpm test` — all tests must pass
5. Only then say DONE
