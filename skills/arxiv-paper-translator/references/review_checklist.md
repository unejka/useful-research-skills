# Translation Review Checklist

## Windows Note

If you are on Windows PowerShell, treat the bash snippets below as conceptual. Prefer `rg`, `Select-String`, `Compare-Object`, and `Group-Object`. When a grep-style check returns many hits, inspect whether they come from commented lines before treating them as active translation defects.

## 1. File Completeness

Before checking anything else, verify that each translated `.tex` file or chunk actually changed on disk in the expected direction. Do not accept "completed" translation work based only on an agent summary.

- [ ] For every translated file/chunk, the file on disk contains Chinese reader-facing prose where expected
- [ ] No translated file/chunk is merely a summary, wrapper message, or effectively unchanged English source
- [ ] For chunked workflows, each chunk passes read-back inspection before merge

## 1a. Layout Fidelity Gate

Before translation or template repair, record the source layout contract. The final PDF must preserve it unless the user explicitly asks for a different layout.

- [ ] Original main file and `\documentclass` / class template identified
- [ ] Original body layout identified as single-column or two-column
- [ ] Original wide floats (`figure*`, `table*`) and explicit column switches (`\twocolumn`, `\onecolumn`) recorded
- [ ] If the original PDF is available, a rendered page confirms the inferred column count
- [ ] If a fallback wrapper replaced the original template, it preserves the original column count
- [ ] Rendered Chinese PDF body pages match the original column count: two-column source -> two-column PDF; single-column source -> single-column PDF
- [ ] Wide figures/tables are not clipped after translation

PowerShell:

```powershell
Get-ChildItem paper_source -Recurse -Include *.tex,*.sty,*.cls |
  Select-String -Pattern '\\documentclass|twocolumn|onecolumn|\\twocolumn|\\onecolumn|\\begin\{figure\*\}|\\begin\{table\*\}' |
  Select-Object Path, LineNumber, Line
```

- Verify all .tex files are translated or copied (skip files that are not translated)
```bash
diff <(cd paper_source && find . -name "*.tex" -type f | sort) \
     <(cd paper_cn && find . -name "*.tex" -type f | sort)
```
- Verify all non-text files copied correctly
```bash
diff <(cd paper_source && find . -type f -not -name "*.tex" | sort) \
     <(cd paper_cn && find . -type f -not -name "*.tex" | sort)
```

## 2. LaTeX Command Spelling

Detect misspelled commands introduced during translation (e.g. `\footnotetext` → `\footnotext`):

```bash
diff <(cd paper_source && grep -ohrIE '\\[a-zA-Z]+' | sort -u) \
     <(cd paper_cn && grep -ohrIE '\\[a-zA-Z]+' | sort -u) \
     | grep '^>'
```

Right-side-only commands are suspicious. Verify each one — if not intentionally added (e.g. `\figurename`, `\setCJKmainfont`), it's likely a typo.

**Also check for environment name typos** - `\end{ xxx}` with a space is a common error:

```bash
grep -rnE '\\end\{[ ]+[^}]+\}' paper_cn/ --include='*.tex'
```

This catches errors like `\end{ abstract}` (should be `\end{abstract}`). Also check `\begin`:
```bash
grep -rnE '\\begin\{[ ]+[^}]+\}' paper_cn/ --include='*.tex'
```

## 2a. Duplicate Labels

Duplicate `\label{...}` keys cause unstable references and should be fixed even if the PDF compiles. This is **especially common** when the paper includes supplementary material that repeats equations from the main paper.

PowerShell:

```powershell
$labels = Get-ChildItem paper_cn -Recurse -Filter *.tex |
  Select-String -Pattern '\\label\{([^}]+)\}' -AllMatches |
  ForEach-Object { $_.Matches } |
  ForEach-Object { $_.Groups[1].Value }
$labels | Group-Object | Where-Object Count -gt 1
```

Any returned label name needs manual deduplication. Rename the duplicate (e.g., `eq:approx` → `eq:approx-supp`) and update the corresponding `\ref` in that file.

## 3. CJK Catcode Issue & Special Characters

### CJK Catcode Issue: Custom macros followed by Chinese
Find custom macros directly followed by CJK characters (missing `{}`):

```bash
rg -n '^[^%]*\\[a-zA-Z]+[一-龥]' paper_cn -g '*.tex'
```

Each match needs `{}` inserted between macro and CJK text. Background: `xeCJK` sets CJK characters to catcode 11 (letter), so `\xmax概率` is parsed as one undefined command `\xmax概率` instead of `\xmax` + `概率`.

### Unescaped underscores in text mode
Find underscores in text mode that need escaping:

```bash
rg -n '^[^%]*[A-Za-z0-9]_' paper_cn -g '*.tex' | grep -v '\$' | grep -v '\\_'
```

**Background**: In text mode, `_` enters subscript math mode. `SODA_c` will cause `Missing $ inserted` because LaTeX expects math mode for subscript. **Every underscore in ordinary text must be escaped as `\_`**.

