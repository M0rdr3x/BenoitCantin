#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets" / "projet-nova"
errors: list[str] = []

if not NOVA.is_dir():
    errors.append("dossier projets/projet-nova absent")

DOCUMENT_MANIFESTS = [
    "data/documents.json",
    "data/documents-word-only.json",
    "documents.json",
    "documents-word-only.json",
]

for rel in DOCUMENT_MANIFESTS:
    p = NOVA / rel
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{rel}: JSON invalide: {exc}")
        continue
    for slug, item in data.items():
        pdf = item.get("pdf")
        if pdf and not (NOVA / pdf).is_file():
            errors.append(f"{rel}: {slug} référence un PDF absent: {pdf}")

manifest_path = NOVA / "data" / "sources.json"
try:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
except Exception as exc:
    manifest = {}
    errors.append(f"data/sources.json invalide ou absent: {exc}")

required_docs = {"corpus", "statuts", "programme"}
document_ids = set((manifest.get("documents") or {}).keys())
if not required_docs.issubset(document_ids):
    errors.append("data/sources.json: corpus/statuts/programme requis")

for doc_id, doc in (manifest.get("documents") or {}).items():
    parts = doc.get("parts") or []
    if not parts:
        errors.append(f"référence {doc_id}: aucune source")
    for part in parts:
        raw = part.get("path", "")
        expected = part.get("sha256", "")
        source = (NOVA / raw).resolve()
        try:
            source.relative_to(ROOT)
        except ValueError:
            errors.append(f"référence {doc_id}: chemin source hors dépôt: {raw}")
            continue
        if not source.is_file():
            errors.append(f"référence {doc_id}: source absente: {raw}")
            continue
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            errors.append(f"référence {doc_id}: SHA-256 invalide: {raw}")
        elif actual != expected:
            errors.append(f"référence {doc_id}: empreinte différente: {raw}")

for p in list(NOVA.rglob("*.html")) + list(NOVA.rglob("*.js")):
    if "node_modules" in p.parts or "vendor" in p.parts:
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    if "formspree.io" in low or "formsubmit.co" in low:
        errors.append(f"{p.relative_to(NOVA)}: fournisseur de formulaire externe encore référencé")
    if "10_formulaire_soutien_preadhesion_projet_nova.pdf" in low:
        errors.append(f"{p.relative_to(NOVA)}: référence à l'ancien PDF de préadhésion")

# Les identifiants de chantier ne doivent pas être exposés dans la couche publique active.
version_re = re.compile(r"\bA[12](?:\.\d+)?\b", re.I)
for p in NOVA.glob("*.html"):
    text = p.read_text(encoding="utf-8", errors="replace")
    public_markup = re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.I | re.S)
    public_markup = re.sub(r"<style\b[^>]*>.*?</style>", "", public_markup, flags=re.I | re.S)
    if version_re.search(public_markup):
        errors.append(f"{p.name}: numéro de version de chantier visible dans l'interface publique")

# La bibliothèque, les manifestes, les références et les fichiers de gouvernance
# servis dans le sous-site ne doivent eux-mêmes contenir aucun numéro de chantier.
active_public_files = [
    NOVA / "assets" / "documents.js",
    NOVA / "data" / "documents.json",
    NOVA / "data" / "documents-word-only.json",
    NOVA / "documents.json",
    NOVA / "documents-word-only.json",
    NOVA / "data" / "sources.json",
    NOVA / "document.html",
    NOVA / "README.md",
    NOVA / "DOCUMENT_CONTROL.md",
    NOVA / "SECURITY.md",
    NOVA / "METHODOLOGIE_BOUSSOLE.md",
]
active_public_files.extend(sorted((NOVA / "official" / "reference").glob("*.md")))
for p in active_public_files:
    if not p.is_file():
        errors.append(f"source publique active absente: {p.relative_to(NOVA)}")
        continue
    if version_re.search(p.read_text(encoding="utf-8", errors="replace")):
        errors.append(f"{p.relative_to(NOVA)}: numéro de version de chantier exposé dans une source publique active")

# Les anciens points d'entrée versionnés sont conservés par l'historique Git,
# mais ne doivent plus être servis par le site actif.
legacy_public_paths = [
    NOVA / "document-a1.html",
    NOVA / "STATUT_A1.md",
    NOVA / "data" / "a1-sources.json",
    NOVA / "official" / "a1",
]
for p in legacy_public_paths:
    if p.exists():
        errors.append(f"ancien chemin versionné encore servi: {p.relative_to(NOVA)}")

docjs = NOVA / "assets" / "documents.js"
if docjs.is_file():
    text = docjs.read_text(encoding="utf-8", errors="replace")
    for path in re.findall(r'"path"\s*:\s*"([^"]+)"', text):
        if not (NOVA / path).is_file():
            errors.append(f"assets/documents.js: fichier absent: {path}")

