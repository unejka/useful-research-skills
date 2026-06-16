# Layout Preservation

Use this reference when mapping the original paper layout, switching templates, or auditing the rendered Chinese PDF. Keep the rule simple: the translated PDF must match the original paper's column count. Two-column source stays two-column; single-column source stays single-column.

## Fast Layout Contract

Record these facts before editing:

- Main file and `\documentclass` line.
- Class/template name, e.g. `article`, `IEEEtran`, `aaai2026`, `neurips`, `llncs`, `elsarticle`.
- Paper options: `twocolumn`, `onecolumn`, `preprint`, `review`, `conference`, `letterpaper`, `a4paper`, font size.
- Explicit switches: `\twocolumn`, `\onecolumn`, `\begin{strip}`, `\clearpage` around appendix/supplement.
- Float span: `figure`/`table` vs `figure*`/`table*`.
- Rendered original PDF layout if available. When source clues conflict, trust rendered PDF.

PowerShell probe:

```powershell
Get-ChildItem .\paper_source -Recurse -Include *.tex,*.sty,*.cls |
  Select-String -Pattern '\\documentclass|twocolumn|onecolumn|\\twocolumn|\\onecolumn|\\begin\{figure\*\}|\\begin\{table\*\}|\\begin\{strip\}' |
  Select-Object Path, LineNumber, Line
```

## Layout Decisions

Prefer this order:

1. Keep the original class/style and patch CJK/XeLaTeX issues.
2. If the original template is too fragile, create a minimal wrapper that preserves the original layout contract.
3. Only change column count if the user explicitly requests it.

Fallback wrapper examples:

```latex
% Two-column source
\documentclass[10pt,twocolumn,letterpaper]{article}
\usepackage[letterpaper,top=0.75in,bottom=1in,left=0.75in,right=0.75in,columnsep=0.25in]{geometry}
```

```latex
% Single-column source
\documentclass[11pt,letterpaper]{article}
\usepackage[letterpaper,margin=1in]{geometry}
```

For a two-column wrapper:

- `\maketitle` normally spans both columns in `article[twocolumn]`.
- Keep wide figures/tables as `figure*`/`table*`.
- Convert a single-column table that is too wide with `\resizebox{\linewidth}{!}{...}`.
- Keep important overview figures wide when the original uses `figure*`.
- Do not use a single-column wrapper just because it compiles faster.

For a single-column wrapper:

- Do not add `twocolumn` unless the user asks.
- Preserve full-width equations, tables, and figures without squeezing them into column width.

## Rendered Verification

After compilation, render at least:

- Page 1.
- One body page with equations/tables.
- One appendix/supplement page if present.

Commands:

```powershell
pdftoppm -png -f 1 -l 1 -singlefile .\<main>.pdf .\verify_page1
pdftoppm -png -f 2 -l 2 -singlefile .\<main>.pdf .\verify_page2
pdftoppm -png -f 6 -l 6 -singlefile .\<main>.pdf .\verify_page6
```

Check visually:

- Body column count matches the original.
- Title/abstract placement is reasonable for the original template.
- Wide figures/tables are not clipped.
- Captions and section headings remain readable.
- No accidental blank page or one-column-only body appears after a template fallback.

## Speed Notes

- Decide the layout contract once before translation and pass it to all translation batches.
- Avoid repeated full-template debugging while translating text. Translate in the copied source, then do one focused CJK/layout compile pass.
- If a monolithic source is large, split translation by top-level section boundaries but keep shared preamble/layout edits in one owner file.
- For a two-column source with many wide tables, mark table risk during mapping so table fixes can be batched after prose translation.
