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
PRIVATE_BOOK_EDGE_PATH = ROOT / "supabase/functions/get-private-book-url/index.ts"
CONFIG_PATH = ROOT / "supabase/config.toml"

FULL_BASENAME = "SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf"
FULL_SHA256 = "9862a11000fe46a2010e7fb902b9bba3dfea70724855a6fb682e0a6192df88e3"
DEMO_BASENAME = "SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"
DEMO_SHA256 = "aad491ce8861928c561caa035fe5ee8cb16d42a8e307c93828758346cc93f26f"
PRODUCT_SLUG = "sinjira-livre-01-la-cendre-du-jugement"
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


def require_fragments(text: str, fragments: dict[str, str], prefix: str, errors: list[str]) -> None:
    for label, fragment in fragments.items():
        if fragment not in text:
            errors.append(f"{prefix}: {label} absent.")


def validate(
    root: Path,
    edge_path: Path,
    private_book_edge_path: Path,
    config_path: Path,
    contract_path: Path,
) -> list[str]:
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
        ("full_edition", "delivery"): "authenticated_private_storage_only",
        ("full_edition", "private_endpoint"): "get-private-book-url",
        ("full_edition", "entitlement_table"): "user_entitlements",
        ("full_edition", "product_slug"): PRODUCT_SLUG,
        ("full_edition", "activation_env"): "SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED",
        ("full_edition", "signed_url_seconds"): 300,
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

    full = contract.get("full_edition", {})
    signed_seconds = int(full.get("signed_url_seconds", 999999))
    signed_max = int(full.get("signed_url_max_seconds", 0))
    if signed_seconds > signed_max:
        errors.append("La durée de l'URL signée dépasse le maximum du contrat.")

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
        edge = ""

    require_fragments(
        edge,
        {
            "authentification/résolution utilisateur": "optionalUser(req)",
            "client serveur pour décision d'accès": "serviceClient()",
            "contrôle du rang d'accès": "userRank<(ranks[doc.access_level]||999)",
            "URL signée de courte durée": "createSignedUrl(doc.storage_path,600)",
            "réponse privée non mise en cache": "'Cache-Control':'private, no-store, max-age=0'",
            "protection MIME": "'X-Content-Type-Options':'nosniff'",
        },
        "Frontière générique affaiblie",
        errors,
    )
    if "getPublicUrl(" in edge:
        errors.append("get-document-url ne doit jamais produire une URL publique de Storage.")

    try:
        private_edge = private_book_edge_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"Fonction get-private-book-url illisible: {exc}")
        private_edge = ""

    require_fragments(
        private_edge,
        {
            "utilisateur authentifié obligatoire": "requiredUser(req)",
            "produit Livre I fixe": PRODUCT_SLUG,
            "table de droits explicites": ".from('user_entitlements')",
            "droit lié à la personne": ".eq('user_id',user.id)",
            "droit lié au produit": ".eq('product_id',product.id)",
            "activation serveur explicite": "Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED')==='true'",
            "bucket privé fourni par le serveur": "Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_BUCKET')",
            "chemin privé fourni par le serveur": "Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_PATH')",
            "durée signée de 300 secondes": "const SIGNED_URL_SECONDS=300",
            "création URL signée privée": "createSignedUrl(storage.storagePath,SIGNED_URL_SECONDS",
            "réponse privée non mise en cache": "'Cache-Control':'private, no-store, max-age=0'",
        },
        "Porte privée Livre I affaiblie",
        errors,
    )
    if "external_url" in private_edge or "getPublicUrl(" in private_edge:
        errors.append("La porte privée Livre I ne doit accepter aucune URL externe/publique de repli.")

    try:
        config = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"Configuration Supabase illisible: {exc}")
        config = ""
    if "[functions.get-private-book-url]\nverify_jwt = true" not in config:
        errors.append("get-private-book-url doit conserver verify_jwt = true dans supabase/config.toml.")

    return errors


def self_test() -> None:
    with TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "projets/sinjira/codex").mkdir(parents=True)
        (root / "projets/sinjira/documents").mkdir(parents=True)
        (root / "assets").mkdir()
        (root / "supabase/functions/get-document-url").mkdir(parents=True)
        (root / "supabase/functions/get-private-book-url").mkdir(parents=True)

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
                "delivery": "authenticated_private_storage_only",
                "private_endpoint": "get-private-book-url",
                "entitlement_table": "user_entitlements",
                "product_slug": PRODUCT_SLUG,
                "activation_env": "SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED",
                "signed_url_seconds": 300,
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

        private_edge = f"""requiredUser(req); serviceClient();
const PRODUCT_SLUG='{PRODUCT_SLUG}';
const SIGNED_URL_SECONDS=300;
Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED')==='true';
Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_BUCKET');
Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_PATH');
service.from('user_entitlements').eq('user_id',user.id).eq('product_id',product.id);
service.storage.from(storage.bucket).createSignedUrl(storage.storagePath,SIGNED_URL_SECONDS);
const h={{'Cache-Control':'private, no-store, max-age=0'}};
"""
        private_edge_path = root / "supabase/functions/get-private-book-url/index.ts"
        private_edge_path.write_text(private_edge, encoding="utf-8")

        config_path = root / "supabase/config.toml"
        config_path.write_text("[functions.get-private-book-url]\nverify_jwt = true\n", encoding="utf-8")

        clean = validate(root, edge_path, private_edge_path, config_path, contract_path)
        if clean:
            raise AssertionError("Le cas sain doit passer: " + " | ".join(clean))

        leaked = root / "projets/sinjira/documents" / FULL_BASENAME
        leaked.write_bytes(b"not-the-real-pdf")
        leaked_errors = validate(root, edge_path, private_edge_path, config_path, contract_path)
        if not any("Édition intégrale interdite" in item for item in leaked_errors):
            raise AssertionError("Le nom de fichier intégral exposé doit être bloqué.")
        leaked.unlink()

        public_page = root / "projets/sinjira/index.html"
        public_page.write_text(f'<a href="/documents/{FULL_BASENAME}">Livre complet</a>', encoding="utf-8")
        link_errors = validate(root, edge_path, private_edge_path, config_path, contract_path)
        if not any("Lien/référence statique" in item for item in link_errors):
            raise AssertionError("Une URL statique vers l'intégrale doit être bloquée.")
        public_page.unlink()

        private_edge_path.write_text(private_edge + "\nconst external_url='https://example.invalid/full.pdf';\n", encoding="utf-8")
        private_errors = validate(root, edge_path, private_edge_path, config_path, contract_path)
        if not any("aucune URL externe/publique" in item for item in private_errors):
            raise AssertionError("Une URL externe dans la porte privée doit être bloquée.")

        private_edge_path.write_text(private_edge, encoding="utf-8")
        config_path.write_text("[functions.get-private-book-url]\nverify_jwt = false\n", encoding="utf-8")
        jwt_errors = validate(root, edge_path, private_edge_path, config_path, contract_path)
        if not any("verify_jwt = true" in item for item in jwt_errors):
            raise AssertionError("La désactivation de la vérification JWT doit être bloquée.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Valide la frontière de diffusion du Livre I de SINJIRA.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("OK auto-test frontière Livre I.")
        return 0

    errors = validate(ROOT, EDGE_PATH, PRIVATE_BOOK_EDGE_PATH, CONFIG_PATH, CONTRACT_PATH)
    if errors:
        print("ÉCHEC frontière Livre I:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("OK Livre I: démo publique stable, intégrale absente du dépôt public, entitlement requis et livraison privée bornée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