attr_re = re.compile(r'(?:href|src)=["\']([^"\'#]+)["\']', re.I)
for p in NOVA.glob("*.html"):
    text = p.read_text(encoding="utf-8", errors="replace")
    for raw in attr_re.findall(text):
        if raw.startswith(("http://", "https://", "mailto:", "tel:", "data:", "javascript:")):
            continue
        path = urlsplit(raw).path
        if not path or path.startswith("/"):
            continue
        target = (p.parent / path).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            errors.append(f"{p.name}: chemin sortant invalide: {raw}")
            continue
        if not target.exists():
            errors.append(f"{p.name}: cible locale absente: {raw}")

required_pages = {
    "index.html": "https://www.benoitcantin.com/projets/projet-nova/",
    "documents.html": "document.html?doc=corpus",
    "programme.html": "document.html?doc=programme",
    "constitution.html": "document.html?doc=corpus",
    "code-conduite.html": "document.html?doc=statuts",
    "registre-conformite.html": "document.html?doc=corpus",
    "finances.html": "document.html?doc=finances",
    "document.html": "data/sources.json",
}
for rel, needle in required_pages.items():
    f = NOVA / rel
    if not f.is_file():
        errors.append(f"page publique absente: {rel}")
        continue
    text = f.read_text(encoding="utf-8", errors="replace")
    if needle not in text:
        errors.append(f"{rel}: marqueur public absent: {needle}")

constitution = NOVA / "constitution.html"
if constitution.is_file() and "noindex" in constitution.read_text(encoding="utf-8", errors="replace").lower():
    errors.append("constitution.html: la page constitutionnelle publique ne doit pas être noindex")

for rel in ["SECURITY.md", "DOCUMENT_CONTROL.md"]:
    if not (NOVA / rel).is_file():
        errors.append(f"gouvernance documentaire absente: {rel}")

# Résilience Projet Nova : la 404 doit conserver le shell mobile accessible
# et la configuration locale ne doit plus pointer vers l'ancien univers.
nova_404 = NOVA / "404.html"
if not nova_404.is_file():
    errors.append("404.html: page de résilience absente")
else:
    html_404 = nova_404.read_text(encoding="utf-8", errors="replace")
    low_404 = html_404.lower()
    for marker in ("noindex", "nofollow", "noarchive"):
        if marker not in low_404:
            errors.append(f"404.html: robots incomplet, {marker} absent")
    for marker in (
        'aria-controls="navigation-principale"',
        'id="navigation-principale"',
        "data-menu-toggle",
        "data-main-nav",
    ):
        if marker not in html_404:
            errors.append(f"404.html: contrat menu mobile absent: {marker}")

nova_netlify = NOVA / "netlify.toml"
if not nova_netlify.is_file():
    errors.append("netlify.toml Projet Nova absent")
else:
    netlify_text = nova_netlify.read_text(encoding="utf-8", errors="replace")
    if "ere-des-consciences" in netlify_text:
        errors.append("netlify.toml Projet Nova: ancienne route ere-des-consciences encore présente")
    for marker in (
        '/projets/projet-nova/documents/*.pdf',
        'to = "/projets/sinjira/index.html"',
        'to = "/projets/sinjira/registre/index.html"',
    ):
        if marker not in netlify_text:
            errors.append(f"netlify.toml Projet Nova: contrat de déploiement absent: {marker}")

# Le manifeste PWA de Projet Nova doit rester borné à son sous-site.
pwa_manifest = NOVA / "site.webmanifest"
if not pwa_manifest.is_file():
    errors.append("site.webmanifest Projet Nova absent")
else:
    try:
        pwa = json.loads(pwa_manifest.read_text(encoding="utf-8"))
    except Exception as exc:
        pwa = {}
        errors.append(f"site.webmanifest Projet Nova invalide: {exc}")
    expected_nova_scope = "/projets/projet-nova/"
    for field in ("id", "start_url", "scope"):
        if pwa.get(field) != expected_nova_scope:
            errors.append(
                f"site.webmanifest Projet Nova: {field} doit valoir {expected_nova_scope}"
            )
    if pwa.get("lang") != "fr-CA":
        errors.append("site.webmanifest Projet Nova: lang doit être fr-CA")
    if pwa.get("display") not in {"standalone", "minimal-ui", "fullscreen"}:
        errors.append("site.webmanifest Projet Nova: display PWA invalide")

# Boussole électorale multidimensionnelle : structure, neutralité et transparence.
compass_visual = ROOT / "assets" / "media" / "nova-boussole-electorale-v2.webp"
if not compass_visual.is_file():
    errors.append("boussole électorale: visuel officiel absent: assets/media/nova-boussole-electorale-v2.webp")
else:
    compass_visual_bytes = compass_visual.read_bytes()
    git_blob_payload = b"blob " + str(len(compass_visual_bytes)).encode("ascii") + b"\0" + compass_visual_bytes
    expected_compass_visual_git_sha = "b4725fec0cccb1e0ec7df3797929ce105ea30c3a"
    actual_compass_visual_git_sha = hashlib.sha1(git_blob_payload).hexdigest()
    if actual_compass_visual_git_sha != expected_compass_visual_git_sha:
        errors.append("boussole électorale: le visuel officiel ne correspond pas au blob approuvé")

