#!/usr/bin/env python3
"""Preuve hors ligne : ne jamais inventer les achats ou le rôle du membre.

Ce test vérifie le contrat du frontend uniquement. Les autorisations
réelles restent imposées côté Supabase/RLS et par les fonctions privées.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Structure(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.summary = 0
        self.live = 0
        self.counter_names: list[str] = []
        self.routes: set[str] = set()
        self.numbers: list[str] = []
        self.reading_summary = False
        self.summary_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "span" and "data-library-summary" in data:
            self.summary += 1
            self.live += int(data.get("aria-live") == "polite")
            self.reading_summary = True
        if tag == "strong":
            for name in ("project", "read", "entitlement", "request"):
                key = "data-library-" + name + "-count"
                if key in data:
                    self.counter_names.append(key)
                    self.numbers.append(data.get("aria-label") or "")
        if tag == "a" and data.get("href", "").startswith("/projets/sinjira/"):
            self.routes.add(data["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "span":
            self.reading_summary = False

    def handle_data(self, data: str) -> None:
        if self.reading_summary:
            self.summary_text += data


def audit(html: str, js: str) -> list[str]:
    structure = Structure()
    structure.feed(html)
    errors: list[str] = []
    if structure.summary != 1 or structure.live != 1:
        errors.append("Région de statut aria-live manquante ou dupliquée")
    if "Vérification de vos accès et droits numériques en cours" not in structure.summary_text:
        errors.append("Aucun état initial neutre de vérification")
    if "Aucun achat ou service payant n’est activé actuellement" in html:
        errors.append("Fausse affirmation d'absence d'achat avant authentification")
    if len(set(structure.counter_names)) != 4 or len(structure.counter_names) != 4:
        errors.append("Statistiques des quatre ressources incomplètes")
    if len(structure.numbers) != 4 or any(v != "En cours de vérification" for v in structure.numbers):
        errors.append("Zéro droits avant réponse API non autorisé")
    for category in ("romans", "jeux", "logiciels"):
        if f"/projets/sinjira/{category}/" not in structure.routes:
            errors.append("Raccourci de catégorie manquant: " + category)
    expectations = (
        "const isOwner=!ownerResult.error&&ownerResult.data===true;",
        "const isAdmin=!adminResult.error&&adminResult.data===true;",
        "const rolesVerified=!ownerResult.error&&!adminResult.error;",
        "function activeProjectAccess(accessRows,now=Date.now())",
        "['player','tester'].includes(row.access_level)",
        "s.rpc('is_sinjira_owner',{p_user_id:user.id})",
        "function canOpenProject(project,activeAccess,isOwner,isAdmin)",
        "function safeProjectPlayPath(value)",
        "return safeLibraryRoute(value);",
        "const demoPath=safeLibraryRoute(novel.demo_path);",
        'data-v2461-request-tester="${escapeHtml(project.id)}"',
        "return safeLibraryCover(project.cover_url,fallback);",
        "Number.isFinite(rawProgress)",
        "Math.round(Math.max(0,Math.min(100,rawProgress)))",
        "Number.isSafeInteger(rawPage)&&rawPage>0",
        "const publicPath=safeLibraryRoute(novel.public_path)||'/projets/sinjira/romans/';",
        "projectsResult.error||accessResult.error||!rolesVerified?'—':availableProjects.length",
        "if(value==='—')node.setAttribute('aria-label','Information momentanément indisponible');",
        "else node.removeAttribute('aria-label');",
        "isAvailable?`<a class=",
        "const entitlementsVerified=!entitlementsResult.error;",
        "entitlementsVerified?entitlements.length:'—'",
        "if(!entitlementsVerified){",
        "Vérification temporairement indisponible",
        "renderEntitlements(entitlements,isOwner,entitlementsVerified)",
        "Aucun droit numérique explicite confirmé pour ce compte.",
        "Certains droits ne peuvent pas être vérifiés pour le moment.",
        "getSupabase().functions.invoke('get-novel-file-url'",
        "const errors=[adminResult,ownerResult,projectsResult",
    )
    for marker in expectations:
        if marker not in js:
            errors.append("Contrat de droits incomplet: " + marker[:60])
    if "data-open-full-novel" in html:
        errors.append("Bouton de roman intégral avant droits vérifiés")
    return errors


def audit_commerce(purchases: str, licenses: str) -> list[str]:
    problems: list[str] = []
    if "Aucun achat payant associé pour le moment" in purchases:
        problems.append("Achats : fausse absence de paiement affirmée avant vérification")
    if "Cette section ne consulte pas actuellement d'historique de paiements" not in purchases:
        problems.append("Achats : limite du suivi des paiements non expliquée")
    if 'href="/compte/bibliotheque.html"' not in purchases:
        problems.append("Achats : lien vers les droits numériques vérifiés absent")
    if "Licences SINJIRA™ — mode gratuit" in licenses:
        problems.append("Licences : statut gratuit généralisé sans base")
    if "codes et droits numériques du compte" not in licenses:
        problems.append("Licences : distinction code et droits absente")
    return problems


def audit_legacy(js: str) -> list[str]:
    problems: list[str] = []
    required = (
        "verifiedProjectAccess(grants,now=Date.now())",
        "['player','tester'].includes(g.access_level)",
        "function projectIsOpen(project,access,isOwner=owner,isAdmin=admin)",
        "const accessMap=verifiedProjectAccess(accessError?[]:access);",
        "if(!allowed){",
        "Documents sur autorisation. Aucun accès privé confirmé.",
        "Playtests non accessibles sans droit confirmé.",
        "s.rpc('is_sinjira_owner',{p_user_id:user.id})",
        "s.rpc('is_sinjira_admin',{p_user_id:user.id})",
        "owner=!ow.error&&ow.data===true;",
        "admin=!ad.error&&ad.data===true;",
        "const playPath=allowed?internalProjectPath(p.play_path):'';",
        "return safeLibraryRoute(raw);",
        "return safeLibraryCover(p.cover_url,fallback);",
        'data-request-tester="${escapeHtml(p.id)}"',
        'data-open-document="${escapeHtml(d.id)}"',
        'id="${escapeHtml(x.id)}"',
        'data-apply-playtest="${escapeHtml(x.id)}"',
    )
    for marker in required:
        if marker not in js:
            problems.append("Détail projet historique : garde absent " + marker[:55])
    if js.count('data-open-document="${escapeHtml(d.id)}"') != 2:
        problems.append("Boutons des documents : les deux attributs id doivent être échappés")
    if "owner=isSinjiraOwner(user)" in js:
        problems.append("Ancienne déduction propriétaire depuis e-mail interdite")
    return problems


def audit_routes(shared: str) -> list[str]:
    """Ne jamais remplacer le contrôle de liens du registre par escapeHtml."""
    required = (
        "export function safeLibraryRoute(value){",
        "typeof value!=='string'||!value||value!==value.trim()",
        "!value.startsWith('/')||value.startsWith('//')",
        "if(/%(?![0-9a-f]{2})/i.test(value))return '';",
        "/%(?:2f|5c|2e|0[0-9a-f]|1[0-9a-f]|7f)/i.test(value)",
        "url.origin!==location.origin",
        "url.pathname!==pathname",
        "if(pathname.includes('%'))return '';",
        "supabase|scripts|tests|docs|mobile-native|node_modules|_site",
        "(?:codex|",
        "netlify",
        "security",
        "upload_github",
        "tsx?|jsx?|sh|env|lock",
        "export function safeLibraryCover(value,fallback=",
        "const safe=safeLibraryRoute(value);",
        "safe.startsWith('/assets/media/')",
        "!/[?#]/.test(safe)",
        "webp|png|jpe?g|avif",
    )
    return ["Navigation locale non canonique : " + key
            for key in required if key not in shared]


def self_test() -> None:
    html = (ROOT / "compte/bibliotheque.html").read_text("utf-8")
    js = (ROOT / "assets/js/sinjira-library-v24-4-61.js").read_text("utf-8")
    assert not audit(html, js), audit(html, js)
    legacy = (ROOT / "assets/js/sinjira-library.js").read_text("utf-8")
    assert not audit_legacy(legacy), audit_legacy(legacy)
    shared = (ROOT / "assets/js/sinjira-supabase.js").read_text("utf-8")
    assert not audit_routes(shared), audit_routes(shared)
    for broken in (
        shared.replace("url.pathname!==pathname", "false"),
        shared.replace("if(pathname.includes('%'))return '';", ""),
        shared.replace("!value.startsWith('/')||value.startsWith('//')", "false"),
        shared.replace("supabase|scripts|tests|docs|mobile-native|node_modules|_site",
                       "other-unused-directory"),
        shared.replace("(?:codex|", "(?:not-codex|"),
        shared.replace("tsx?|jsx?|sh|env|lock", "not-source-code"),
        shared.replace("safe.startsWith('/assets/media/')", "true"),
        shared.replace("!/[?#]/.test(safe)", "true"),
        shared.replace("webp|png|jpe?g|avif", "svg|html|js"),
    ):
        assert audit_routes(broken), "URL non canonique non détectée"
    purchases = (ROOT / "compte/mes-achats.html").read_text("utf-8")
    licenses = (ROOT / "compte/licences.html").read_text("utf-8")
    assert not audit_commerce(purchases, licenses), audit_commerce(purchases, licenses)
    for broken in (
        purchases.replace(
            "Historique des paiements en ligne",
            "Aucun achat payant associé pour le moment"
        ),
        purchases.replace('href="/compte/bibliotheque.html"',
                          'href="/compte/page-inexistante.html"'),
    ):
        assert audit_commerce(broken, licenses), "Régression Achats acceptée"
    assert audit_commerce(purchases, licenses.replace(
        "codes et droits numériques du compte", "mode gratuit"
    )), "Régression Licences acceptée"
    for broken in (
        html.replace("Vérification de vos accès et droits numériques en cours…",
                     "Aucun achat ou service payant n’est activé actuellement."),
        html.replace('data-library-summary aria-live="polite"',
                     'data-library-summary'),
        html.replace('/projets/sinjira/logiciels/', '/projets/sinjira/faux/'),
    ):
        assert audit(broken, js), "Texte ou raccourci trompeur accepté"
    for broken in (
        legacy.replace("owner=!ow.error&&ow.data===true;", "owner=true;"),
        legacy.replace("if(!allowed){", "if(false){"),
        legacy.replace("return safeLibraryRoute(raw);", "return String(raw||'');"),
        legacy.replace("return safeLibraryCover(p.cover_url,fallback);",
                       "return p.cover_url||fallback;"),
        legacy.replace('data-request-tester="${escapeHtml(p.id)}"',
                       'data-request-tester="${p.id}"'),
        legacy.replace('data-open-document="${escapeHtml(d.id)}"',
                       'data-open-document="${d.id}"', 1),
        legacy.replace('id="${escapeHtml(x.id)}"',
                       'id="${x.id}"'),
        legacy.replace('data-apply-playtest="${escapeHtml(x.id)}"',
                       'data-apply-playtest="${x.id}"'),
    ):
        assert audit_legacy(broken), "Contournement droits du détail de projet accepté"
    for broken in (
        js.replace("const entitlementsVerified=!entitlementsResult.error;",
                   "const entitlementsVerified=true;"),
        js.replace("const isOwner=!ownerResult.error&&ownerResult.data===true;",
                   "const isOwner=true;"),
        js.replace("if(!entitlementsVerified){", "if(false){"),
        js.replace("const demoPath=safeLibraryRoute(novel.demo_path);",
                   "const demoPath=novel.demo_path;"),
        js.replace("return safeLibraryCover(project.cover_url,fallback);",
                   "return project.cover_url||fallback;"),
        js.replace('data-v2461-request-tester="${escapeHtml(project.id)}"',
                   'data-v2461-request-tester="${project.id}"'),
        js.replace("Number.isFinite(rawProgress)", "true"),
        js.replace("Number.isSafeInteger(rawPage)&&rawPage>0", "true"),
    ):
        assert audit(html, broken), "Droits accordés sans vérification acceptés"
    print("OK bibliothèque : chargement neutre et erreurs de droits non assimilées à zéro")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    html = (ROOT / "compte/bibliotheque.html").read_text("utf-8")
    js = (ROOT / "assets/js/sinjira-library-v24-4-61.js").read_text("utf-8")
    errors = audit(html, js)
    errors.extend(audit_legacy((ROOT / "assets/js/sinjira-library.js").read_text("utf-8")))
    errors.extend(audit_routes(
        (ROOT / "assets/js/sinjira-supabase.js").read_text("utf-8")
    ))
    errors.extend(audit_commerce(
        (ROOT / "compte/mes-achats.html").read_text("utf-8"),
        (ROOT / "compte/licences.html").read_text("utf-8")
    ))
    for error in errors:
        print("ERREUR : " + error)
    if errors:
        return 1
    print("OK : les droits de bibliothèque sont présentés sans supposition")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
