# Compile Debugging Guide

Read this file when:
- translated LaTeX compiles with errors or warnings
- citations or refs show `?` / `??`
- `latexmk` exits non-zero
- Windows PDF locking or bibliography backend issues appear

## Quick Start

On Windows PowerShell, use the helper script:

```powershell
& "$PSScriptRoot\..\scripts\compile_ps1.ps1" -WorkDir . -MainTex main.tex
```

Or use `latexmk` directly:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

## Critical Pre-Compilation Setup (NEW)

Based on DeepSeekMath-V2 translation experience, **ALWAYS** perform these checks BEFORE first compilation:

### 1. Pre-Flight Compatibility Check

Run this PowerShell checklist:

```powershell
# Check 1: microtype tracking (CRITICAL - must be done BEFORE documentclass)
Select-String -Path main.tex -Pattern "PassOptionsToPackage.*tracking.*microtype"
if (-not $?) { 
    Write-Host "WARNING: Add '\PassOptionsToPackage{tracking=false}{microtype}' BEFORE \documentclass" -ForegroundColor Red
}

# Check 2: wrapfig presence (CRITICAL - incompatible with xeCJK)
$wrapfig = Select-String -Path main.tex -Pattern "usepackage.*wrapfig"
if ($wrapfig) {
    Write-Host "WARNING: wrapfig detected - must remove and convert wrapfigure/wraptable to standard environments" -ForegroundColor Red
}

# Check 3: xeCJK setup
$xeCJK = Select-String -Path main.tex -Pattern "usepackage.*xeCJK"
if (-not $xeCJK) {
    Write-Host "WARNING: xeCJK not found - required for Chinese" -ForegroundColor Red
}
```

### 2. Essential Preamble Configuration

Ensure these appear in the exact order shown:

```latex
% Step 1: Disable microtype tracking (MUST be before documentclass)
\PassOptionsToPackage{tracking=false}{microtype}

% Step 2: Document class
\documentclass[...]{...}

% Step 3: Remove incompatible packages
% - \usepackage[T1]{fontenc}  <-- REMOVE (conflicts with XeLaTeX)
% - \usepackage[utf8]{inputenc}  <-- REMOVE (not needed)
% - \usepackage{wrapfig}  <-- REMOVE (incompatible with xeCJK)

% Step 4: Add xeCJK with Windows fonts (or Fandol for Docker)
\usepackage{xeCJK}
\xeCJKsetup{CJKspace=true, CJKmath=true}
\setCJKmainfont{SimSun}[BoldFont=SimHei, ItalicFont=KaiTi]
\setCJKsansfont{Microsoft YaHei}
\setCJKmonofont{FangSong}

% Step 5: Page layout fix
\raggedbottom

% Step 6: Localize float labels
\renewcommand{\figurename}{图}
\renewcommand{\tablename}{表}
\renewcommand{\abstractname}{摘要}
```

## Known Critical Issues (from DeepSeekMath-V2 Experience)

### Issue 1: microtype Tracking Error

**Symptom:**
```
Package microtype Error: The tracking feature only works with pdftex
```

**Solution:** Add BEFORE `\documentclass`:
```latex
\PassOptionsToPackage{tracking=false}{microtype}
```

**Note:** If the class file forces microtype with tracking, you may need to edit the `.cls` file directly and comment out the `\RequirePackage[tracking]{microtype}` line.

### Issue 2: wrapfig Package Incompatibility

**Symptom:**
```
Environment wraptable undefined
```
or tables/figures overlapping with text

**Solution:**
1. Remove `\usepackage{wrapfig}`
2. Convert all `wrapfigure` to `figure`:
```latex
% BEFORE (remove this)
\begin{wrapfigure}{r}{6.5cm}
\centering
\includegraphics[scale=0.4]{figure.pdf}
\caption{...}
\end{wrapfigure}

% AFTER (use this)
\begin{figure}[t!]  % or [htbp]
\centering
\includegraphics[scale=0.4]{figure.pdf}
\caption{...}
\end{figure}
```

### Issue 3: xeCJK Catcode Issues with Custom Macros

**Symptom:**
```
Undefined control sequence
\xmax概率  % or similar custom macro followed by CJK
```