Only report matches that are **not inside math mode `$...$`** and **not already escaped** with `\`. Each match needs `_` → `\_`.

## 4. Unescaped & Characters

Find unescaped `&` characters in non-table contexts:

```bash
rg -n '^[^%]*&' paper_cn -g '*.tex'
```

Any `&` not in a table/alignment context must be escaped as `\&`. Ignore hits that are clearly inside commented lines or active tabular rows.

This matters even when the prose translation is otherwise correct. Terms like `文本&图表` are common natural-language translations but are invalid in ordinary LaTeX text mode unless written as `文本\&图表`.

## 4a. Incorrect Table Line Endings

Find lines ending with single backslash instead of double backslash in tables:

```bash
grep -rnE '^.*\\[[:space:]]*$' paper_cn/ --include='*.tex' | grep -B1 -A1 'tabular'
```

If any matches are found, they likely need to be changed from `\` to `\\` to avoid `Misplaced \noalign` compilation errors.

## 4b. Unescaped % Characters

Find unescaped `%` characters in non-comment contexts:

```bash
rg -n '^[^%].*[^\\]%' paper_cn -g '*.tex'
```

*Note: On Windows PowerShell, use this command instead:*
```powershell
Get-ChildItem paper_cn -Recurse -Filter *.tex | Select-String '^[^%].*[^\\]%' | Select-Object Filename,LineNumber,Line
```

Any `%` that is not a comment and not in a tabular column spec must be escaped as `\%`.
**Unescaped % causes file truncation**: everything from `%` to end of line becomes a comment, leading to "File ended while scanning" errors.

## 4c. Unbalanced Braces/Parentheses in Math Mode

Common issue: translation can accidentally add extra closing parentheses when inserting Chinese text into math expressions, causing "Extra }, or forgotten $" errors.

Manual check recommendations:
- After translation, verify inline math expressions like `$p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t)$` have balanced parentheses
- Each opening `(` should have exactly one closing `)`
- Each opening `{` should have exactly one closing `}`
- Common mistake: adding an extra `)` after Chinese text insertion

## 5. Terminology Consistency Check

For each .tex file, verify:

- [ ] Key terms translated consistently across all files
- [ ] First mention of key terms includes both English and Chinese
- [ ] Technical terms follow established terminology table
- [ ] Proper nouns (Agent Swarm, PARL, MoonViT-3D) handled correctly
- [ ] Acronyms first appear with full name + acronym (e.g., "强化学习 (Reinforcement Learning, RL)")
- [ ] After chunk merge, the same concept is not translated inconsistently across sections (for example, one chunk using one Chinese term and another chunk using a different one for the same English concept)

## 6. Translation Quality Check

For each .tex file, verify:

- [ ] Chinese expression is natural and fluent (avoiding direct translation artifacts)
- [ ] Academic language style is maintained throughout
- [ ] Sentence structures follow Chinese expression patterns
- [ ] Key verbs translated appropriately
- [ ] No colloquial expressions or overly casual language
- [ ] Technical descriptions are precise and professional

## 7. Content Spot-Check

For each .tex file, compare with source to verify:

- [ ] Paper title (`\title{...}` / `\icmltitle{...}`) translated
- [ ] `\thanks{...}`, `\footnote{...}`, `\footnotetext{...}` content translated
- [ ] All section/subsection titles translated
- [ ] Figure and table captions translated
- [ ] LaTeX commands and math formulas unchanged
- [ ] File paths (`\input`, `\includegraphics`) unchanged
- [ ] Labels and references (`\label`, `\ref`, `\cite`) unchanged

Also distinguish active source text from figure-baked text:

- [ ] Any remaining English in active `.tex` prose is intentional/protected, not a missed translation
- [ ] English embedded inside external figures / screenshots is treated as a separate figure-localization decision, not automatically as a source-translation defect

## 8. Optional Template Hard-coded Labels Audit

Run this section when the user wants a polished localized PDF, or when rendered output shows template-generated English labels that actually matter. For source-first delivery, English template labels do not block completion by default.

Check `.sty/.cls/.tex` files in `paper_cn/` for visible English strings that may need localization:

```bash
grep -rnE '(Equal contribution|Equal Contribution|Correspondence|Correspondence to|Corresponding Author|Keywords|Index Terms|ACM Reference Format|Under review|Preprint|Proceedings of|Abstract|Supplementary Material|References|Bibliography|Figure|Table|Appendix)' paper_cn/ --include='*.sty' --include='*.cls' --include='*.tex'
```

- [ ] Conference/journal template labels translated or overridden when the requested output calls for full localization (e.g. `Equal contribution` → `同等贡献`)
- [ ] Template-specific labels like `Abstract` / `Figure` / `Table` / `References` / `Supplementary Material` in copied `.sty/.cls` files localized only when they are user-visible and relevant to the requested output
- [ ] Author affiliation/institution names handled (keep original or add Chinese translation)

Do not mix this audit with figure-localization work. English baked into plot images or screenshots will not be found reliably in `.tex/.sty/.cls` audits and should only be treated as blocking if the user explicitly asked for fully localized figures.

## 8a. Optional Date / Title-Page Metadata Audit

Run this section only for polished rendered output. If the user accepts English title-page metadata or only wants translated source, this audit is optional.

- [ ] Check `\date{...}` and `\today` in the translated source — do not leave English month/day formats on an otherwise Chinese title page
- [ ] Check copied `.cls/.sty` files for visible metadata labels such as `Date`, `Correspondence`, `Project Page`, `Keywords`, `Index Terms`, and `ACM Reference Format`
- [ ] If the template uses a titlebox/metadata wrapper, verify those labels are localized in the rendered PDF, not only in source comments

PowerShell helper:

```powershell
Get-ChildItem paper_cn -Recurse -Include *.tex,*.sty,*.cls |
  Select-String -Pattern '\\date\{|\\today|Date|Correspondence|Project Page|Keywords|Index Terms|ACM Reference Format' |
  Select-Object Path, LineNumber, Line
