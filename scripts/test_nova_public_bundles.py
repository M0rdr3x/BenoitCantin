#!/usr/bin/env python3
"""Verrouiller l'identité exacte des corpus Javascript publics et des JSON GitHub.

Aucune requête externe ni aucun bulletin. Le mode Pages legacy exclut data/*.json,
mais conserve les JS publics revus, dont la CI prouve la correspondance.
"""
import json
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

    for page, names in (
        ("boussole-electorale.html",("assets/boussole-public-corpus.js?v=1","assets/boussole-electorale.js?v=3.4.15")),
        ("sondage-citoyen.html",("assets/sondage-public-corpus.js?v=1","assets/sondage-citoyen.js?v=6")),
    ):
        content = (NOVA / page).read_text(encoding="utf-8")
        assert all(content.count(name) == 1 for name in names), page
        assert content.index(names[0]) < content.index(names[1]), f"Ordre de chargement invalide: {page}"

    jekyll = (ROOT / "scripts" / "validate_jekyll_emergency_pages.py").read_text(encoding="utf-8")
    assert '"projets/projet-nova/assets/boussole-public-corpus.js"' in jekyll
    assert '"projets/projet-nova/assets/sondage-public-corpus.js"' in jekyll

    # Valider syntaxiquement les deux objets, sans dépendance NPM ni navigation.
    for name in ("boussole-public-corpus.js","sondage-public-corpus.js"):
        subprocess.run(["node","--check",str(NOVA / "assets" / name)],check=True)

    print("OK: bundle questionnaire 64/16, preuves et registre exacts, sondage 8 questions fermé, scripts chargés dans le bon ordre.")


if __name__ == "__main__":
    main()