**Solution:** Add `{}` after every custom macro before CJK text:
```latex
% WRONG
\xmax概率
\Ours方法

% CORRECT
\xmax{}概率
\Ours{}方法
```

**Note:** This is especially critical in figure/table captions where xeCJK changes catcode handling.

### Issue 4: Cleveref Localization Order

**Symptom:**
```
figure 图图figure 图图
table 表表table 表表
```

**Cause:** Adding `\crefname` BEFORE `\usepackage{cleveref}`

**Solution:** Add `\crefname` AFTER `\usepackage{cleveref}`:
```latex
\usepackage{cleveref}  % First load cleveref
% ... other packages ...
\crefname{figure}{图}{图}  % Then add Chinese localization
\crefname{table}{表}{表}
```

**For delayed cleveref loading** (e.g., in `\AtEndPreamble`), use:
```latex
\AtEndPreamble{
  \crefname{figure}{图}{图}
  \crefname{table}{表}{表}
}
```

### Issue 5: Font Warnings (Non-Fatal)

**Symptom:**
```
Font shape `TU/FangSong(0)/b/it' undefined
```

**Cause:** FangSong doesn't have bold italic variant.

**Solution:** These warnings are cosmetic and can be ignored. To suppress:
```latex
\setCJKmonofont{FangSong}
% Then avoid using \ttfamily\bfseries\itshape together
```

## Compile Diagnostics Order

```
IMPORTANT: Follow this exact order when debugging compilation issues.
Skipping steps or doing them out of order will waste time.
```

### Phase 1: Pre-Flight (Before Any Compilation)

**Checklist:**
- [ ] `\PassOptionsToPackage{tracking=false}{microtype}` before `\documentclass`
- [ ] `\usepackage{xeCJK}` present
- [ ] `\usepackage{wrapfig}` removed
- [ ] All `wrapfigure`/`wraptable` converted to standard environments
- [ ] Font configuration appropriate for platform (Windows: SimSun/SimHei/FangSong, Docker: Fandol)

### Phase 2: First Pass Structure Check

Run:
```bash
xelatex -interaction=nonstopmode -halt-on-error main.tex 2>&1 | head -100
```

**Stop and fix immediately if you see:**
- `! LaTeX Error:` (any fatal error)
- `File ended while scanning`
- `Undefined control sequence` (unless it's a known missing package)

### Phase 3: Bibliography Backend

Detect backend:
```bash
grep -l "usepackage.*biblatex" *.tex && echo "BIBER" || echo "BIBTEX"
```

Run appropriate sequence:

**For BibTeX:**
```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

**For Biber:**
```bash
xelatex main.tex
biber main
xelatex main.tex
xelatex main.tex
```

### Phase 4: Verify References

Check for unresolved references:
```bash
grep -E "\?\?|\(\?\)" main.log || echo "All references resolved"
```

If `??` found, check `.bbl` was read and search log for later fatal errors.

## Common Error Patterns and Solutions

| Error Pattern | Root Cause | Solution |
|--------------|-----------|----------|
| `microtype Error: tracking only works with pdftex` | microtype's tracking feature is incompatible with XeLaTeX | Add `\PassOptionsToPackage{tracking=false}{microtype}` BEFORE `\documentclass` |
| `Environment wraptable undefined` | wrapfig package removed but document still uses wraptable | Convert all wrapfigure/wraptable to standard figure/table environments |
| `Undefined control sequence \xmax概率` | Custom macro directly followed by CJK text due to xeCJK catcode changes | Add `{}` after macro: `\xmax{}概率` |
| `figure 图图figure 图图` | cleveref localization added before `\usepackage{cleveref}` | Move `\crefname` AFTER `\usepackage{cleveref}` |
| `Citation ... undefined` (every citation) | Bibliography backend not run or failed | Run bibtex/biber and recompile twice |
| `.bbl read but citations show ?` | Later LaTeX fatal error prevented final pass completion | Search log for first fatal error after `.bbl read` |

## References

- [Chinese Support Configuration](chinese_support.md) - CJK setup, font selection, and label localization
- [Translation Guidelines](translation_guidelines.md) - LaTeX-specific translation rules
