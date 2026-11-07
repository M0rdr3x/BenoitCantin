#!/usr/bin/env python3
"""Verrouiller l'identité exacte des corpus Javascript publics et des JSON GitHub.

Aucune requête externe ni aucun bulletin. Le mode Pages legacy exclut data/*.json,
mais conserve les JS publics revus, dont la CI prouve la correspondance.
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets" / "projet-nova"


def load_bundle(name: str, variable: str):
    text = (NOVA / "assets" / name).read_text(encoding="utf-8")
    prefix = f"window.{variable} = "
    assert text.count(prefix) == 1, f"{name} : affectation publique unique attendue"
    payload = text.split(prefix, 1)[1].strip()
    assert payload.endswith(";"), f"{name}: ponctuation invalide"
    return json.loads(payload[:-1])


def load_json(name: str):
    return json.loads((NOVA / "data" / name).read_text(encoding="utf-8"))


def main() -> None:
    compass = load_bundle("boussole-public-corpus.js", "__NOVA_COMPASS_PUBLIC_CORPORA")
    poll = load_bundle("sondage-public-corpus.js", "__NOVA_POLL_PUBLIC_CORPUS")
    assert set(compass) == {"questionnaire", "parties", "sources", "evidence"}
    for key, name in {
        "questionnaire": "boussole-electorale-v2.json",
        "parties": "boussole-partis-2026.json",
        "sources": "boussole-sources-partis-2026.json",
        "evidence": "boussole-preuves-2026.json",
    }.items():
        assert compass[key] == load_json(name), f"Divergence corpus public: {name}"
    assert poll == load_json("sondage-citoyen-v1.json"), "Divergence questionnaire du sondage"
    assert len(compass["questionnaire"]["questions"]) == 64
    assert len(compass["questionnaire"]["axes"]) == 16
    assert len(poll["questions"]) == 8
    assert poll["published"] is False, "Interdiction d'ouvrir les votes par génération du bundle"

    # Vérifier le code réellement versionné dans chaque page, sans figer
    # des numéros de cache qui évoluent indépendamment des tests de corpus.
    for page, files in (
        ("boussole-electorale.html", (
            "boussole-public-corpus.js", "nova-civic-integrity.js", "boussole-electorale.js")),
        ("sondage-citoyen.html", (
            "sondage-public-corpus.js", "nova-civic-integrity.js", "sondage-citoyen.js")),
    ):
        content = (NOVA / page).read_text(encoding="utf-8")
        sources = re.findall(r'<script\b[^>]*\bsrc="([^"]+)"', content, flags=re.I)
        positions = []
        for filename in files:
            refs = [src for src in sources if src.split("?", 1)[0] == "assets/" + filename]
            assert len(refs) == 1, f"Script absent ou dupliqué dans {page} : {filename}"
            assert re.search(r"[?&]v=[0-9][0-9.]*$", refs[0]), (
                f"Script sans version de cache dans {page} : {filename}")
            assert (NOVA / "assets" / filename).is_file(), f"Script manquant : {filename}"
            positions.append(content.index('src="' + refs[0] + '"'))
        assert positions == sorted(positions) and len(set(positions)) == 3, (
            f"Ordre de chargement invalide dans {page} : corpus, intégrité, application")

    jekyll = (ROOT / "scripts" / "validate_jekyll_emergency_pages.py").read_text(encoding="utf-8")
    assert '"projets/projet-nova/assets/boussole-public-corpus.js"' in jekyll
    assert '"projets/projet-nova/assets/sondage-public-corpus.js"' in jekyll
    assert '"projets/projet-nova/assets/nova-civic-integrity.js"' in jekyll

    # Valider syntaxiquement les deux objets, sans dépendance NPM ni navigation.
    for name in ("boussole-public-corpus.js","sondage-public-corpus.js","nova-civic-integrity.js"):
        subprocess.run(["node","--check",str(NOVA / "assets" / name)],check=True)

    print("OK: bundle questionnaire 64/16, preuves et registre exacts, sondage 8 questions fermé, scripts chargés dans le bon ordre.")


if __name__ == "__main__":
    main()
