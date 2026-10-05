#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re

from validate_site import (
    LEGACY_PERSONAL_FORMSPREE_ENDPOINT,
    NOVA_FORMSPREE_ENDPOINT,
    PERSONAL_CONTACT_ACTIVE_GOVERNANCE_COPY,
    PERSONAL_CONTACT_ACTIVE_HERO,
    PERSONAL_CONTACT_ACTIVE_META,
    PERSONAL_CONTACT_ACTIVE_SECURITY,
    PERSONAL_CONTACT_ACTIVE_STATE,
    PERSONAL_CONTACT_PENDING_GOVERNANCE_COPY,
    PERSONAL_CONTACT_PENDING_HERO,
    PERSONAL_CONTACT_PENDING_META,
    PERSONAL_CONTACT_PENDING_SECURITY,
    PERSONAL_CONTACT_PENDING_STATE,
    validate_personal_contact_contract,
)

ROOT = Path(__file__).resolve().parents[1]
CONTACT = ROOT / "contact.html"
PRIVACY = ROOT / "confidentialite.html"
GOVERNANCE = ROOT / "gouvernance-vie-privee.html"
ENDPOINT_RE = re.compile(r"https://formspree\.io/f/[A-Za-z0-9_-]+")

CONTACT_REPLACEMENTS = (
    (
        "Pendant la configuration de ce nouvel endpoint personnel, le formulaire reste volontairement désactivé afin qu’aucun message ne soit envoyé vers le mauvais canal.",
        "Le formulaire personnel utilise un endpoint Formspree distinct de Projet Nova, configuré et vérifié.",
    ),
    (
        "Lorsque le formulaire personnel sera réactivé, il utilisera <strong>Formspree</strong> avec un endpoint distinct de Projet Nova;",
        "Le formulaire personnel utilise <strong>Formspree</strong> avec un endpoint distinct de Projet Nova configuré et vérifié;",
    ),
    (
        "Aucune soumission personnelle n’est envoyée à Formspree tant que le nouvel endpoint distinct n’est pas configuré.",
        "Les soumissions personnelles sont envoyées uniquement au canal Formspree personnel distinct de Projet Nova.",
    ),
)

PRIVACY_PENDING = (
    "<strong>Le formulaire personnel du portail est actuellement désactivé</strong> "
    "et n’envoie aucune donnée à Formspree tant qu’un nouvel endpoint personnel distinct "
    "de Projet Nova n’est pas configuré et vérifié."
)
PRIVACY_ACTIVE = (
    "<strong>Le formulaire personnel du portail utilise un endpoint Formspree distinct de Projet Nova "
    "configuré et vérifié</strong>. Les données soumises par ce formulaire sont transmises à Formspree "
    "pour acheminer la demande au canal personnel de Benoit Cantin."
)
RUNTIME_GATE = (
    "function endpointReady(){return "
    "form.getAttribute('data-personal-formspree-state')==='active-separate-endpoint'&&"
    "/^https:\\/\\/formspree\\.io\\/f\\/[A-Za-z0-9_-]+$/.test(PERSONAL_ENDPOINT)}"
)


def validate_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    if not ENDPOINT_RE.fullmatch(endpoint):
        raise ValueError("Endpoint Formspree invalide: https://formspree.io/f/<identifiant> requis.")
    if endpoint in {LEGACY_PERSONAL_FORMSPREE_ENDPOINT, NOVA_FORMSPREE_ENDPOINT}:
        raise ValueError("Endpoint refusé: le canal personnel doit être distinct de l’ancien endpoint et de Projet Nova.")
    return endpoint


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: occurrence attendue=1, observée={count}.")
    return text.replace(old, new, 1)


def replace_exact_count(text: str, old: str, new: str, count: int, label: str) -> str:
    observed = text.count(old)
    if observed != count:
        raise ValueError(f"{label}: occurrence attendue={count}, observée={observed}.")
    return text.replace(old, new)


def build_active_contents(
    contact_text: str,
    privacy_text: str,
    governance_text: str,
    endpoint: str,
) -> tuple[str, str, str]:
    endpoint = validate_endpoint(endpoint)

    current_errors = validate_personal_contact_contract(contact_text, privacy_text, governance_text)
    if current_errors:
        raise ValueError("État courant du contact personnel invalide: " + " | ".join(current_errors))
    if f'data-personal-formspree-state="{PERSONAL_CONTACT_PENDING_STATE}"' not in contact_text:
        raise ValueError("Activation refusée: le formulaire personnel n’est pas dans l’état pending attendu.")
    if "var PERSONAL_ENDPOINT=''" not in contact_text:
        raise ValueError("Activation refusée: PERSONAL_ENDPOINT doit être vide avant la transition.")

    contact_text = replace_once(
        contact_text,
        f'data-personal-formspree-state="{PERSONAL_CONTACT_PENDING_STATE}"',
        f'data-personal-formspree-state="{PERSONAL_CONTACT_ACTIVE_STATE}"',
        "état DOM contact",
    )
    contact_text = replace_once(
        contact_text,
        "var PERSONAL_ENDPOINT=''",
        f"var PERSONAL_ENDPOINT='{endpoint}'",
        "PERSONAL_ENDPOINT",
    )
    contact_text = replace_exact_count(
        contact_text,
        PERSONAL_CONTACT_PENDING_META,
        PERSONAL_CONTACT_ACTIVE_META,
        4,
        "métadonnées Contact",
    )
    contact_text = replace_once(
        contact_text,
        PERSONAL_CONTACT_PENDING_HERO,
        PERSONAL_CONTACT_ACTIVE_HERO,
        "hero Contact",
    )
    contact_text = replace_once(
        contact_text,
        PERSONAL_CONTACT_PENDING_SECURITY,
        PERSONAL_CONTACT_ACTIVE_SECURITY,
        "bloc sécurité Contact",
    )
    for index, (old, new) in enumerate(CONTACT_REPLACEMENTS, start=1):
        contact_text = replace_once(contact_text, old, new, f"texte contact #{index}")

    privacy_text = replace_once(
        privacy_text,
        PRIVACY_PENDING,
        PRIVACY_ACTIVE,
        "politique de confidentialité",
    )
    governance_text = replace_once(
        governance_text,
        PERSONAL_CONTACT_PENDING_GOVERNANCE_COPY,
        PERSONAL_CONTACT_ACTIVE_GOVERNANCE_COPY,
        "gouvernance vie privée",
    )

    generated_errors = validate_personal_contact_contract(contact_text, privacy_text, governance_text)
    if generated_errors:
        raise ValueError("État actif généré invalide: " + " | ".join(generated_errors))
    return contact_text, privacy_text, governance_text