compass_page = NOVA / "boussole-electorale.html"
compass_data = NOVA / "data" / "boussole-electorale-v2.json"
party_corpus = NOVA / "data" / "boussole-partis-2026.json"
party_sources = NOVA / "data" / "boussole-sources-partis-2026.json"
evidence_matrix = NOVA / "data" / "boussole-preuves-2026.json"
compass_methodology = NOVA / "METHODOLOGIE_BOUSSOLE.md"
compass_js = NOVA / "assets" / "boussole-electorale.js"
compass_css = NOVA / "assets" / "boussole-electorale.css"

for required in (compass_page, compass_data, compass_js, compass_css, party_corpus, party_sources, evidence_matrix, compass_methodology):
    if not required.is_file():
        errors.append(f"boussole électorale: fichier absent: {required.relative_to(NOVA)}")

if compass_data.is_file():
    try:
        compass = json.loads(compass_data.read_text(encoding="utf-8"))
    except Exception as exc:
        compass = {}
        errors.append(f"boussole électorale: JSON invalide: {exc}")
    axes = compass.get("axes") or []
    questions = compass.get("questions") or []
    if len(axes) != 16:
        errors.append(f"boussole électorale: 16 dimensions requises, {len(axes)} trouvées")
    if len(questions) != 64:
        errors.append(f"boussole électorale: 64 questions requises, {len(questions)} trouvées")
    axis_ids = {axis.get("id") for axis in axes}
    for axis_id in axis_ids:
        axis_questions = [q for q in questions if q.get("axis") == axis_id]
        positive = sum(1 for q in axis_questions if q.get("direction") == 1)
        negative = sum(1 for q in axis_questions if q.get("direction") == -1)
        if len(axis_questions) != 4 or positive != 2 or negative != 2:
            errors.append(
                f"boussole électorale: axe {axis_id} doit avoir 4 questions, 2 par direction"
            )
    for q in questions:
        quality = q.get("quality") or {}
        for flag in (
            "singlePolicyDecision",
            "explicitActor",
            "neutralTone",
            "noPartyReference",
            "noIdeologicalLabel",
            "noPresumedMotive",
            "reviewedForDoubleBarrel",
            "reviewedForUndefinedQualifier",
        ):
            if quality.get(flag) is not True:
                errors.append(f"boussole électorale: {q.get('id')} sans validation de rédaction: {flag}")
        loadings = q.get("loadings") or []
        if not loadings:
            errors.append(f"boussole électorale: {q.get('id')} sans chargement dimensionnel")
        primary = [loading for loading in loadings if loading.get("axis") == q.get("axis")]
        if len(primary) != 1 or primary[0].get("weight") != 1:
            errors.append(f"boussole électorale: {q.get('id')} doit avoir un chargement principal de poids 1")
        for loading in loadings:
            if loading.get("axis") not in axis_ids:
                errors.append(f"boussole électorale: {q.get('id')} charge une dimension inconnue")
            weight = loading.get("weight")
            if not isinstance(weight, (int, float)) or weight <= 0 or weight > 1:
                errors.append(f"boussole électorale: poids invalide pour {q.get('id')}")
            if loading.get("axis") != q.get("axis") and weight > 0.4:
                errors.append(f"boussole électorale: chargement secondaire > 0.4 pour {q.get('id')}")
    unknown_axes = sorted({q.get("axis") for q in questions if q.get("axis") not in axis_ids})
    if unknown_axes:
        errors.append(f"boussole électorale: axes inconnus dans les questions: {unknown_axes}")
    if (compass.get("partyComparison") or {}).get("enabled") is not False:
        errors.append("boussole électorale: comparaison de partis doit rester désactivée sans corpus sourcé")
    if compass.get("jurisdiction") != "Québec":
        errors.append("boussole électorale: juridiction Québec requise")

