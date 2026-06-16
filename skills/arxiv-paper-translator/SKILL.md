---
name: arxiv-paper-translator
description: >-
  Translate academic papers from arXiv to Chinese. MUST use this skill when the
  user provides an arXiv URL or arXiv ID and asks to translate, localize,
  compile, or summarize the paper in Chinese. Default deliverable is a translated
  paper_cn LaTeX source tree plus a compiled, layout-matched, and
  rendered-verified Chinese PDF. Use for arXiv source extraction,
  LaTeX-preserving academic translation, original single/double-column layout
  preservation, Chinese XeLaTeX/CJK fixes, bibliography-aware compilation, and
  optional technical reports.
---

# arXiv Paper Translator

Translate arXiv papers by downloading source, translating reader-facing LaTeX content, compiling with XeLaTeX, and verifying the rendered Chinese PDF. Optimize for throughput: load only the references needed for the current stage, and avoid reading the entire troubleshooting corpus up front.

## Progressive Disclosure Map

Read these files only when the trigger applies:

- `references/translation_guidelines.md`: before translating unfamiliar LaTeX structures, algorithms, prompts, tables, or dense math prose.
- `references/translation_prompt.md`: when delegating or batching translation work.
- `references/layout_preservation.md`: when detecting original column count/template layout, replacing a fragile template with a wrapper, or reviewing rendered layout fidelity.
- `references/review_checklist.md`: before source-level completion claims, or when audits show suspicious English/LaTeX hazards.
- `references/chinese_support.md`: only when adding or repairing CJK/XeLaTeX support, fonts, template labels, or rendered Chinese output.
- `references/compile_debugging.md`: only after `latexmk`/BibTeX/Biber/PDF rendering fails or shows unresolved refs/citations.
- `references/summary_prompt.md` and `assets/report_template.md`: only when the user requests a technical report.

Do not load every reference at startup. Start with the fast path below, then pull detail files on demand.

## Fast Path

1. **Resolve paper metadata**
   - Extract `ARXIV_ID` from the URL or ID.
   - Create `arXiv_<ARXIV_ID>/paper_source` and `arXiv_<ARXIV_ID>/paper_cn`.
   - Download from `https://arxiv.org/e-print/<ARXIV_ID>`.
   - On Windows, use PowerShell-native commands first.

2. **Download with fallbacks**
   - Try `curl.exe -L`.
   - If the download resets or produces a bad archive, retry with `Invoke-WebRequest`.
   - Extract with `tar -xzf`; if extraction fails and the file is plain TeX, store it as the main `.tex`.

3. **Map the source**
   - Find the main file: `rg -l "\\documentclass" paper_source -g "*.tex"` or PowerShell `Select-String`.
   - List `\input`/`\include` dependencies, section files, table files, figures, `.bib`, `.bbl`, `.sty`, and `.cls`.
   - Detect and record the original layout contract before editing: main class/template, paper size, one-column vs two-column, title/abstract span, and which floats are `figure*`/`table*`.
   - The final translated PDF must preserve the original column count: two-column source -> two-column Chinese PDF; single-column source -> single-column Chinese PDF. If this is ambiguous or a wrapper template is needed, read `references/layout_preservation.md`.
   - Build a short terminology table from title, abstract, headings, and repeated technical terms.

4. **Copy before editing**
   - Copy all source files into `paper_cn/`.
   - Edit only the `paper_cn/` copy.

5. **Translate in throughput order**
   - Translate title, abstract, introduction, and terminology first to stabilize style.
   - Preserve layout commands and float span while translating (`twocolumn`, `onecolumn`, `figure*`, `table*`, class options, `\maketitle`, and abstract placement).
   - Translate independent section/table files in parallel when current higher-priority instructions permit subagents; otherwise batch locally by file.
   - Assign disjoint write sets. Never let two workers edit the same file.
   - For a monolithic `.tex`, split only at safe top-level section boundaries, translate chunks, verify chunk files from disk, then reassemble once.
   - For speed, keep a single terminology/layout note and pass only the relevant section scope to each translation batch; do not reload every reference for every chunk.

6. **Review source**
   - Run structural and active-English audits before compiling.
   - Treat audit hits as a queue, not a blind replacement list.
   - Protected English may remain: model/dataset/benchmark names, author/institution names, citation keys, labels, URLs, code, schema, executable prompts, and image-baked text.
   - Translate surrounding narrative, captions, and headings. Preserve executable prompt/schema bodies when translating them may change semantics, unless the user asks for a reader-only full localization.

