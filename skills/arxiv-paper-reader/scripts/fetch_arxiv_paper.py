#!/usr/bin/env python3
"""Fetch arXiv paper metadata, PDF, source, and extracted text."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


USER_AGENT = "Codex arxiv-paper-reader/1.0"
ARXIV_API = "https://export.arxiv.org/api/query?id_list={id}"
ARXIV_PDF = "https://arxiv.org/pdf/{id}.pdf"
ARXIV_SOURCE = "https://arxiv.org/e-print/{id}"


def normalize_arxiv_id(value: str) -> str:
    raw = value.strip().strip("<>")
    parsed = urllib.parse.urlparse(raw)
    candidate = raw
    if parsed.netloc:
        path = parsed.path.strip("/")
        match = re.search(r"(?:abs|pdf|e-print)/(.+)$", path)
        if match:
            candidate = match.group(1)
    candidate = candidate.removesuffix(".pdf")
    candidate = re.sub(r"[?#].*$", "", candidate)
    if not re.match(r"^[a-zA-Z0-9._/-]+(?:v\d+)?$", candidate):
        raise ValueError(f"Cannot parse arXiv id from input: {value}")
    return candidate


def safe_name(arxiv_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", arxiv_id)


def request_bytes(url: str, attempts: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=90) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, ConnectionResetError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(2 * attempt)
    assert last_error is not None
    raise last_error


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def fetch_metadata(arxiv_id: str) -> dict:
    data = request_bytes(ARXIV_API.format(id=urllib.parse.quote(arxiv_id)))
    root = ET.fromstring(data)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    entry = root.find("atom:entry", ns)
    if entry is None:
        return {"id": arxiv_id}

    def text(path: str) -> str:
        node = entry.find(path, ns)
        return " ".join(node.text.split()) if node is not None and node.text else ""

    authors = []
    for author in entry.findall("atom:author", ns):
        name = author.find("atom:name", ns)
        if name is not None and name.text:
            authors.append(" ".join(name.text.split()))

    categories = [cat.attrib.get("term", "") for cat in entry.findall("atom:category", ns)]
    return {
        "id": arxiv_id,
        "title": text("atom:title"),
        "authors": authors,
        "summary": text("atom:summary"),
        "published": text("atom:published"),
        "updated": text("atom:updated"),
        "categories": [cat for cat in categories if cat],
        "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": ARXIV_PDF.format(id=arxiv_id),
        "source_url": ARXIV_SOURCE.format(id=arxiv_id),
    }


def safe_extract_tar(tar_path: Path, target_dir: Path) -> None:
    target_root = target_dir.resolve()
    with tarfile.open(tar_path) as archive:
        for member in archive.getmembers():
            member_target = (target_dir / member.name).resolve()
            if not str(member_target).startswith(str(target_root)):
                raise RuntimeError(f"Unsafe tar member path: {member.name}")
        try:
            archive.extractall(target_dir, filter="data")
        except TypeError:
            archive.extractall(target_dir)


def extract_source(download_path: Path, target_dir: Path) -> bool:
    target_dir.mkdir(parents=True, exist_ok=True)
    if tarfile.is_tarfile(download_path):
        safe_extract_tar(download_path, target_dir)
        return True

    data = download_path.read_bytes()
    try:
        data = gzip.decompress(data)
    except OSError:
        pass

    if b"\\documentclass" in data or b"\\begin{document}" in data:
        (target_dir / "main.tex").write_bytes(data)
        return True

    (target_dir / "source_payload.bin").write_bytes(data)
    return False


def extract_pdf_text(pdf_path: Path, output_path: Path) -> bool:
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        cmd = [pdftotext, "-layout", "-enc", "UTF-8", str(pdf_path), str(output_path)]
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=120)
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return True

    for module_name in ("pypdf", "PyPDF2"):
        try:
            module = __import__(module_name)
        except ImportError:
            continue
        reader_cls = getattr(module, "PdfReader", None)
        if reader_cls is None:
            continue
        reader = reader_cls(str(pdf_path))
        chunks = []
        for page in reader.pages:
            chunks.append(page.extract_text() or "")
        output_path.write_text("\n\n".join(chunks), encoding="utf-8")
        return output_path.stat().st_size > 0

    return False


def collect_source_text(source_dir: Path, output_path: Path) -> list[str]:
    extensions = {".tex", ".bbl", ".bib", ".md", ".txt"}
    files = sorted(
        path for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in extensions
    )
    with output_path.open("w", encoding="utf-8", errors="replace") as out:
        for path in files:
            rel = path.relative_to(source_dir)
            out.write(f"\n\n===== {rel.as_posix()} =====\n\n")
            out.write(path.read_text(encoding="utf-8", errors="replace"))
    return [str(path.relative_to(source_dir)) for path in files]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", help="arXiv ID or arXiv abs/pdf/e-print URL")
    parser.add_argument("--out", type=Path, default=None, help="Output directory")
    parser.add_argument("--skip-pdf", action="store_true", help="Do not download PDF")
    parser.add_argument("--skip-source", action="store_true", help="Do not download source")
    args = parser.parse_args(argv)

    arxiv_id = normalize_arxiv_id(args.paper)
    out_dir = args.out or Path.cwd() / f"arxiv-{safe_name(arxiv_id)}"
    out_dir.mkdir(parents=True, exist_ok=True)

    metadata = fetch_metadata(arxiv_id)
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    results = {
        "arxiv_id": arxiv_id,
        "out_dir": str(out_dir.resolve()),
        "metadata": "metadata.json",
        "pdf": None,
        "pdf_text": None,
        "source_archive": None,
        "source_dir": None,
        "source_text": None,
        "source_files": [],
        "warnings": [],
    }

    if not args.skip_pdf:
        try:
            pdf_path = out_dir / "paper.pdf"
            write_bytes(pdf_path, request_bytes(ARXIV_PDF.format(id=urllib.parse.quote(arxiv_id, safe="/"))))
            results["pdf"] = "paper.pdf"
            text_path = out_dir / "paper.txt"
            if extract_pdf_text(pdf_path, text_path):
                results["pdf_text"] = "paper.txt"
            else:
                results["warnings"].append("PDF downloaded, but text extraction failed.")
        except (urllib.error.URLError, subprocess.SubprocessError, OSError) as exc:
            results["warnings"].append(f"PDF fetch/extraction failed: {exc}")

    if not args.skip_source:
        try:
            archive_path = out_dir / "source_download"
            write_bytes(archive_path, request_bytes(ARXIV_SOURCE.format(id=urllib.parse.quote(arxiv_id, safe="/"))))
            results["source_archive"] = "source_download"
            source_dir = out_dir / "source"
            if extract_source(archive_path, source_dir):
                results["source_dir"] = "source"
                source_text = out_dir / "source_text.txt"
                results["source_files"] = collect_source_text(source_dir, source_text)
                results["source_text"] = "source_text.txt"
            else:
                results["warnings"].append("Source downloaded, but no TeX-like source was detected.")
        except (urllib.error.URLError, tarfile.TarError, OSError, RuntimeError) as exc:
            results["warnings"].append(f"Source fetch/extraction failed: {exc}")

    (out_dir / "fetch_manifest.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