if compass_page.is_file():
    compass_html = compass_page.read_text(encoding="utf-8", errors="replace")
    for marker in (
        "16 dimensions",
        "64 propositions",
        "64 questions, une à la fois",
        "ne vous dit pas pour qui voter",
        "Pourquoi cette boussole existe",
        "Comment ça fonctionne",
        "Votre résultat vous appartient",
        "Les 16 dimensions",
        "Voir précisément ce que la boussole mesure",
        "Ce que votre résultat permet de lire",
        "Questions fréquentes",
        'id="dimensions"',
        'id="lecture-resultat"',
        'id="faq-boussole"',
        'id="questionnaire"',
        'id="compass-results"',
        'id="partis"',
        'id="methodologie"',
        'id="etat-documentaire"',
        'id="compass-evidence-summary"',
        'id="compass-evidence-status"',
        'id="compass-evidence-question"',
        'id="compass-evidence-only-documented"',
        'id="compass-evidence-question-results"',
        'id="compass-evidence-parties"',
        "Le nombre de documents n’est pas un score politique",
        "Même règle pour tout le monde",
        "assets/boussole-electorale.js?v=3.3.0",
        "assets/boussole-electorale.css?v=3.6.0",
    ):
        if marker.lower() not in compass_html.lower():
            errors.append(f"boussole électorale: marqueur public absent: {marker}")

    for marker in (
        'id="compass-start-panel"',
        'id="compass-stepper"',
        'id="compass-prev"',
        'id="compass-next"',
        'id="compass-share-native"',
        'id="compass-email-recipient"',
        'id="compass-share-email"',
        'id="compass-share-facebook"',
        'id="compass-share-x"',
        'id="compass-share-linkedin"',
        'id="compass-copy-result"',
    ):
        if marker not in compass_html:
            errors.append(f"boussole électorale: parcours guidé ou partage absent: {marker}")
    if compass_html.count('href="boussole-electorale.html"') < 1:
        errors.append("boussole électorale: lien de retour vers la boussole absent de sa navigation")
    for marker in (
        '../../assets/media/nova-boussole-electorale-v2.webp',
        'compass-hero-grid',
        'class="compass-hero-visual"',
        '>Boussole électorale</a>',
        'https://www.benoitcantin.com/assets/media/nova-boussole-electorale-v2.webp',
        'meta property="og:image"',
        'meta name="twitter:image"',
    ):
        if marker not in compass_html:
            errors.append(f"boussole électorale: visuel officiel ou navigation explicite absent: {marker}")


    forbidden_compass_copy = (
        "Votre profil, plusieurs dimensions, aucune consigne de vote",
    )
    for forbidden in forbidden_compass_copy:
        if forbidden.lower() in compass_html.lower():
            errors.append(f"boussole électorale: texte public interdit encore présent: {forbidden}")
    if "<figcaption" in compass_html.lower():
        errors.append("boussole électorale: légende de visuel non désirée encore présente")
    if compass_html.count('class="compass-dimension-card"') != 16:
        errors.append("boussole électorale: les 16 dimensions doivent être visibles sur la page")

nova_runtime = NOVA / "script.js"
if nova_runtime.is_file():
    nova_runtime_text = nova_runtime.read_text(encoding="utf-8", errors="replace")
    for marker in (
        "['boussole-electorale.html','Boussole électorale']",
        "nav-link-boussole",
    ):
        if marker not in nova_runtime_text:
            errors.append(f"boussole électorale: menu runtime Nova incomplet: {marker}")
else:
    errors.append("boussole électorale: runtime Projet Nova absent: script.js")

if compass_js.is_file():
    compass_runtime = compass_js.read_text(encoding="utf-8", errors="replace")
    if 'const DATA_URL = "data/boussole-electorale-v2.json"' not in compass_runtime:
        errors.append("boussole électorale: dataset canonique non chargé")
    if 'PARTY_DATA_URL = "data/boussole-partis-2026.json"' not in compass_runtime:
        errors.append("boussole électorale: registre des partis non chargé")
    if 'PARTY_SOURCE_DATA_URL = "data/boussole-sources-partis-2026.json"' not in compass_runtime:
        errors.append("boussole électorale: inventaire des sources non chargé")
    if 'EVIDENCE_DATA_URL = "data/boussole-preuves-2026.json"' not in compass_runtime:
        errors.append("boussole électorale: matrice de preuves non chargée")
    if "fetch(" not in compass_runtime:
        errors.append("boussole électorale: chargement local du dataset absent")
    if re.search(r"https?://", compass_runtime):
        errors.append("boussole électorale: URL réseau externe interdite dans le moteur")
    if "localStorage" in compass_runtime or "sessionStorage" in compass_runtime:
        errors.append("boussole électorale: stockage navigateur persistant interdit en V2")

    for marker in (
        "currentIndex",
        "renderCurrentQuestion",
        "replaceChildren(renderQuestion",
        "Consulter mes résultats",
        "navigator.share",
        "copyText",
        "buildResultText",
        "compass-email-recipient",
        "mailto:",
    ):
        if marker not in compass_runtime:
            errors.append(f"boussole électorale: moteur guidé incomplet: {marker}")
    if "mount.appendChild(fieldset)" in compass_runtime:
        errors.append("boussole électorale: toutes les questions ne doivent plus être rendues simultanément")