def self_test() -> None:
    endpoint = "https://formspree.io/f/personalSelfTest42"
    contact = (
        '<form id="contact-general" data-personal-formspree-state="pending-separate-endpoint">'
        '<button aria-disabled="true" disabled id="contact-submit">Configuration</button></form>'
        + (PERSONAL_CONTACT_PENDING_META * 4)
        + PERSONAL_CONTACT_PENDING_HERO
        + PERSONAL_CONTACT_PENDING_SECURITY
        + "".join(old for old, _ in CONTACT_REPLACEMENTS)
        + "<script>var PERSONAL_ENDPOINT='';"
        + RUNTIME_GATE
        + "</script>"
    )
    privacy = PRIVACY_PENDING
    governance = PERSONAL_CONTACT_PENDING_GOVERNANCE_COPY

    active_contact, active_privacy, active_governance = build_active_contents(
        contact, privacy, governance, endpoint
    )
    if endpoint not in active_contact:
        raise SystemExit("ERREUR auto-test Formspree: endpoint actif non injecté.")
    if PERSONAL_CONTACT_ACTIVE_STATE not in active_contact or PERSONAL_CONTACT_PENDING_STATE in active_contact:
        raise SystemExit("ERREUR auto-test Formspree: transition d’état DOM incorrecte.")
    if active_contact.count(PERSONAL_CONTACT_ACTIVE_META) != 4:
        raise SystemExit("ERREUR auto-test Formspree: métadonnées actives incomplètes.")
    if PERSONAL_CONTACT_ACTIVE_HERO not in active_contact or PERSONAL_CONTACT_ACTIVE_SECURITY not in active_contact:
        raise SystemExit("ERREUR auto-test Formspree: copies actives hero/sécurité incomplètes.")
    if PERSONAL_CONTACT_PENDING_META in active_contact or PERSONAL_CONTACT_PENDING_HERO in active_contact or PERSONAL_CONTACT_PENDING_SECURITY in active_contact:
        raise SystemExit("ERREUR auto-test Formspree: copie pending résiduelle après activation.")
    if PRIVACY_ACTIVE not in active_privacy:
        raise SystemExit("ERREUR auto-test Formspree: politique active non générée.")
    if PERSONAL_CONTACT_ACTIVE_GOVERNANCE_COPY not in active_governance:
        raise SystemExit("ERREUR auto-test Formspree: gouvernance active non générée.")

    for forbidden in (LEGACY_PERSONAL_FORMSPREE_ENDPOINT, NOVA_FORMSPREE_ENDPOINT):
        try:
            validate_endpoint(forbidden)
        except ValueError:
            pass
        else:
            raise SystemExit(f"ERREUR auto-test Formspree: endpoint interdit accepté: {forbidden}")

    try:
        validate_endpoint("https://example.com/form")
    except ValueError:
        pass
    else:
        raise SystemExit("ERREUR auto-test Formspree: domaine non Formspree accepté.")

    print("OK auto-test activation Formspree personnelle: transition atomique pending -> active validée.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Préparer l’activation du formulaire Formspree personnel sans toucher à Projet Nova."
    )
    parser.add_argument("--endpoint", help="Endpoint personnel Formspree distinct, ex. https://formspree.io/f/xxxx")
    parser.add_argument("--apply", action="store_true", help="Écrire les trois fichiers après validation complète")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.endpoint:
        parser.error("--endpoint est requis hors --self-test")

    endpoint = validate_endpoint(args.endpoint)
    contact = CONTACT.read_text(encoding="utf-8", errors="strict")
    privacy = PRIVACY.read_text(encoding="utf-8", errors="strict")
    governance = GOVERNANCE.read_text(encoding="utf-8", errors="strict")
    generated = build_active_contents(contact, privacy, governance, endpoint)

    if not args.apply:
        print("OK dry-run Formspree personnel: transition valide, aucun fichier modifié.")
        print("Fichiers concernés: contact.html, confidentialite.html, gouvernance-vie-privee.html")
        return 0

    for path, content in zip((CONTACT, PRIVACY, GOVERNANCE), generated, strict=True):
        path.write_text(content, encoding="utf-8")
    print("OK activation locale préparée: 3 fichiers écrits. Exécuter ensuite la validation complète du site.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
