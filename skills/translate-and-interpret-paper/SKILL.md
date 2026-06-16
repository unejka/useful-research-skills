---
name: translate-and-interpret-paper
description: Translate and interpret academic papers, especially arXiv AI/ML papers, by combining the existing arxiv-paper-translator and arxiv-paper-reader workflows. Use when the user asks to "翻译并解读", translate and explain, translate and analyze, produce a Chinese paper PDF plus Chinese methodology reading notes, or create both a Chinese LaTeX/PDF translation and a rigorous Chinese method-analysis report from an arXiv ID, arXiv URL, local PDF, local LaTeX source, or pasted paper text.
---

# 翻译并解读

## Overview

Execute a full Chinese paper workflow: translate the paper into a verified Chinese LaTeX/PDF artifact, then write a Chinese methodology-focused interpretation report grounded in the original paper evidence.

This skill is an orchestrator. Reuse the existing component skills instead of duplicating their procedures:

- `arxiv-paper-translator` for arXiv source download, LaTeX-preserving translation, XeLaTeX/CJK fixes, compilation, and rendered PDF verification.
- `arxiv-paper-reader` for evidence gathering, method analysis, experiment/ablation synthesis, reproduction guidance, and the final Chinese Markdown report.

## Workflow

1. Resolve the paper input.
   - Accept arXiv IDs, arXiv abs/pdf/e-print URLs, local PDFs, local LaTeX source folders, or pasted paper text.
   - Normalize arXiv inputs to a stable `ARXIV_ID`.
   - Use one shared workspace for both phases, preferably `arXiv_<ARXIV_ID>/` for arXiv inputs.

2. Load the component instructions.
   - Read and follow `../arxiv-paper-translator/SKILL.md` for the translation phase.
   - Read and follow `../arxiv-paper-reader/SKILL.md` for the interpretation phase.
   - Load each component skill's referenced files only when its own progressive-disclosure rules require them.

3. Translate first.
   - Produce `paper_cn/` with translated LaTeX source.
   - Compile the translated PDF with XeLaTeX/latexmk when source compilation is available.
   - Verify rendered Chinese output, not just the existence of a PDF.
   - Preserve the original layout contract, especially one-column vs two-column body layout.

4. Build the interpretation evidence set.
   - Prefer original paper source/text for factual claims, formulas, experiments, and numbers.
   - Use translated artifacts to improve readability, but do not treat translation output as the only source of truth.
   - Reuse files already downloaded during translation instead of downloading the same paper again.
   - If translation succeeded from source, inspect `paper_source/`, `paper_cn/`, metadata, bibliography, tables, and appendix files.
   - If only a PDF or pasted text is available, extract text and explicitly note missing source-level evidence.

5. Write the Chinese interpretation report.
   - Use the `arxiv-paper-reader` report structure and section requirements.
   - Focus on methodology, pipeline, objective, algorithms, experiments, ablations, limitations, and reproduction guidance.
   - Include the abstract translation, method comparison table, representative metrics, and a concise memory pipeline.
   - Flag mismatches among abstract, introduction, tables, appendix, source, or repository evidence.

6. Produce a combined final handoff.
   - Report the translated PDF path if compiled.
   - Report the translated LaTeX source directory.
   - Report the method-analysis Markdown path.
   - Summarize verification: translation compilation/render checks, reader report section checks, and any unresolved warnings.

## Deliverables

Default deliverables for arXiv inputs:

- `arXiv_<ARXIV_ID>/paper_cn/`: translated Chinese LaTeX source tree.
- `arXiv_<ARXIV_ID>/paper_cn/<main>.pdf`: compiled Chinese PDF when source compilation is possible.
- `arXiv_<ARXIV_ID>/<ARXIV_ID>-read.md`: Chinese methodology interpretation report.

If a user supplies an output directory, place all deliverables under that directory while preserving the same internal structure.

## Quality Rules

- Do not skip translation verification before claiming the PDF is complete.
- Do not skip reader report verification before claiming the interpretation is complete.
- Do not invent open-source status, hyperparameters, datasets, metrics, limitations, or implementation details.
- Distinguish original-paper evidence from translation artifacts when the two diverge.
- If one phase is blocked, complete and verify the other phase, then report the blocker with the exact failed command, missing dependency, or unavailable evidence.