if party_corpus.is_file():
    try:
        parties = json.loads(party_corpus.read_text(encoding="utf-8"))
    except Exception as exc:
        parties = {}
        errors.append(f"boussole électorale: corpus partis invalide: {exc}")
    party_rows = parties.get("parties") or []
    if len(party_rows) != 22:
        errors.append(f"boussole électorale: 22 entrées requises (20 autorisés + 1 retrait 2026 + Parti Nova), {len(party_rows)} trouvées")
    names = [row.get("name") for row in party_rows]
    if len(names) != len(set(names)):
        errors.append("boussole électorale: nom de parti dupliqué")
    authorized = [row for row in party_rows if row.get("entityType") == "authorized_provincial_party"]
    withdrawn = [row for row in party_rows if row.get("entityType") == "authorization_withdrawn_2026"]
    future = [row for row in party_rows if row.get("entityType") == "future_party_project"]
    if len(authorized) != 20:
        errors.append(f"boussole électorale: 20 partis provinciaux actuellement autorisés requis, {len(authorized)} trouvés")
    if len(withdrawn) != 1 or withdrawn[0].get("name") != "Parti populaire du Québec":
        errors.append("boussole électorale: le Parti populaire du Québec doit être conservé avec statut autorisation retirée en 2026")
    if len(future) != 1 or future[0].get("name") != "Parti Nova":
        errors.append("boussole électorale: Parti Nova doit être l’unique futur parti")
    if any(row.get("comparisonEligible") is not False for row in party_rows):
        errors.append("boussole électorale: aucune comparaison de parti ne doit être activée avant codage sourcé")
    neutrality = parties.get("neutralityRules") or {}
    for key in (
        "equalQuestionSetForEveryParty",
        "equalPresentationRulesForEveryParty",
        "equalCoverageThresholdForEveryParty",
        "equalSourcePriorityForEveryParty",
        "noHostPartyBonus",
        "noManualResultBoost",
        "alphabeticalDisplayDefault",
        "noFeaturedParty",
        "noLogoSizePreference",
        "tiesRemainTies",
        "unknownPositionsRemainUnknown",
    ):
        if neutrality.get(key) is not True:
            errors.append(f"boussole électorale: règle de neutralité absente ou fausse: {key}")

    presentation = parties.get("presentationRules") or {}
    if presentation.get("mode") != "factual_side_by_side":
        errors.append("boussole électorale: mode de présentation factuelle requis")
    for key in (
        "noAutomaticRanking",
        "noWinnerLabel",
        "noRecommendedParty",
        "noBestMatchBadge",
        "evidenceVisiblePerQuestion",
        "unknownVisible",
        "contradictoryVisible",
        "alphabeticalDefault",
        "allPartiesVisibleRegardlessOfCoverage",
    ):
        if presentation.get(key) is not True:
            errors.append(f"boussole électorale: règle de présentation factuelle absente ou fausse: {key}")
    for row in party_rows:
        if row.get("comparisonEligible") is not False:
            errors.append(f"boussole électorale: comparaison prématurément activée pour {row.get('name')}")
        if row.get("coverage") != 0:
            errors.append(f"boussole électorale: couverture initiale non nulle pour {row.get('name')}")
        if row.get("positions") != {}:
            errors.append(f"boussole électorale: positions non sourcées présentes pour {row.get('name')}")
    rules = parties.get("activationRules") or {}
    if rules.get("minimumIndependentCoders") != 2:
        errors.append("boussole électorale: double codage indépendant requis")
    if rules.get("allPartiesVisibleRegardlessOfCoverage") is not True:
        errors.append("boussole électorale: tous les partis doivent rester visibles quelle que soit la couverture")
    if rules.get("noOverallPartyScore") is not True:
        errors.append("boussole électorale: aucun score global de parti ne doit être produit")


    forbidden_party_runtime_tokens = [row.get("name") for row in party_rows if row.get("name")]
    forbidden_party_runtime_tokens += [row.get("id") for row in party_rows if row.get("id")]
    for token in forbidden_party_runtime_tokens:
        if token in compass_runtime:
            errors.append(f"boussole électorale: moteur runtime ne doit contenir aucun traitement spécifique à {token}")
    for token in ("partyBoost", "partyBonus", "featuredParty", "preferredParty", "incumbencyWeight", "pollingWeight"):
        if token in compass_runtime:
            errors.append(f"boussole électorale: mécanisme de favoritisme interdit dans le moteur: {token}")
    for marker in (
        "renderDocumentaryStatus",
        "renderEvidenceExplorer",
        "loadPoliticalRegistryAndEvidence",
        "Preuves candidates",
        "Deuxième révision terminée",
        "Positions finalisées",
        "Questions recherchées",
        "Justification du codage",
        "Consulter la source officielle",
        "Non documentée",
        "Cela ne signifie ni appui, ni opposition, ni neutralité",
        "researchCoverage",
        "secondIndependentReview",
        "Aucun de ces nombres ne modifie le poids d’un parti",
    ):
        if marker not in compass_runtime:
            errors.append(f"boussole électorale: transparence documentaire runtime absente: {marker}")
    if compass_runtime.count("localeCompare(String(b.name)") < 2:
        errors.append("boussole électorale: registre et état documentaire doivent tous deux rester triés alphabétiquement")
    if 'localeCompare(String(b.name), "fr-CA")' not in compass_runtime:
        errors.append("boussole électorale: tri alphabétique neutre des partis absent")


