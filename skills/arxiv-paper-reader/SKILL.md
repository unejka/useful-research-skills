---
name: arxiv-paper-reader
description: Analyze AI/ML arXiv papers from an arXiv ID, arXiv abs/pdf URL, local PDF, or provided paper text and produce a rigorous Chinese Markdown report focused on methodology. Use when the user asks for paper interpretation, method analysis, methodology breakdown, experiment/ablation summary, reproduction guidance, or a structured Chinese reading note for an academic paper.
---

# ArXiv Paper Reader

## Workflow

1. Resolve the paper input.
   - Accept arXiv IDs such as `2503.09516`, arXiv links such as `https://arxiv.org/abs/2503.09516`, local PDFs, local TeX/source folders, or pasted paper text.
   - If the user provides an arXiv ID/link, run `scripts/fetch_arxiv_paper.py <input> --out <work-dir>` to download metadata, PDF, source when available, and extracted text.
   - If the user provides a local PDF, use `pdftotext` or an available PDF extraction tool to create text before analysis.

2. Build the evidence set before writing.
   - Read `metadata.json` and the abstract first.
   - Search the extracted text/source for methodology, algorithm, objective, training, inference, experiments, ablations, implementation details, limitations, and appendix sections.
   - Prefer TeX/source files for formulas, tables, captions, and exact experimental numbers when source is available.
   - Cross-check headline claims against tables and appendix details. If the paper uses inconsistent improvement numbers, metric names, dataset settings, or baseline references, explicitly flag the discrepancy in the report.
   - Treat generated model outputs, case studies, and appendix examples as evidence only for the claims they directly support.

3. Produce a Markdown report.
   - Use `references/method-analysis-template.md` as the required output skeleton.
   - Write entirely in Chinese unless preserving paper symbols, dataset names, model names, metrics, URLs, or code identifiers.
   - Focus on Methodology. Discuss introduction/conclusion only when needed to explain motivation, assumptions, or limitations.
   - Translate the abstract in section 0 of the template.
   - In section 2 of the template, make the pipeline especially detailed: input, processing steps, model/tool modules, training/inference behavior, outputs, formulas, and algorithm roles.
   - Write mathematical notation in Markdown math syntax: use `$...$` for inline math and `$$...$$` for display equations. Do not put equations in plain code fences.
   - Keep non-math protocol tokens, CLI commands, XML-like tags, file names, and code identifiers in backticks. Do not wrap mathematical variables or equations in backticks.

4. Ground every claim in the paper content.
   - Do not invent open-source status, hyperparameters, datasets, metrics, or limitations.
   - If a requested item is not present in the paper content, explicitly state in Chinese that the paper does not specify it, then explain the closest available evidence.
   - When key numbers are available, include the most representative values rather than every table entry.

5. Save the artifact.
   - If the user gives an output path, write there.
   - Otherwise write a Markdown file near the working artifact, named `<arxiv-id>-read.md` for arXiv inputs or `<paper-name>-read.md` for local inputs.
   - For arXiv inputs, derive `<arxiv-id>` from `metadata.json` or `fetch_manifest.json`; remove URL decorations and replace filesystem-unsafe characters such as `/` with `_`.
   - Before final response, verify the Markdown includes sections 0 through 6 and the required comparison table.
   - Verify equations are rendered as Markdown math: inline formulas use `$...$`, display equations use `$$...$$`, and no mathematical equations remain in code fences.

## Output Requirements

The final Markdown must include:

- Section 0: faithful Chinese abstract translation.
- Section 1: method motivation, prior pain points, and core hypothesis/intuition.
- Section 2: detailed method design, modules, formulas/algorithms in plain language.
- Section 3: comparison with mainstream methods and a clear table.
- Section 4: experiments, representative metrics, strongest scenarios, and limitations.
- Section 5: open-source/reproduction guidance, implementation details, transferability.
- Section 6: one-sentence core idea under 20 Chinese characters and a 3-5 step jargon-light memory pipeline.
- Markdown math: all mathematical notation must use `$...$` or `$$...$$`; code fences are only for real code or commands.
- Evidence hygiene: explicitly note any mismatch among abstract, introduction, tables, appendix, or repository evidence.

## Resources

- `scripts/fetch_arxiv_paper.py`: download arXiv metadata/PDF/source and extract text for analysis.
- `references/method-analysis-template.md`: strict Chinese Markdown report skeleton.
