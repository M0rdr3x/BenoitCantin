#!/usr/bin/env python3
"""Validation statique minimale du site BenoitCantin/SINJIRA.

Aucune dépendance externe. Destiné à GitHub Actions et à l'exécution locale.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", "node_modules"}
TEXT_EXTS = {".html", ".js", ".css", ".json", ".md", ".txt", ".xml", ".webmanifest", ".sql", ".ts"}
FORBIDDEN_SECRET_PATTERNS = [
    re.compile(r"SUPABASE_SERVICE_ROLE_KEY\s*[:=]\s*['\"]?[A-Za-z0-9._-]{20,}", re.I),
    re.compile(r"OPENAI_API_KEY\s*[:=]\s*['\"]?sk-[A-Za-z0-9_-]{16,}", re.I),
    re.compile(r"sk-proj-[A-Za-z0-9_-]{16,}"),
]
FULL_BOOK_PATTERNS = [
    re.compile(r"SINJIRA.*Livre.*01.*La.*Cendre.*Jugement(?!.*DEMO).*\.pdf", re.I),
    re.compile(r"MAITRE.*CORRIGE.*\.pdf", re.I),
]


class RefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str]] = []
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(data["id"])
        attr = {"a": "href", "img": "src", "script": "src", "link": "href", "source": "src", "video": "src", "audio": "src", "iframe": "src"}.get(tag)
        if attr and data.get(attr):
            self.refs.append((tag, data[attr]))


def files():
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in IGNORED_DIRS for part in p.parts):
            continue
        yield p


def resolve_ref(page: Path, raw: str) -> Path | None:
    if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "blob:", "//")):
        return None
    u = urlparse(raw)
    if u.scheme in {"http", "https"}:
        return None
    path = unquote(u.path)
    if not path:
        return None
    q = ROOT / path.lstrip("/") if path.startswith("/") else page.parent / path
    if path.endswith("/"):
        q = q / "index.html"
    if not q.exists() and q.suffix == "" and (q / "index.html").exists():
        q = q / "index.html"
    return q.resolve()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    all_files = list(files())

    # Fichiers parasites déjà observés dans les anciennes versions.
    for p in all_files:
        if p.name == "1":
            errors.append(f"Fichier parasite nommé '1': {p.relative_to(ROOT)}")

    # Le roman intégral et les secrets ne doivent jamais être dans le dépôt public.
    for p in all_files:
        rel = str(p.relative_to(ROOT))
        if any(rx.search(rel) for rx in FULL_BOOK_PATTERNS):
            errors.append(f"Roman intégral potentiellement public: {rel}")
        if p.suffix.lower() in TEXT_EXTS and p.stat().st_size <= 3_000_000:
            text = p.read_text("utf-8", errors="ignore")
            for rx in FORBIDDEN_SECRET_PATTERNS:
                if rx.search(text):
                    errors.append(f"Secret potentiel dans {rel}: {rx.pattern}")

    html_files = [p for p in all_files if p.suffix.lower() == ".html"]
    for page in html_files:
        parser = RefParser()
        try:
            parser.feed(page.read_text("utf-8", errors="ignore"))
        except Exception as exc:
            errors.append(f"HTML illisible {page.relative_to(ROOT)}: {exc}")
            continue
        duplicates = sorted({x for x in parser.ids if parser.ids.count(x) > 1})
        if duplicates:
            errors.append(f"IDs HTML dupliqués dans {page.relative_to(ROOT)}: {', '.join(duplicates)}")
        for tag, raw in parser.refs:
            target = resolve_ref(page, raw)
            if target is not None and not target.exists():
                errors.append(f"Référence locale manquante dans {page.relative_to(ROOT)} ({tag}): {raw}")

    # Routes critiques.
    required = [
        "index.html",
        "404.html",
        "admin/index.html",
        "admin/sinjira/index.html",
        "compte/index.html",
        "compte/profil.html",
        "compte/mon-personnage.html",
        "compte/reseau-personnage.html",
        "projets/sinjira/index.html",
        "projets/sinjira/registre/index.html",
        "projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            errors.append(f"Route critique absente: {rel}")

    # JavaScript syntaxique si Node est présent.
    js_files = [p for p in all_files if p.suffix.lower() == ".js"]
    try:
        subprocess.run(["node", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for p in js_files:
            proc = subprocess.run(["node", "--check", str(p)], text=True, capture_output=True)
            if proc.returncode:
                errors.append(f"Erreur JavaScript dans {p.relative_to(ROOT)}: {proc.stderr.strip()}")
    except (FileNotFoundError, subprocess.CalledProcessError):
        warnings.append("Node indisponible: validation syntaxique JavaScript ignorée.")

    print(f"Validation SINJIRA: {len(html_files)} HTML, {len(js_files)} JS, {len(all_files)} fichiers.")
    for w in warnings:
        print(f"AVERTISSEMENT: {w}")
    if errors:
        print(f"ECHEC: {len(errors)} problème(s) détecté(s).")
        for e in errors:
            print(f"- {e}")
        return 1
    print("OK: aucune erreur statique bloquante détectée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
