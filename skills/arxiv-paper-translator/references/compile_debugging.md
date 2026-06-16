# Compile Debugging

Read this file when:
- translated LaTeX compiles with errors or warnings
- citations or refs show `?` / `??`
- `latexmk` exits non-zero
- Windows PDF locking or bibliography backend issues appear

## Recommended Entry Points

On Windows PowerShell, prefer the helper script:

```powershell
& "$PSScriptRoot\..\scripts\compile_ps1.ps1" -WorkDir . -MainTex main.tex
```

If you are working manually, prefer:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

Do not force `-bibtex` on papers that use `biblatex`/`biber`.

## Diagnose in This Order

1. Resolve fatal LaTeX structure errors first.
2. Verify bibliography backend and whether `.bbl` is generated/read.
3. Check for duplicate labels or other non-fatal structural warnings that still break references.
4. Re-run the full compile chain.
5. Check the final PDF for `?` / `??`.

## Fast Checks

PowerShell log scan:

```powershell
Select-String -Path .\main.log -Pattern `
  'undefined citations', `
  'Citation .* undefined', `
  'There were undefined citations', `
  'undefined references', `
  'multiply-defined labels', `
  'Label .* multiply defined', `
  '! LaTeX Error', `
  'File ended while scanning', `
  'ended by \\end\{document\}'
```

If `pdftotext` is available:

```powershell
pdftotext .\main.pdf - | rg '\?\?|\(\?\)|\(\?\?\)|（\?）|（\?\?）'
```

## Backend Detection

Treat these patterns as `biber` indicators:
- `\usepackage[...,backend=biber]{biblatex}`
- `\addbibresource{...}`
- `\printbibliography`

Treat these patterns as traditional BibTeX indicators:
- `\bibliography{...}`
- `\bibliographystyle{...}`
- `natbib` without `biblatex`

If unsure, let `latexmk` auto-detect first. Only fall back to manual `bibtex`/`biber` commands when the automatic pass is unclear.

Manual fallback for `biber` projects:

```bash
xelatex main.tex
biber main
xelatex main.tex
xelatex main.tex
```

Manual fallback for traditional BibTeX projects:

```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

## Critical Failure Modes

### `.bbl` missing

Meaning:
- bibliography backend did not run
- backend ran against the wrong main file
- backend failed on malformed `.bib` data

Actions:
- inspect `<main>.blg` or biber output
- confirm backend choice
- rerun the full chain after fixing the root cause

### `.bbl` is read but citations still show `?`

Meaning:
- this is often not a bibliography problem
- a later fatal LaTeX error prevented the final XeLaTeX pass from finishing

Common causes:
- unmatched `\begin{...}` / `\end{...}`
- unclosed braces
- appendix float environments not closed
- `File ended while scanning...`

Action:
- search the log for the first fatal error after `.bbl` is read
- fix that structure error
- rerun the full compile chain

### `Package natbib Warning: Citation ... undefined` for nearly every citation

Meaning:
- if this persists in the final log, treat it as unresolved
- if `.bbl` exists and is read, suspect an interrupted final pass rather than missing bibliography data

Action:
- do not immediately copy `.bbl` or edit citations
- inspect for later `! LaTeX Error`

### `LaTeX Warning: There were multiply-defined labels`

Meaning:
- at least two active `\label{...}` definitions share the same key
- references may silently point to the wrong figure/table/section

Action:
- search all `.tex` files for repeated label keys
- keep one canonical key per referenced object
- rerun XeLaTeX twice after the fix

## Common Fixes

### PDF locked on Windows

Symptom:
- cannot overwrite `main.pdf`

Fix:
- close the PDF viewer and rerun compilation

### Duplicate `\bibdata`

Symptom:
- BibTeX reports `Illegal, another \bibdata command`

Fix:
- inspect `.aux`
- remove duplicate bibliography directives at the source
- delete stale aux files if needed and rerun

### `@software` entries break BibTeX

Symptom:
- traditional BibTeX stops on unsupported entry type

Fix:
- convert `@software` to `@misc`
- or switch to a `biblatex` pipeline if the paper already uses it

### `microtype` tracking fails under XeLaTeX

Symptom:
- `The tracking feature only works with pdftex`

Fix:

```latex
\PassOptionsToPackage{tracking=false}{microtype}
```

Place it before `\documentclass`.

If the error persists, inspect copied `.cls/.sty` files for `microtype`, `tracking=`, and `\DisableLigatures`. Some templates force incompatible `microtype` behavior from the class file itself, so fixing `main.tex` alone is not enough.

### Rendered PDF still shows English labels after source translation

Symptom:
- the PDF compiles, but visible labels such as `Figure`, `Table`, `References`, `Abstract`, `Appendix`, `Under review`, or `Preprint` still appear in English

Meaning:
- the untranslated text may come from copied `.cls/.sty` files rather than from `main.tex`
- source-level English audits can pass while rendered output is still wrong

Fix:
- inspect copied `.cls/.sty` files for the visible English string and localize or override it
- check bibliography-heading commands such as `\refname` and `\bibname`
- rerun XeLaTeX after the template fix and inspect the regenerated PDF again

### PDF exists but Chinese is missing or blank

Symptom:
- `latexmk` succeeds and a PDF exists
- source text is Chinese
- rendered pages or `pdftotext` show missing Chinese, blank spaces, or only English identifiers/citations

Meaning:
- this is usually a font embedding/rendering failure, not a translation failure
- a minimal CJK file may pass while the full template still fails because template font packages changed `fontspec` state

Actions:
- run `pdffonts main.pdf` and confirm Chinese fonts such as `SimSun`, `SimHei`, `KaiTi`, or Fandol are embedded
- render at least page 1 with `pdftoppm` and inspect the PNG
- search the log for `Missing character`, `fontspec Error`, and CJK font warnings
- on Windows, prefer direct `C:/Windows/Fonts/*.ttc/*.ttf` font-file configuration
- if the template loads `newtxtext`, disable it in the copied template or bind CJK fonts after all template font packages
- recompile and rerender before claiming completion

## Last-Resort Workaround

If bibliography generation genuinely fails and arXiv source includes a precompiled `.bbl`, copy the original `.bbl` from `paper_source/` to `paper_cn/`.

Use this only after:
- checking the correct backend
- checking `.blg` / biber output
- checking for later fatal LaTeX errors