if party_sources.is_file():
    try:
        source_inventory = json.loads(party_sources.read_text(encoding="utf-8"))
    except Exception as exc:
        source_inventory = {}
        errors.append(f"boussole électorale: inventaire de sources invalide: {exc}")
    source_rows = source_inventory.get("parties") or []
    corpus_ids = {row.get("id") for row in party_rows}
    source_ids = {row.get("id") for row in source_rows}
    if len(source_rows) != 22:
        errors.append(f"boussole électorale: inventaire de sources doit contenir 22 entrées, {len(source_rows)} trouvées")
    if source_ids != corpus_ids:
        errors.append("boussole électorale: inventaire de sources désaligné avec le registre des partis")
    source_rules = source_inventory.get("equalityRules") or {}
    for key in (
        "sameSourceFieldsForEveryParty",
        "registrySourceRequiredForAuthorizedParties",
        "missingOfficialSiteDoesNotCreatePoliticalPosition",
        "documentationVolumeDoesNotIncreaseSimilarity",
        "sourceCountDoesNotIncreaseWeight",
        "sourceQualityAffectsConfidenceOnly",
        "futurePartyUsesSameEvidenceFields",
    ):
        if source_rules.get(key) is not True:
            errors.append(f"boussole électorale: règle d’égalité documentaire absente ou fausse: {key}")
    required_source_fields = {
        "id", "name", "entityType", "registryUrl", "officialSite", "platformUrls",
        "pressReleaseUrls", "legislativeRecordUrls", "verificationStatus",
        "lastVerified", "usableForPositionCoding", "notes"
    }
    for row in source_rows:
        if set(row.keys()) != required_source_fields:
            errors.append(f"boussole électorale: champs de sources non uniformes pour {row.get('name')}")
        if row.get("entityType") in {"authorized_provincial_party", "authorization_withdrawn_2026"} and not row.get("registryUrl"):
            errors.append(f"boussole électorale: registre Élections Québec absent pour {row.get('name')}")
        if row.get("officialSite") is None and row.get("usableForPositionCoding") is True:
            errors.append(f"boussole électorale: codage interdit sans site/source officielle vérifiée pour {row.get('name')}")
        if not isinstance(row.get("platformUrls"), list):
            errors.append(f"boussole électorale: platformUrls doit être une liste pour {row.get('name')}")