7. **Compile**
   - Prefer `latexmk -xelatex -interaction=nonstopmode -halt-on-error <main>.tex`.
   - Let `latexmk` run BibTeX/Biber when possible.
   - Prefer repairing the original copied template over switching templates. If a fallback wrapper is necessary, preserve the recorded original layout contract, especially column count.
   - If it fails, read `references/compile_debugging.md`.

8. **Verify rendered PDF**
   - Confirm PDF exists in `paper_cn/`.
   - Inspect the PDF or rendered page images, not just exit code.
   - Verify rendered layout matches the original paper at the column-count level and broad float behavior: if the source body was two-column, body pages in the Chinese PDF must be two-column; if it was single-column, the Chinese PDF must remain single-column.
   - Check that Chinese appears in the title/abstract and at least two body/appendix locations.
   - Run a log scan for fatal errors, unresolved citations/refs, and missing CJK glyphs.

## Windows Commands

```powershell
$ARXIV_ID = "2605.05185v1"
New-Item -ItemType Directory -Force "arXiv_$ARXIV_ID\paper_source" | Out-Null
curl.exe -L "https://arxiv.org/e-print/$ARXIV_ID" -o "arXiv_$ARXIV_ID\paper_source.tar.gz"
# Fallback if curl resets:
# Invoke-WebRequest "https://arxiv.org/e-print/$ARXIV_ID" -OutFile "arXiv_$ARXIV_ID\paper_source.tar.gz"
tar -xzf "arXiv_$ARXIV_ID\paper_source.tar.gz" -C "arXiv_$ARXIV_ID\paper_source"

New-Item -ItemType Directory -Force "arXiv_$ARXIV_ID\paper_cn" | Out-Null
Copy-Item "arXiv_$ARXIV_ID\paper_source\*" "arXiv_$ARXIV_ID\paper_cn" -Recurse -Force
```

Use `rg` when available. If bundled `rg.exe` fails on Windows, fall back to:

```powershell
Get-ChildItem .\paper_cn -Recurse -Filter *.tex |
  Select-String -Pattern "\\documentclass|\\input|\\include|\\section"
```

Quick layout probes:

```powershell
Get-ChildItem .\paper_source -Recurse -Include *.tex,*.sty,*.cls |
  Select-String -Pattern '\\documentclass|twocolumn|onecolumn|\\begin\{figure\*\}|\\begin\{table\*\}|\\twocolumn|\\onecolumn' |
  Select-Object Path, LineNumber, Line
```

## Source Audits

Run these before compiling:

```powershell
# Read-tool line-number contamination
Get-ChildItem .\paper_cn -Recurse -Filter *.tex |
  Select-String -Pattern '^\s*[0-9]+:\s'

# Macro directly followed by CJK, a common xeCJK catcode hazard
Get-ChildItem .\paper_cn -Recurse -Filter *.tex |
  Select-String -Pattern '^[^%]*\\[a-zA-Z]+[\u4e00-\u9fff]'

# Active English review queue
Get-ChildItem .\paper_cn -Recurse -Filter *.tex |
  Select-String -Pattern '[A-Za-z]{8,}' |
  Where-Object {
    $_.Line -notmatch '^\s*%' -and
    $_.Line -notmatch '\\(cite|citet|citep|ref|eqref|label|url|href|documentclass|usepackage|input|includegraphics|bibliography|bibliographystyle|newcommand|def)\b'
  } |
  Select-Object Path, LineNumber, Line
```

If audits produce many hits from executable examples, JSON, tool schemas, citations, or identifiers, classify them once and move on. Do not spend time translating protected strings that would not improve the requested paper translation.

## CJK/XeLaTeX Fast Rules

Only add Chinese support after translation or when compilation needs it. Read `references/chinese_support.md` for full details.

High-probability fixes:

- Comment out pdfTeX-only primitives under XeLaTeX, such as `\pdfobjcompresslevel` or `\pdfcompresslevel`.
- Add `\PassOptionsToPackage{tracking=false}{microtype}` before `\documentclass` if `microtype` tracking fails.
- Comment out `\RequirePackage[T1]{fontenc}` in copied `.sty/.cls` files under XeLaTeX.
- Prefer `ctex`/`xeCJK` with verified local fonts on Windows.
- If a template loads `newtxtext` and Chinese font lookup or rendering breaks, disable `newtxtext` in the copied template or bind CJK fonts after all template font packages.
- Do not trust a PDF that exists but renders missing Chinese. Confirm with `pdffonts` and a page render.

