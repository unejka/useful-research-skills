# Chinese Support Configuration

Use this file when you need to compile Chinese output under XeLaTeX, fix CJK/rendering compatibility, or intentionally localize template-generated labels. It is not a requirement to fully localize every copied `.sty/.cls` label for a source-first translation handoff.

Add the following to the main .tex file preamble (before `\begin{document}`).

## Pre-Compatibility Configuration

Before `\documentclass`, add microtype disabling for XeLaTeX compatibility:
```latex
% Disable microtype tracking for XeLaTeX compatibility
\PassOptionsToPackage{tracking=false}{microtype}
```

## Remove Incompatible Packages

Remove the old CJK package if it exists:
- Remove `\usepackage{CJKutf8}`
- Keep `\usepackage[utf8]{inputenc}` (or remove it, XeLaTeX doesn't need it)
- **Remove/comment out** `\usepackage[T1]{fontenc}` (T1 encoding conflicts with XeLaTeX Unicode)

## Add xeCJK Package

Using `xeCJK` package to support CJK characters. **IMPORTANT**: Before choosing fonts, check available fonts on the system:

**On Windows (local TeX Live)**, prefer installed system fonts over TeX Live fallback fonts. Probe common fonts first:

```powershell
Get-ChildItem C:\Windows\Fonts\simsun.ttc,C:\Windows\Fonts\simhei.ttf,C:\Windows\Fonts\simkai.ttf,C:\Windows\Fonts\msyh.ttc,C:\Windows\Fonts\simfang.ttf
```

If these files exist, use:

```latex
\usepackage{xeCJK}
\xeCJKsetup{CJKspace=true, CJKmath=true}
\setCJKmainfont{SimSun}[BoldFont=SimHei, ItalicFont=KaiTi]
\setCJKsansfont{Microsoft YaHei}
\setCJKmonofont{FangSong}
```

`STSong` is not guaranteed on every Windows host. Use it only if you verified it is installed. TeX Live Fandol fonts may compile locally, but Windows system fonts usually produce fewer `fontspec` warnings.

### Robust Windows Template Recipe

Use this when a complex `.sty`/`.cls` template loads font packages such as `newtxtext`, `helvet`, or `microtype`, or when a minimal CJK test works but the full paper cannot find/render Chinese fonts.

Before applying this recipe, preserve the source layout contract. If the original paper is two-column, keep `twocolumn` in any fallback wrapper; if it is single-column, keep it single-column. Do not silently change column count while fixing CJK support.

1. Load `ctex` with no preset fontset near the top of the main file.
2. Load the copied template package/class.
3. Bind CJK fonts after the template has loaded its font packages.
4. If `newtxtext` causes `fontspec` lookup failures or rendered Chinese disappears, comment it out in the copied template for the Chinese build.

```latex
\PassOptionsToPackage{tracking=false}{microtype}
\documentclass[10pt,twocolumn,letterpaper]{article} % use twocolumn only when the source is two-column

\usepackage[fontset=none,scheme=plain]{ctex}
\usepackage{scai} % or the copied template package

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

This pattern fixed `OpenSearch-VL` (`2605.05185v1`) after these failed or incomplete alternatives:
- font-name-only `SimSun`/`Microsoft YaHei` setup worked in a minimal file but failed in the full template.
- explicit Fandol font paths compiled but the final PDF did not render Chinese in Poppler and did not list Fandol as embedded.
- disabling `newtxtext` in the copied template allowed `SimSun`/`SimHei`/`KaiTi` to embed and render correctly.

Always validate the final PDF with both `pdffonts` and a rendered page image. PDF existence and successful `.xdv` generation are not enough.

**On Docker/Linux**, use Fandol fonts (pre-installed in the recommended image):
```latex
\usepackage{xeCJK}
\xeCJKsetup{CJKspace=true, CJKmath=true}
\setCJKmainfont{FandolSong}[ItalicFont=FandolKai]
\setCJKsansfont{FandolHei}
\setCJKmonofont{FandolFang}
```

**Avoid these fonts** that have known issues:
- `Noto Serif SC` - causes "Invalid TTC index" errors on Windows
- `Noto Sans SC` - may cause similar issues
- Variable fonts (`.ttf` with weight variations) - use static fonts instead

**Font configuration tips**:
- `xeCJKsetup{CJKspace=true}` prevents unwanted line breaks between CJK and Latin characters
- `xeCJKsetup{CJKmath=true}` ensures math formulas work correctly with CJK
- Always set `\setCJKsansfont` and `\setCJKmonofont` even if only using one Chinese font — xeCJK switches fonts for different contexts and may fall back to the last set font

## Add Compatibility for Old Custom Commands

If the original document defines `\newcommand{\chinese}[1]{...}` for CJK text with old CJK package, add this compatibility definition after xeCJK config to avoid undefined command errors:
```latex
% Compatibility: keep \chinese command for existing uses
\newcommand{\chinese}[1]{#1}
```

**Option 1.** When using Docker to compile, ask user to select the font scheme:

**方案 A: Fandol（默认，学术正式风格）**
```latex
\usepackage{xeCJK}
\setCJKmainfont{FandolSong}[ItalicFont=FandolKai]  % 宋体 - 正文，\emph 用楷体
\setCJKsansfont{FandolHei}    % 黑体 - 标题、\textsf
\setCJKmonofont{FandolFang}   % 仿宋 - 代码、\texttt
```

**方案 B: 霞鹜文楷（开源，易读美观）**
```latex
\usepackage{xeCJK}
\setCJKmainfont{LXGW WenKai Lite}[ItalicFont=FandolKai]  % 霞鹜文楷 - 正文，\emph 用楷体
\setCJKsansfont{LXGW Marker Gothic}      % 霞鹜漫黑 - 标题、\textsf
\setCJKmonofont{FandolFang}              % 仿宋 - 代码、\texttt
```

以上字体均在推荐的 Docker 镜像（`xu-cheng/texlive-debian`）中预装。

**Option 2.** When compiling locally on Linux/macOS, query the local font list and ask user to select the font:

本地编译时可通过以下命令查看可用中文字体：

```bash
fc-list :lang=zh family
```

特别注意，中文字体没有斜体，一般用**楷体**代替。


e.g.: 

```latex
\usepackage{xeCJK}
\setCJKmainfont{Songti SC}[ItalicFont=Kaiti SC]
\setCJKsansfont{Heiti SC}
\setCJKmonofont{PingFang SC}
```

## Optional Localize Float Labels

If the user accepts English template labels such as `Abstract`, `Figure`, `Table`, bibliography headings, or page-header text, you may skip this section. Use it when polished rendered localization is requested or when the current template needs these overrides to look acceptable.

```latex
\renewcommand{\figurename}{图}
\renewcommand{\tablename}{表}
\renewcommand{\abstractname}{摘要}
\renewcommand{\refname}{参考文献}
\renewcommand{\bibname}{参考文献}
\renewcommand{\contentsname}{目录}
```

`\refname` and `\bibname` are both needed because different classes use different bibliography-heading commands. Check which one the template renders and keep both localized unless you verified only one is active.

## Optional Localize Date and Metadata Labels

If the translated paper uses Chinese throughout and the user wants a polished rendered PDF, inspect title-page metadata too — not just float labels. On many English templates, `\today` will still render an English date string even after body translation.

Recommended approach:

```latex
% Prefer an explicit localized date over raw \today when the template renders English dates
\date{2026年3月31日}
```

If the class defines metadata wrappers such as `\metadata[Date]{...}`, `\metadata[Correspondence]{...}`, `\metadata[Project Page]{...}`, or similar titlebox fields, localize the visible label text in the `.cls/.sty` file or override it from the main document if the template allows it and if that level of polish is requested.

Typical visible labels worth checking on the title page:
- `Date`
- `Correspondence`
- `Equal contribution` / `Equal Contribution`
- `Project Page`
- `Keywords`
- `Index Terms`
- `ACM Reference Format`

Do not assume float-label localization is enough when polished rendered localization is in scope. A translated PDF can still look unfinished if the first page shows `Date: March 31, 2026` above otherwise Chinese content.

If the paper uses the `algorithm` float, localize its float name separately:

```latex
\floatname{algorithm}{算法}
```

For `algpseudocode` / `algorithmicx` keywords, localization is optional. If you localize them, only redefine commands that actually exist in the installed package version. Do **not** assume commands such as `\algorithmicto` are universally available. When unsure, keep pseudocode keywords in English and localize only the float/caption name.

**Check custom `.cls`/`.sty` templates for hard-coded labels when needed**:
- Some custom class/files hard-code section headings in English. For example:
  - CVPR `cvpr.sty`: hard-codes `Abstract` and `Supplementary Material` → change to `摘要` and `补充材料`
  - NeurIPS `neurips_xxxx.sty`: hard-codes `Abstract` in the abstract environment definition → change `Abstract` to `摘要`
  - Other custom classes may hard-code `Figure`, `Table`, `References`, `Bibliography`, `Appendix`, `Under review`, `Preprint`, or author-note labels. Search copied `.cls/.sty` files broadly instead of checking only known conference templates, but only patch labels that matter for the requested output.
  - Appendix/Appendix labels:
```latex
\newcommand{\beginappendix}{\appendix{\huge\sffamily Appendix\par}}
```
Localize it to Chinese:
```latex
\newcommand{\beginappendix}{\appendix{\huge\sffamily 附录\par}}
```

## Optional Localize Preprint Notice String

If the user is fine with the English preprint/review banner, you can leave it alone. Use this override only when that banner is visibly distracting or the user asked for fuller localization.

When overriding the preprint notice string in `neurips_*.sty`, **must** wrap the redefinition in `\makeatletter`/`\makeatother`:

```latex
% Override preprint notice string to Chinese
\makeatletter
\renewcommand{\@noticestring}{%
预印本。正在审稿。%
}
\makeatother
```

**Why**: The `@` character in command names like `\@noticestring` is special in LaTeX and requires changing catcode before accessing it. Without `\makeatletter` you will get the error: `LaTeX Error: Missing \begin{document}.`

## Optional Localize cleveref Names

Use this section when rendered cross-reference labels should appear in Chinese. If the user only wants translated source or accepts English cross-reference labels, this section is optional.

**CRITICAL**: Cleveref Chinese localization MUST be added **AFTER** `\usepackage{cleveref}`. If added before `\usepackage{cleveref}`, the original English `Fig.~`/`Tab.~` definitions will still exist, resulting in duplicated text like `figure 图图figure 图图`.

If paper uses `cleveref` package:

```latex
% First load cleveref package (already loaded in original document)
% Then add Chinese localization AFTER loading:
\crefname{figure}{图}{图}
\Crefname{figure}{图}{图}
\crefname{table}{表}{表}
\Crefname{table}{表}{表}
\crefname{section}{章节}{章节}
\Crefname{section}{章节}{章节}
\crefname{algorithm}{算法}{算法}
\Crefname{algorithm}{算法}{算法}
\crefname{appendix}{附录}{附录}
\Crefname{appendix}{附录}{附录}
\crefname{equation}{式}{式}
\Crefname{equation}{式}{式}
```

### When `cleveref` is loaded indirectly or delayed by a style/class file

Some templates (for example CVPR-style `cvpr.sty`) load `cleveref` inside `\AtEndPreamble{...}` or another delayed hook. In that case, adding `\crefname` directly in `main.tex` can fail with:

```latex
! Undefined control sequence.
\crefname ...
```

Use a matching delayed hook for the Chinese localization:

```latex
\AtEndPreamble{
  \crefname{figure}{图}{图}
  \Crefname{figure}{图}{图}
  \crefname{table}{表}{表}
  \Crefname{table}{表}{表}
  \crefname{section}{章节}{章节}
  \Crefname{section}{章节}{章节}
  \crefname{algorithm}{算法}{算法}
  \Crefname{algorithm}{算法}{算法}
  \crefname{appendix}{附录}{附录}
  \Crefname{appendix}{附录}{附录}
  \crefname{equation}{式}{式}
  \Crefname{equation}{式}{式}
}
```

Before adding cleveref localization, inspect `.sty/.cls` files for `\AtEndPreamble`, `\usepackage{cleveref}`, `\crefname`, and `\Crefname`.

**Note**: Full `\Crefformat` and `\Crefmultiformat` redefinitions are omitted because they can cause compilation errors `Undefined control sequence \@nil` on some cleveref versions. Basic name localization is sufficient for most documents and more robust across different cleveref versions.

## Optional Localize Theorem-like Environments

Use this section when theorem headings must render in Chinese. It is not required for every fast draft or source-first translation handoff.

Find `\newtheorem` definitions (usually in preamble or .sty file) and replace display names:

```
Theorem → 定理
Proposition → 命题
Definition → 定义
Lemma → 引理
Corollary → 推论
Proof → 证明
```

## Remove Incompatible Packages

删除 `\usepackage[T1]{fontenc}`（如存在）。T1 是 pdfLaTeX 的 8-bit 字体编码，XeLaTeX 原生使用 Unicode，两者冲突会导致字体查找异常。

## Page Layout Fix

```latex
\raggedbottom
```

Prevents vertical stretching on pages with mixed CJK/math content.

## Custom Command for CJK Text

如果原文定义了自定义命令包裹 CJK 文本，修改为直接输出参数内容。避免与`xeCJK`冲突。

```latex
% custom command for CJK text
\chinese{一}
```

```latex
% before
\newcommand{\chinese}[1]{\begin{CJK*}{UTF8}{gbsn}{#1}\end{CJK*}}
% after
\newcommand{\chinese}[1]{#1}
```

## 引号改写

将原文中的引号 "" 替换为 `` 和 ''。或者直接用中文引号“”

e.g:

```latex
% before 原文，用英文引号""包裹
Traditional approaches typically follow a "train-then-compress" pipeline
% after 翻译，用``和''包裹
传统方法通常采用``先训练后压缩''的流程
% after 翻译 2，用中文引号“”包裹
传统方法通常采用“先训练后压缩”的流程
```