if evidence_matrix.is_file():
    try:
        evidence = json.loads(evidence_matrix.read_text(encoding="utf-8"))
    except Exception as exc:
        evidence = {}
        errors.append(f"boussole électorale: matrice de preuves invalide: {exc}")
    matrix_party_ids = evidence.get("partyIds") or []
    matrix_questions = evidence.get("questions") or []
    allowed_statuses = set(evidence.get("statusValues") or [])
    if len(matrix_party_ids) != 22 or set(matrix_party_ids) != {row.get("id") for row in party_rows}:
        errors.append("boussole électorale: matrice de preuves doit couvrir exactement les 22 formations")
    if len(matrix_questions) != 64:
        errors.append(f"boussole électorale: matrice de preuves doit couvrir 64 questions, {len(matrix_questions)} trouvées")
    expected_question_ids = {q.get("id") for q in questions}
    if {row.get("questionId") for row in matrix_questions} != expected_question_ids:
        errors.append("boussole électorale: matrice de preuves désalignée avec les 64 questions")
    for row in matrix_questions:
        statuses = row.get("statuses") or {}
        if set(statuses.keys()) != set(matrix_party_ids):
            errors.append(f"boussole électorale: {row.get('questionId')} ne couvre pas toutes les formations")
        for party_id, status in statuses.items():
            if status not in allowed_statuses:
                errors.append(f"boussole électorale: statut de preuve invalide {status} pour {row.get('questionId')} / {party_id}")
    rules = evidence.get("evidenceRules") or {}
    for key in (
        "officialSourcesPreferred",
        "exactQuestionMatchRequired",
        "noIdeologicalInference",
        "noPartyNameInference",
        "noMissingSourceInference",
        "sameEvidenceStandardForEveryParty",
        "sourceVolumeDoesNotIncreaseWeight",
        "contradictoryEvidencePreserved",
        "secondIndependentReviewRequiredBeforeFinalization",
    ):
        if rules.get(key) is not True:
            errors.append(f"boussole électorale: règle de preuve absente ou fausse: {key}")
    forbidden_keys = {"score", "rank", "ranking", "winner", "recommendedParty", "bestParty"}
    def walk_keys(value):
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in forbidden_keys:
                    errors.append(f"boussole électorale: champ de classement politique interdit dans la matrice: {key}")
                walk_keys(nested)
        elif isinstance(value, list):
            for nested in value:
                walk_keys(nested)
    walk_keys(evidence)
    records = evidence.get("evidenceRecords") or []
    record_ids = [r.get("recordId") for r in records]
    if len(record_ids) != len(set(record_ids)):
        errors.append("boussole électorale: identifiant de preuve dupliqué")
    allowed_confidence = set(evidence.get("confidenceValues") or [])
    required_record_fields = {
        "recordId", "questionId", "partyId", "proposedStatus", "sourceUrl",
        "sourceTitle", "sourceDate", "checkedAt", "sourceType", "evidenceSummary",
        "rationale", "confidence", "firstReview", "secondIndependentReview", "finalizable"
    }
    for record in records:
        if set(record.keys()) != required_record_fields:
            errors.append(f"boussole électorale: schéma de preuve incomplet pour {record.get('recordId')}")
        if record.get("questionId") not in expected_question_ids:
            errors.append(f"boussole électorale: preuve liée à une question inconnue: {record.get('recordId')}")
        if record.get("partyId") not in set(matrix_party_ids):
            errors.append(f"boussole électorale: preuve liée à une formation inconnue: {record.get('recordId')}")
        if record.get("proposedStatus") not in allowed_statuses - {"unknown"}:
            errors.append(f"boussole électorale: statut candidat invalide: {record.get('recordId')}")
        if record.get("confidence") not in allowed_confidence - {"none"}:
            errors.append(f"boussole électorale: confiance candidate invalide: {record.get('recordId')}")
        if not str(record.get("sourceUrl") or "").startswith("https://"):
            errors.append(f"boussole électorale: URL HTTPS de preuve requise: {record.get('recordId')}")
        if record.get("checkedAt") != "2026-10-06":
            errors.append(f"boussole électorale: date de vérification inattendue: {record.get('recordId')}")
        if (record.get("firstReview") or {}).get("status") != "completed":
            errors.append(f"boussole électorale: première révision absente: {record.get('recordId')}")
        second = record.get("secondIndependentReview") or {}
        if second.get("status") == "pending":
            if record.get("finalizable") is not False:
                errors.append(f"boussole électorale: preuve en attente de seconde révision ne peut pas être finalisable: {record.get('recordId')}")
        elif second.get("status") == "completed":
            if not second.get("reviewer") or not second.get("reviewedAt"):
                errors.append(f"boussole électorale: seconde révision complétée sans identité/date: {record.get('recordId')}")
        else:
            errors.append(f"boussole électorale: statut de seconde révision invalide: {record.get('recordId')}")

    record_by_id = {r.get("recordId"): r for r in records}
    research_batches = evidence.get("researchCoverage") or []
    batch_ids = [batch.get("batchId") for batch in research_batches]
    if len(batch_ids) != len(set(batch_ids)):
        errors.append("boussole électorale: identifiant de lot de recherche dupliqué")
    referenced_record_ids = set()
    question_batch_membership = {question_id: [] for question_id in expected_question_ids}
    required_batch_fields = {
        "batchId", "checkedAt", "questionIds", "partyIds", "scope", "sourcePolicy",
        "candidateCountByQuestion", "note", "evidenceRecordIds"
    }
    allowed_optional_batch_fields = {"finalizedCountByQuestion"}
    for batch in research_batches:
        batch_id = batch.get("batchId")
        keys = set(batch.keys())
        if not required_batch_fields.issubset(keys) or not keys.issubset(required_batch_fields | allowed_optional_batch_fields):
            errors.append(f"boussole électorale: schéma de lot de recherche invalide pour {batch_id}")
        question_ids = batch.get("questionIds") or []
        party_ids = batch.get("partyIds") or []
        evidence_record_ids = batch.get("evidenceRecordIds") or []
        counts = batch.get("candidateCountByQuestion") or {}
        if batch.get("checkedAt") != "2026-10-06":
            errors.append(f"boussole électorale: date de lot de recherche inattendue pour {batch_id}")
        if not question_ids or len(question_ids) != len(set(question_ids)) or not set(question_ids).issubset(expected_question_ids):
            errors.append(f"boussole électorale: questions invalides dans le lot {batch_id}")
        for question_id in question_ids:
            if question_id in question_batch_membership:
                question_batch_membership[question_id].append(batch_id)
        if set(party_ids) != set(matrix_party_ids) or len(party_ids) != len(matrix_party_ids):
            errors.append(f"boussole électorale: le lot {batch_id} ne couvre pas exactement les 22 formations")
        if set(counts.keys()) != set(question_ids):
            errors.append(f"boussole électorale: comptes candidats désalignés dans le lot {batch_id}")
        if len(evidence_record_ids) != len(set(evidence_record_ids)):
            errors.append(f"boussole électorale: preuve répétée dans le lot {batch_id}")
        for record_id in evidence_record_ids:
            if record_id in referenced_record_ids:
                errors.append(f"boussole électorale: preuve liée à plusieurs lots de recherche: {record_id}")
            referenced_record_ids.add(record_id)
            record = record_by_id.get(record_id)
            if record is None:
                errors.append(f"boussole électorale: preuve de lot introuvable: {record_id}")
                continue
            if record.get("questionId") not in set(question_ids):
                errors.append(f"boussole électorale: preuve hors questions du lot {batch_id}: {record_id}")
            if record.get("partyId") not in set(party_ids):
                errors.append(f"boussole électorale: preuve hors formations du lot {batch_id}: {record_id}")
        for question_id in question_ids:
            expected_count = counts.get(question_id)
            actual_count = sum(
                1 for record_id in evidence_record_ids
                if (record_by_id.get(record_id) or {}).get("questionId") == question_id
            )
            if not isinstance(expected_count, int) or expected_count < 0 or actual_count != expected_count:
                errors.append(
                    f"boussole électorale: compte candidat incohérent dans {batch_id} / {question_id}: "
                    f"{actual_count} preuves liées pour {expected_count} annoncées"
                )
        finalized_counts = batch.get("finalizedCountByQuestion")
        if finalized_counts is not None:
            if set(finalized_counts.keys()) != set(question_ids):
                errors.append(f"boussole électorale: comptes finalisés désalignés dans le lot {batch_id}")
            for question_id in question_ids:
                expected_finalized = finalized_counts.get(question_id)
                actual_finalized = sum(
                    1 for record_id in evidence_record_ids
                    if (record_by_id.get(record_id) or {}).get("questionId") == question_id
                    and (record_by_id.get(record_id) or {}).get("finalizable") is True
                    and ((record_by_id.get(record_id) or {}).get("secondIndependentReview") or {}).get("status") == "completed"
                )
                if not isinstance(expected_finalized, int) or expected_finalized < 0 or actual_finalized != expected_finalized:
                    errors.append(
                        f"boussole électorale: compte finalisé incohérent dans {batch_id} / {question_id}: "
                        f"{actual_finalized} preuves finalisées pour {expected_finalized} annoncées"
                    )

    for question_id, memberships in question_batch_membership.items():
        if len(memberships) == 0:
            errors.append(f"boussole électorale: question sans lot de recherche: {question_id}")
        elif len(memberships) > 1:
            errors.append(
                f"boussole électorale: question présente dans plusieurs lots de recherche: "
                f"{question_id} ({', '.join(memberships)})"
            )
    unbatched_record_ids = set(record_by_id) - referenced_record_ids
    if unbatched_record_ids:
        errors.append(
            "boussole électorale: preuves non rattachées à un lot de recherche: "
            + ", ".join(sorted(unbatched_record_ids))
        )

    finalized_records = {
        (r.get("questionId"), r.get("partyId")): r
        for r in records
        if (r.get("secondIndependentReview") or {}).get("status") == "completed"
        and r.get("finalizable") is True
    }
    matrix_status_by_key = {}
    for row in matrix_questions:
        question_id = row.get("questionId")
        for party_id, status in (row.get("statuses") or {}).items():
            key = (question_id, party_id)
            matrix_status_by_key[key] = status
            if status != "unknown":
                record = finalized_records.get(key)
                if record is None:
                    errors.append(f"boussole électorale: statut documenté sans fiche de preuve finalisée pour {question_id} / {party_id}")
                elif status != record.get("proposedStatus"):
                    errors.append(f"boussole électorale: statut de matrice différent de la preuve finalisée pour {question_id} / {party_id}")
    for key, record in finalized_records.items():
        if matrix_status_by_key.get(key) != record.get("proposedStatus"):
            errors.append(f"boussole électorale: preuve finalisée non répercutée dans la matrice pour {key[0]} / {key[1]}")

