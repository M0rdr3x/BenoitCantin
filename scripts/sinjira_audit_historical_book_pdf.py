#!/usr/bin/env python3
"""Audit métrique d'un ancien PDF SINJIRA fourni par son détenteur.

Usage:
    python -m pip install pymupdf
    python scripts/sinjira_audit_historical_book_pdf.py --input /chemin/vers/roman.pdf --output /dossier-local/mesures.json

IMPORTANT:
- Cet outil ne valide ni un manuscrit courant ni une édition finale.
- Aucun texte de chapitre, aucune citation ni empreinte de manuscrit ne sort dans le JSON.
- L'utilisateur décide explicitement d'où lire le PDF et où enregistrer les métriques.
"""
from __future__ import annotations
import argparse
import collections
import json
from pathlib import Path
import re
import statistics
import unicodedata

HEADER_RE = re.compile(r"(?m)^Chapitre\s+(\d{1,3})\s*[—–-]\s*(.+?)\s*$")
RIGHTS_RE = re.compile(r"(?m)^© 2026 Benoit Cantin[^\n]*\n?")
WORD_RE = re.compile(r"[a-zà-öø-ÿ0-9]+(?:['-][a-zà-öø-ÿ0-9]+)*")
WINDOW_LENGTH = 30

def tokenize(raw: str) -> list[str]:
    return WORD_RE.findall(unicodedata.normalize("NFKC", raw).lower().replace("’", "'"))

def audit_pdf(input_pdf: Path) -> dict:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Installer d'abord PyMuPDF : python -m pip install pymupdf") from exc

    if not input_pdf.is_file() or input_pdf.suffix.lower() != ".pdf":
        raise ValueError("Le fichier d'entrée doit être un PDF existant.")
    with fitz.open(input_pdf) as doc:
        if doc.is_encrypted:
            raise ValueError("PDF chiffré : extraction impossible sans autorisation.")
        page_count = len(doc)
        text = "\n".join(page.get_text() for page in doc)
    headings = list(HEADER_RE.finditer(text))
    if not headings:
        raise ValueError("Aucun en-tête Chapitre N détecté; vérifier l'archive manuellement.")

    chapters = []
    for i, heading in enumerate(headings):
        stop = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        words = tokenize(RIGHTS_RE.sub("", text[heading.end():stop]))
        chapters.append({"number": int(heading.group(1)), "words": words})
    by_window: dict[tuple[str, ...], set[int]] = collections.defaultdict(set)
    for chapter in chapters:
        tokens = chapter["words"]
        for i in range(max(0, len(tokens) - WINDOW_LENGTH + 1)):
            by_window[tuple(tokens[i:i + WINDOW_LENGTH])].add(chapter["number"])
    shared = {token_window for token_window, ids in by_window.items() if len(ids) > 1}

    results = []
    for chapter in chapters:
        words = chapter["words"]
        covered = [False] * len(words)
        repetitions = 0
        for i in range(max(0, len(words) - WINDOW_LENGTH + 1)):
            if tuple(words[i:i + WINDOW_LENGTH]) in shared:
                repetitions += 1
                covered[i:i + WINDOW_LENGTH] = [True] * WINDOW_LENGTH
        results.append({
            "number": chapter["number"],
            "word_count": len(words),
            "windows_30_tokens_shared_across_chapters": repetitions,
            "word_share_covered_by_shared_windows_percent": round(100 * sum(covered) / len(words), 2) if words else 0.0,
            "review_status": "ARCHIVE_HISTORIQUE_NON_CERTIFIANTE",
        })
    weighted = sum(c["word_count"] * c["word_share_covered_by_shared_windows_percent"] for c in results)
    size = sum(c["word_count"] for c in results)
    return {
        "schema": "sinjira-archive-pdf-audit-reproducible/v1",
        "scope": "ARCHIVE_NON_CERTIFIANTE",
        "no_manuscript_text_exported": True,
        "methodology": "Fenêtres identiques de 30 tokens entre chapitres; couverture de tokens au sein de chaque chapitre.",
        "pages": page_count,
        "chapter_headings_found": len(headings),
        "unique_chapter_numbers": len(set(c["number"] for c in chapters)),
        "prologue_heading_found": bool(re.search(r"(?mi)^\s*Prologue\s*$", text)),
        "epilogue_heading_found": bool(re.search(r"(?mi)^\s*[ÉE]pilogue\s*$", text)),
        "total_chapter_tokens": size,
        "shared_unique_windows_30_tokens": len(shared),
        "all_chapter_occurrences_of_shared_windows": sum(c["windows_30_tokens_shared_across_chapters"] for c in results),
        "weighted_coverage_percent": round(weighted / size, 2) if size else None,
        "chapters": results,
        "verified_editorial_completion_percentage": None,
        "current_master_authoritative": False
    }

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True, help="Chemin du PDF historique autorisé")
    ap.add_argument("--output", type=Path, required=True, help="JSON local de métriques, sans texte")
    ap.add_argument("--overwrite", action="store_true", help="Autoriser explicitement la réécriture")
    args = ap.parse_args()
    if args.output.exists() and not args.overwrite:
        ap.error("Refus d'écraser le rapport existant sans --overwrite.")
    report = audit_pdf(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Audit métrique enregistré, sans texte de manuscrit :", args.output)
    print(f"{report['pages']} pages; {report['chapter_headings_found']} chapitres; fin éditoriale NON certifiée.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
