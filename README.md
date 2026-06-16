# Useful Research Skills

Reusable Codex skills for research paper workflows.

This repository currently contains three local skills:

- `arxiv-paper-reader`: fetches and analyzes AI/ML arXiv papers, then produces a rigorous Chinese Markdown reading report focused on methodology.
- `arxiv-paper-translator`: translates arXiv papers into Chinese while preserving LaTeX structure and compiling a layout-checked Chinese PDF.
- `translate-and-interpret-paper`: combines the translator and reader workflows to produce both a Chinese paper translation and a Chinese methodology interpretation report.

## Repository Layout

```text
skills/
  arxiv-paper-reader/
    SKILL.md
    agents/
    references/
    scripts/
  arxiv-paper-translator/
    SKILL.md
    assets/
    references/
    scripts/
  translate-and-interpret-paper/
    SKILL.md
    agents/
```

## Install

Clone this repository:

```powershell
git clone https://github.com/unejka/useful-research-skills.git
cd useful-research-skills
```

Install all skills into Codex on Windows:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

Install all skills on macOS or Linux:

```bash
mkdir -p ~/.codex/skills
cp -R skills/* ~/.codex/skills/
```

Restart Codex after installing so the new skills are loaded.

## Usage

Analyze an arXiv paper and write a Chinese methodology report:

```text
Use $arxiv-paper-reader to analyze https://arxiv.org/abs/2503.09516
```

Translate an arXiv paper into Chinese LaTeX and compile a verified PDF:

```text
Use $arxiv-paper-translator to translate https://arxiv.org/abs/2605.05185v1
```

Translate and interpret a paper in one workflow:

```text
Use $translate-and-interpret-paper to 翻译并解读 https://arxiv.org/abs/2503.09516
```

## Requirements

Common requirements:

- Codex with local skills enabled.
- Internet access for arXiv downloads.
- Python 3 for helper scripts.

`arxiv-paper-reader` can use:

- `pdftotext` for PDF text extraction when available.
- `pypdf` or `PyPDF2` as Python fallbacks.

`arxiv-paper-translator` can use:

- TeX Live or another LaTeX distribution with `xelatex` and `latexmk`.
- Poppler tools such as `pdftotext`, `pdftoppm`, and `pdffonts` for PDF verification.
- Windows PowerShell for the included `compile_ps1.ps1` helper.

`translate-and-interpret-paper` expects the two component skills to be installed alongside it because it reuses their workflows and resources.

## Notes

- Generated paper workspaces, PDFs, LaTeX build artifacts, and local Codex/OMX state are intentionally ignored by Git.
- The skills are stored under `skills/` so they can be copied directly into a Codex skills directory.
- No license has been declared yet.