if compass_methodology.is_file():
    method_text = compass_methodology.read_text(encoding="utf-8", errors="replace")
    for marker in ("Vote Compass", "Smartvote", "Élections Québec", "deux codages indépendants", "Rédaction non ambiguë", "Couverture des partis", "Parti Nova", "Matrice factuelle de preuves", "aucun classement automatique"):
        if marker.lower() not in method_text.lower():
            errors.append(f"boussole électorale: méthodologie incomplète: {marker}")

for sitemap_rel in ("sitemap.xml",):
    sitemap_text = (NOVA / sitemap_rel).read_text(encoding="utf-8", errors="replace")
    if "boussole-electorale.html" not in sitemap_text:
        errors.append("boussole électorale: absente du sitemap Projet Nova")


nova_home = NOVA / "index.html"
if nova_home.is_file():
    nova_home_html = nova_home.read_text(encoding="utf-8", errors="replace")
    if nova_home_html.count('href="boussole-electorale.html"') < 3:
        errors.append("boussole électorale: l’accueil Nova doit offrir au moins trois accès visibles vers la boussole")
    for marker in (
        "Faire la boussole",
        ">Boussole électorale</a>",
        "64 questions, une à la fois",
        'class="nova-compass-entry"',
        'class="nova-compass-entry-link"',
        'class="nav-link nav-link-boussole"',
        'class="hero-side-link-boussole"',
        '../../assets/media/nova-boussole-electorale-v2.webp',
    ):
        if marker not in nova_home_html:
            errors.append(f"boussole électorale: accès accueil incomplet: {marker}")

if compass_page.is_file() and (NOVA / "index.html").is_file():
    if "boussole-electorale.html" not in (NOVA / "index.html").read_text(encoding="utf-8", errors="replace"):
        errors.append("boussole électorale: lien absent de l’accueil Projet Nova")

if errors:
    print("PROJET NOVA — FAIL")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("PROJET NOVA — PASS")