For Windows local TeX Live, a robust pattern is:

```latex
\usepackage[fontset=none,scheme=plain]{ctex}
% load the copied template package/class here if possible
\xeCJKsetup{CJKspace=true, CJKmath=true}
\setCJKmainfont[
  Path=C:/Windows/Fonts/,
  UprightFont=simsun.ttc,
  BoldFont=simhei.ttf,
  ItalicFont=simkai.ttf
]{SimSun}
\setCJKsansfont[
  Path=C:/Windows/Fonts/,
  UprightFont=simsun.ttc,
  BoldFont=simhei.ttf
]{SimSun}
\setCJKmonofont[
  Path=C:/Windows/Fonts/,
  UprightFont=simsun.ttc
]{SimSun}
```

When using a fallback wrapper because the original conference template is too fragile, keep the original column count in the wrapper. For example, use `\documentclass[10pt,twocolumn,letterpaper]{article}` for a two-column source and a single-column `article` only for a single-column source. Read `references/layout_preservation.md` before changing templates.

Localize template-generated labels (`Figure`, `Table`, `References`, metadata labels) only when requested, visibly necessary for polish, or required by compilation/rendering. Source translation can be complete while some template strings remain intentionally unchanged.

## Compile and Render Verification

```powershell
latexmk -xelatex -interaction=nonstopmode -halt-on-error <main>.tex

Select-String -Path .\<main>.log -Pattern `
  '! LaTeX Error', `
  'Undefined control sequence', `
  'Citation .* undefined', `
  'Reference .* undefined', `
  'There were undefined citations', `
  'There were undefined references', `
  'Missing character', `
  'fontspec Error'

pdffonts .\<main>.pdf
pdftoppm -png -f 1 -l 1 -singlefile .\<main>.pdf .\verify_page1
pdftoppm -png -f 2 -l 2 -singlefile .\<main>.pdf .\verify_page2
pdftotext .\<main>.pdf .\<main>.txt
```

Rendered verification is required. If Poppler text extraction or rendering warns about font mappings but the page render is visually correct and `pdffonts` shows embedded Chinese fonts, report the warning as a tool limitation rather than a LaTeX failure.

## Completion Criteria

Do not claim completion until all are true:

- `paper_cn/` contains translated LaTeX source.
- Active body prose, headings, captions, tables, and appendix narrative are translated or explicitly classified as protected English.
- Source audits have been reviewed and real misses fixed.
- XeLaTeX compilation completed after final source edits.
- Bibliography and references are resolved or known original-source warnings are reported.
- Final PDF preserves the original paper's layout contract, especially single-column vs two-column body layout.
- The final PDF exists and rendered inspection confirms visible Chinese.

## Optional Technical Report

Only when requested, create `arXiv_<ARXIV_ID>/technical_report.md` using `references/summary_prompt.md` and `assets/report_template.md`.

## Field Notes from 2605.05185v1

This paper exposed speed and reliability pitfalls worth reusing:

- `curl.exe` can reset on arXiv e-print downloads; `Invoke-WebRequest` worked as a fallback.
- Fandol/font-name configurations can compile while rendered Chinese is missing or blank. Always verify fonts and rendered pages.
- A minimal CJK test can pass while the full template fails because template font packages change fontspec state.
- Disabling `newtxtext` in the copied template and using direct Windows font files produced a stable Chinese PDF.
- `pdftotext` is useful but not sufficient; `pdftoppm` page render caught the missing-Chinese failure.
- Large English audit output was mostly protected identifiers, citations, and executable prompt/schema content. Classify protected categories early to avoid wasting translation time.

## Field Notes from 2604.17898v1

- AAAI-style sources are two-column; a simplified single-column wrapper can compile but fails user expectations. If replacing a fragile template, copy the column count (`twocolumn`) and adapt tables/figures with `figure*`/`table*` or `\resizebox{\linewidth}{!}{...}` as needed.
- Verify rendered layout, not just PDF existence. Page 1 should show title/abstract and body in the expected column style.
- `\mathbf{\Theta}` under XeLaTeX/Latin Modern may trigger missing `U+0002` warnings. Prefer plain `\Theta` or a proper bold-math package if bold Greek is required.
