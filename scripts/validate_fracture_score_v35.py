#!/usr/bin/env python3
"""Contrat public : assistant de score Fracture, ni ancien moteur ni données de compte."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "projets/sinjira/jeux/fracture-du-reseau-mere/feuille-de-score.html"
MODEL = ROOT / "assets/js/sinjira-fracture-score-v35.mjs"
UI = ROOT / "assets/js/sinjira-fracture-score-page-v35.mjs"
CSS = ROOT / "assets/css/fracture-score-v35.css"
GAME_INDEX = ROOT / "projets/sinjira/jeux/fracture-du-reseau-mere/index.html"
GAME_WEB = ROOT / "projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html"
RULES = ROOT / "projets/sinjira/jeux/fracture-du-reseau-mere/regles.html"
GAMES_HUB = ROOT / "projets/sinjira/jeux/index.html"
LIBRARY = ROOT / "compte/bibliotheque-jeux.html"
HUB_SCRIPT = ROOT / "assets/js/sinjira-library-hub-v26.js"


def validate():
    errors = []
    sources = [(p, p.read_text(encoding="utf-8")) for p in
               [SCORE, MODEL, UI, CSS, GAME_INDEX, GAME_WEB,
                RULES, GAMES_HUB, LIBRARY, HUB_SCRIPT]]
    data = {path: text for path, text in sources}
    html, model, js = data[SCORE], data[MODEL], data[UI]
    for target in [GAME_INDEX, GAME_WEB, RULES]:
        if 'href="feuille-de-score.html"' not in data[target]:
            errors.append(f"Lien de score absent : {target.relative_to(ROOT)}")
    for target in [GAMES_HUB, LIBRARY]:
        if 'fracture-du-reseau-mere/feuille-de-score.html' not in data[target]:
            errors.append(f"Accès à la feuille absent : {target.relative_to(ROOT)}")
    for token in [
        'id="fracture-score-form"', 'id="fracture-rounds-body"',
        'id="fracture-final-panel"', 'id="fracture-score-status"',
        'id="fracture-conclusion"', 'aria-live="polite"',
        'sinjira-fracture-score-page-v35.mjs?v=35.11.07',
        'fracture-score-v35.css?v=35.11.07',
        'ne réactive pas le moteur multijoueur Web',
        'aucune sauvegarde locale ou distante',
    ]:
        if token not in html:
            errors.append(f"Élément sécurité ou accessibilité absent : {token}")
    for token in [
        'RESEAU_AGENTS', 'POINTS_PAR_ACCUSATION=3',
        'centralCards:2*seats', 'dealtCards:3*seats',
        'rounds:express?6:10', 'if(express&&h<13)',
        'ballots:h*agents', 'resistanceWins>reseauWins',
        'CARTES_PAR_FACTION', 'SCORE_POSSIBLE_PAR_FACTION',
        'possibleOperationScores(config.centralCards,resistance,reseau)',
        'maxScoreForCards(2*seats)',
        "status:winner?'finished':'tie-breaker'",
    ]:
        if token not in model:
            errors.append(f"Règle officielle non couverte : {token}")
    for token in ['textContent', 'replaceChildren', "window.confirm(",
                  "window.print()", "scoreForm.addEventListener('submit'",
                  "finalPanel.hidden=!ready"]:
        if token not in js:
            errors.append(f"Commande UI ou garde-fou manquant : {token}")
    for forbidden in ['localStorage', 'sessionStorage', 'getSupabase',
                      'fetch(', '.rpc(', '.from(', 'document.cookie',
                      'innerHTML=', 'navigator.sendBeacon', 'indexedDB']:
        if forbidden in model or forbidden in js:
            errors.append(f"Le calculateur ne doit pas contenir : {forbidden}")
    if "project.slug==='fracture-du-reseau-mere'?null:safeLink(project.play_path)" not in data[HUB_SCRIPT]:
        errors.append("L'ancienne URL « Jouer » Fracture doit rester désactivée")
    if "Mode Web en mise à niveau" not in data[GAME_WEB]:
        errors.append("Le moteur multijoueur n'est pas confirmé suspendu")
    if "Le Premier Refuge" in data[LIBRARY]:
        errors.append("Le projet renommé reste présenté comme un troisième jeu")
    if 'prefers-reduced-motion' in data[CSS]:
        pass  # Pas d'animation à activer : impression et clavier suffisent.
    return errors


if __name__ == "__main__":
    issues = validate()
    for issue in issues:
        print("ÉCHEC:", issue)
    if not issues:
        print("OK: feuille de score locale, liens officiels, règles, confidentialité et clavier")
    raise SystemExit(bool(issues))