```

## 8b. Draft / TODO Artifact Audit

Check for draft-mode or author-note artifacts that may still render in English or signal an unfinished translation:

```bash
rg -n '^[^%]*\\(todo|TODO|note|NOTE|fixme|FIXME)\b|draft|Draft' paper_cn -g '*.tex' -g '*.sty' -g '*.cls'
```

- [ ] No visible draft markers, TODO notes, or unfinished author annotations remain in active content unless explicitly intended

## 9. Compilation Pre-check

Run this section when you are actually compiling or preparing a compile-ready draft. Do not block source-first delivery on compile-only checks.

- [ ] `\PassOptionsToPackage{tracking=false}{microtype}` added before `\documentclass` for XeLaTeX compatibility (microtype tracking not supported by XeLaTeX)
- [ ] Search copied `.cls/.sty` files for `microtype`, `tracking=`, and `\DisableLigatures` before compile churn starts
- [ ] Check `.cls` files for `\DisableLigatures` lines → comment them out for XeLaTeX compatibility (only works with pdftex)
- [ ] `\usepackage[T1]{fontenc}` commented out or removed (T1 encoding conflicts with XeLaTeX Unicode)
- [ ] `\bibliographystyle` and `\bibliography` commands both exist and in correct order
- [ ] If using cleveref Chinese localization, verify it appears **after** `\usepackage{cleveref}`
- [ ] If `cleveref` is loaded from `.sty/.cls` via `\AtEndPreamble` or another delayed hook, place Chinese `\crefname` / `\Crefname` localizations in a matching delayed hook instead of raw preamble lines
- [ ] All `\input{file.tex}` references point to existing files; comment out any missing files with `%`
- [ ] Citation key case matches between `.tex` and `.bib` (e.g., `\cite{GAIA}` matches `@inproceedings{GAIA,`)
- [ ] Check `.bib` file for `@software` entries → traditional BibTeX doesn't support `@software`, convert to `@misc`
- [ ] If `paper_source/` already contains a precompiled `.bbl`, keep it available in `paper_cn/` as a fallback for compile-path troubleshooting when BibTeX/Biber generation fails
- [ ] `axessibility` package with `[accsupp]` option disabled/commented out (incompatible with XeLaTeX due to pdfTeX-specific `\pdfcompresslevel` command)
- [ ] Check custom `.cls` templates for hard-coded English labels (Appendix, Abstract) and localize them only when polished rendered localization is in scope
- [ ] Run a special-character pass on active prose for unescaped `&`, unescaped `%`, text-mode underscores, and malformed `\begin` / `\end` names before compiling

Recommended search when cleveref behavior is unclear:

```bash
rg -n 'AtEndPreamble|usepackage.*cleveref|crefname|Crefname' paper_cn -g '*.tex' -g '*.sty' -g '*.cls'
```

## 10. Optional Rendered PDF Audit

Run this section only when a PDF deliverable is in scope and you can inspect the render. Source-first completion does not require it.

- [ ] Confirm the generated PDF exists and was regenerated after the latest fixes
- [ ] Confirm rendered body layout matches the original column count and broad template style
- [ ] Visually inspect the PDF for visible English labels or headings that source-only audits can miss, especially `Abstract`, `Figure`, `Table`, `References`, `Bibliography`, `Appendix`, `Under review`, and `Preprint`, but only treat them as defects when the requested output calls for localization
- [ ] Visually inspect the title page for English date strings and metadata labels such as `Date`, `Correspondence`, or `Equal contribution` when title-page localization is part of the requested output
- [ ] Verify abstract and at least two body sections visibly render in Chinese
- [ ] Verify figure/table labels and bibliography heading are localized in rendered output when full template localization is in scope

If `pdftotext` is available, extract text from the final PDF and use it as a rendered-output audit queue:

```bash
pdftotext paper_cn/main.pdf - | rg 'Abstract|Figure|Table|References|Bibliography|Appendix|Under review|Preprint'
```

Treat matches as review targets, not blind replacement commands. Some English may still be protected technical content, and visible UI/template labels only need localization when that level of polish is actually part of the requested deliverable.
