#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "projets/sinjira/codex/livre-i-delivery-contract.json"
EDGE_PATH = ROOT / "supabase/functions/get-document-url/index.ts"

FULL_BASENAME = "SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf"
FULL_SHA256 = "9862a11000fe46a2010e7fb902b9bba3dfea70724855a6fb682e0a6192df88e3"
DEMO_BASENAME = "SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"
DEMO_SHA256 = "aad491ce8861928c561caa035fe5ee8cb16d42a8e307c93828758346cc93f26f"
STATIC_EXTENSIONS = {".html", ".js", ".mjs", ".css", ".json", ".xml", ".webmanifest", ".txt"}
SKIP_PARTS = {"codex", ".git", "node_modules"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def static_roots(root: Path) -> tuple[Path, ...]:
    return (
        root / "projets/sinjira",
        root / "assets",
        root / "sitemap.xml",
        root / "robots.txt",
        root / "manifest.webmanifest",
    )


def iter_static_text_files(root: Path):
    for candidate in static_roots(root):
        if not candidate.exists():
            continue
        if candidate.is_file():
            yield candidate
            continue
        for path in candidate.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in STATIC_EXTENSIONS:
                continue
            relative = path.relative_to(root)
            if any(part in SKIP_PARTS for part in relative.parts):
                continue
            yield path


def validate(root: Path, edge_path: Path, contract_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Contrat Livre I illisible: {exc}"]

    expected = {
        ("schema",): "sinjira.livre-i.delivery.v1",
        ("publication_state",): "not_activated",
        ("human_gate_required",): True,
        ("demo", "pages"): 83,
        ("demo", "sha256"): DEMO_SHA256,
        ("full_edition", "pages"): 1066,
        ("full_edition", "sha256"): FULL_SHA256,
        ("full_edition", "public_repository_allowed"): False,
        ("full_edition", "public_static_url_allowed"): False,
        ("full_edition", "signed_url_max_seconds"): 600,
        ("full_edition", "activation_requires_explicit_human_decision"): True,
    }
    for keys, expected_value in expected.items():
        current = contract
        try:
            for key in keys:
                current = current[key]
        except (KeyError, TypeError):
            errors.append("Contrat Livre I incomplet: " + ".".join(keys))
            continue
        if current != expected_value:
            errors.append(
                f"Contrat Livre I inattendu pour {'.'.join(keys)}: {current!r} != {expected_value!r}"
            )

    demo_url = str(contract.get("demo", {}).get("public_url", ""))
    if not demo_url.endswith("/projets/sinjira/documents/" + DEMO_BASENAME):
        errors.append("L'URL publique stable de la démo n'est plus celle attendue.")

    for path in root.rglob(FULL_BASENAME):
        if path.is_file() and ".git" not in path.parts:
            errors.append(f"Édition intégrale interdite dans le dépôt public: {path.relative_to(root)}")

    for pdf in root.rglob("*.pdf"):
        if ".git" in pdf.parts or not pdf.is_file():
            continue
        try:
            digest = sha256_file(pdf)
        except OSError as exc:
            errors.append(f"Impossible de vérifier {pdf.relative_to(root)}: {exc}")
            continue
        if digest == FULL_SHA256:
            errors.append(
                f"Octets de l'édition intégrale détectés dans le dépôt public: {pdf.relative_to(root)}"
            )

    for path in iter_static_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        relative = path.relative_to(root)
        if FULL_BASENAME in text:
            errors.append(f"Lien/référence statique vers l'intégrale détecté: {relative}")
        if FULL_SHA256 in text:
            errors.append(f"Empreinte de l'intégrale injectée dans un actif public: {relative}")

    try:
        edge = edge_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"Fonction get-document-url illisible: {exc}")
        return errors

    required_fragments = {
        "authentification/résolution utilisateur": "optionalUser(req)",
        "client serveur pour décision d'accès": "serviceClient()",
        "contrôle du rang d'accès": "userRank<(ranks[doc.access_level]||999)",
        "URL signée de courte durée": "createSignedUrl(doc.storage_path,600)",
        "réponse privée non mise en cache": "'Cache-Control':'private, no-store, max-age=0'",
        "protection MIME": "'X-Content-Type-Options':'nosniff'",
    }
    for label, fragment in required_fragments.items():
        if fragment not in edge:
            errors.append(f"Frontière privée affaiblie: {label} absent de get-document-url.")

    if "getPublicUrl(" in edge:
        errors.append("get-document-url ne doit jamais produire une URL publique de Storage.")

    return errors


def self_test() -> None:
    with TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "projets/sinjira/codex").mkdir(parents=True)
        (root / "projets/sinjira/documents").mkdir(parents=True)
        (root / "assets").mkdir()
        (root / "supabase/functions/get-document-url").mkdir(parents=True)

        contract = {
            "schema": "sinjira.livre-i.delivery.v1",
            "publication_state": "not_activated",
            "human_gate_required": True,
            "demo": {
                "pages": 83,
                "sha256": DEMO_SHA256,
                "public_url": "https://www.benoitcantin.com/projets/sinjira/documents/" + DEMO_BASENAME,
            },
            "full_edition": {
                "pages": 1066,
                "sha256": FULL_SHA256,
                "public_repository_allowed": False,
                "public_static_url_allowed": False,
                "signed_url_max_seconds": 600,
                "activation_requires_explicit_human_decision": True,
            },
        }
        contract_path = root / "projets/sinjira/codex/livre-i-delivery-contract.json"
        contract_path.write_text(json.dumps(contract), encoding="utf-8")

        edge = """optionalUser(req); serviceClient();
if(userRank<(ranks[doc.access_level]||999)){}
service.storage.from(doc.storage_bucket).createSignedUrl(doc.storage_path,600);
const h={'Cache-Control':'private, no-store, max-age=0','X-Content-Type-Options':'nosniff'};
"""
        edge_path = root / "supabase/functions/get-document-url/index.ts"
        edge_path.write_text(edge, encoding="utf-8")

        clean = validate(root, edge_path, contract_path)
        if clean:
            raise AssertionError("Le cas sain doit passer: " + " | ".join(clean))

        leaked = root / "projets/sinjira/documents" / FULL_BASENAME
        leaked.write_bytes(b"not-the-real-pdf")
        leaked_errors = validate(root, edge_path, contract_path)
        if not any("Édition intégrale interdite" in item for item in leaked_errors):
            raise AssertionError("Le nom de fichier intégral exposé doit être bloqué.")
        leaked.unlink()

        public_page = root / "projets/sinjira/index.html"
        public_page.write_text(f'<a href="/documents/{FULL_BASENAME}">Livre complet</a>', encoding="utf-8")
        link_errors = validate(root, edge_path, contract_path)
        if not any("Lien/référence statique" in item for item in link_errors):
            raise AssertionError("Une URL statique vers l'intégrale doit être bloquée.")
        public_page.unlink()

        edge_path.write_text(edge + "\nservice.storage.from('x').getPublicUrl('full.pdf');\n", encoding="utf-8")
        edge_errors = validate(root, edge_path, contract_path)
        if not any("URL publique" in item for item in edge_errors):
            raise AssertionError("getPublicUrl doit être bloqué.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Valide la frontière de diffusion du Livre I de SINJIRA.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("OK auto-test frontière Livre I.")
        return 0

    errors = validate(ROOT, EDGE_PATH, CONTRACT_PATH)
    if errors:
        print("ÉCHEC frontière Livre I:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("OK Livre I: démo publique stable, intégrale absente du dépôt public et livraison privée bornée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
