#!/usr/bin/env python3
"""P55H — acquisition volontaire de deux PDF publics, sans certification."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener
)

import controler_integrite_pieces_nova_p55g as p55g

p55f = p55g.p55f
p55e = p55f.p55e
p55b = p55g.p55b
p54z = p55g.p54z
BASE = p55g.BASE
CONFIG = BASE / "P55H_REFERENTIEL_ACQUISITION_PUBLIQUE_2024.json"
NO_GO = p55g.NO_GO
MAX_BYTES = 20_000_000
STATES = (
    "NON_ACQUISES",
    "CONCORDANCE_HISTORIQUE_NON_AUTHENTIFIANTE",
    "EDITION_DIFFERENTE_NON_AUTHENTIFIEE",
)
FILENAME = {
    "VILLE_2024": "VILLE_2024.pdf",
    "MAMH_23027_2024": "MAMH_23027_2024.pdf",
}
GUARDS = {
    "telechargement_interdit_sans_autorisation_explicite",
    "seulement_deux_urls_https_officielles_allowlist",
    "aucune_url_personnalisee",
    "redirects_http_https_refuses",
    "aucun_parametre_de_secret_ni_authentification",
    "pas_de_soumission_ou_contact_humain",
    "pas_d_execution_reseau_en_ci",
    "deux_sources_obligatoires_ensemble",
    "destination_privee_neuve_hors_git",
    "creation_repertoire_0700",
    "fichiers_pdfs_0600",
    "liens_symboliques_interdits",
    "lecture_streaming_taille_limitee_20mo",
    "controle_en_tete_pdf",
    "hash_sha256_calcules_sur_octets_reels",
    "validation_reference_historique_p54q_inchangee",
    "manifest_prive_sans_chemin_ni_signature",
    "aucun_pdf_ni_sha_courant_dans_bilan_public",
    "pas_d_ecrasement_des_references_historiques",
    "editions_divergentes_conservees_en_reserve",
    "telechargement_partiel_nettoye",
    "stabilite_et_relecture_apres_capture",
    "reproduction_nfkc_hors_acquisition",
    "recu_n_est_pas_preuve_de_provenance",
    "aucun_mandat_ni_avis_professionnel",
    "aucune_economie_certifiee",
    "redressement_2023_pas_economie_2024",
    "eliminations_ville_rtc_somhac_pas_gain_nouveau",
    "emplois_services_pouvoir_achat_proteges",
    "deux_scenarios_constitutionnels_distincts",
    "quatre_dossiers_et_date_non_clos",
    "p54n40_p54o10_p54b96_p54c8_non_attestes",
    "aucun_changement_sinjira",
    "aucune_fusion_main",
    "no_go_automatique",
}
INITIAL = {
    "copies_pdf_acquises_et_verifiees_dans_ce_jalon": 0,
    "reproductions_nfkc_cinq_positions": 0,
    "avis_independants_authentifies": 0,
    "mandats_signes": 0,
    "dossiers_p54e_ouverts": 4,
    "date_probable_non_certifiee": 1,
    "taches_p54n_non_attestees": 40,
    "blocages_p54o_non_leves": 10,
    "controles_p54b_non_attestes": 96,
    "controles_p54c_non_attestes": 8,
    "economies_certifiees_cad": None,
    "decision": NO_GO,
}


def need(condition, code):
    if not condition:
        raise ValueError(code)


def official_sources():
    return [
        {
            "code": code,
            "url_officielle": url,
            "nom_fichier": FILENAME[code],
            "taille_octets_historique": length,
            "sha256_historique": sha,
        }
        for code, _org, url, _key, _page, length, sha, _refs
        in p55b.SOURCE_DATA
    ]


def configuration():
    cfg = p54z.read_json(CONFIG)
    expected = {
        "schema_version": "P55H-1",
        "date_reference": "2026-11-03",
        "exercice": 2024,
        "sources_requises": official_sources(),
        "protocole_reseau": "HTTPS_PUBLIC_EXPLICITE_SANS_REDIRECTION",
        "etat_sources": list(STATES),
        "recu_prive_schema": "P55H-RECU-PRIVE-1",
        "protections": {name: True for name in GUARDS},
        "etat_initial": INITIAL,
    }
    need(cfg == expected, "P55H_CONFIGURATION_MODIFIEE")
    prior = p55g.configuration()
    need(prior["schema_version"] == "P55G-1"
         and prior["etat_initial"]["decision"] == NO_GO
         and prior["codes_documents"] == list(FILENAME)
         and len(cfg["sources_requises"]) == 2,
         "P55H_REFERENCES_AMONT_NON_CONFORMES")
    return cfg


class RefuseRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("P55H_REDIRECTION_REFUSEE")


def open_public_https(url):
    allowed = {x["url_officielle"] for x in official_sources()}
    parsed = urlsplit(url)
    need(url in allowed and parsed.scheme == "https"
         and not parsed.username and not parsed.password
         and parsed.port is None and parsed.fragment == "",
         "P55H_HOTE_OU_URL_NON_AUTORISE")
    # No ambient HTTP(S) proxies, browser cookies, credentials or redirects.
    opener = build_opener(
        ProxyHandler({}), HTTPSHandler(context=ssl.create_default_context()),
        RefuseRedirects()
    )
    request = Request(
        url,
        headers={"User-Agent": "ProjetNova-P55H/1.0 public-financial-documents",
                 "Accept": "application/pdf, application/octet-stream"},
        method="GET",
    )
    return opener.open(request, timeout=25)


def private_new_folder(folder):
    target = p54z.outside_repo(folder)
    need(target.parent.is_dir()
         and not target.parent.is_symlink()
         and not target.exists() and not target.is_symlink(),
         "P55H_REPERTOIRE_EXISTANT_OU_NON_AUTORISE")
    target.mkdir(mode=0o700, exist_ok=False)
    need((target.stat().st_mode & 0o777) == 0o700,
         "P55H_REPERTOIRE_NON_PRIVE")
    return target


def retrieve_one(spec, directory, fetch=None):
    """Stream only an allowlisted PDF; remove only the newly created file on error."""
    need(type(spec) is dict and spec in official_sources(),
         "P55H_SOURCE_NON_AUTORISEE")
    target = directory / spec["nom_fichier"]
    need(target.parent.is_dir()
         and (target.parent.stat().st_mode & 0o777) == 0o700
         and not target.exists() and not target.is_symlink(),
         "P55H_SORTIE_PDF_REFUSEE")
    fetch = open_public_https if fetch is None else fetch
    created = False
    try:
        with fetch(spec["url_officielle"]) as response:
            need(getattr(response, "status", None) == 200,
                 "P55H_STATUT_HTTP_INVALIDE")
            need(response.geturl() == spec["url_officielle"],
                 "P55H_URL_FINALE_DIFFERE")
            # A server-provided length is advisory. Actual bytes enforce MAX_BYTES.
            clen = response.headers.get("Content-Length")
            if clen is not None:
                need(clen.isascii() and clen.isdigit()
                     and int(clen) <= MAX_BYTES,
                     "P55H_LONGUEUR_ANNONCEE_EXCESSIVE")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0]
            need(mime.lower().strip() in (
                "", "application/pdf", "application/octet-stream"),
                "P55H_TYPE_CONTENU_REFUSE")
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(target, flags, 0o600)
            created = True
            total = 0
            digest = hashlib.sha256()
            with os.fdopen(fd, "wb") as writer:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    need(type(chunk) is bytes,
                         "P55H_CONTENU_NON_BINAIRE")
                    total += len(chunk)
                    need(total <= MAX_BYTES, "P55H_TAILLE_REELLE_EXCESSIVE")
                    if total == len(chunk):
                        need(chunk.startswith(b"%PDF-"),
                             "P55H_ENTETE_PDF_INVALIDE")
                    writer.write(chunk)
                    digest.update(chunk)
                writer.flush()
                os.fsync(writer.fileno())
            need(total >= 5, "P55H_PDF_TROP_COURT")
            return {
                "code": spec["code"],
                "taille_octets_lus": total,
                "sha256_octets_lus": digest.hexdigest(),
                "statut": (
                    p55g.MATCH
                    if total == spec["taille_octets_historique"]
                    and digest.hexdigest() == spec["sha256_historique"]
                    else p55g.DIVERGENT
                ),
            }
    except Exception:
        if created:
            target.unlink(missing_ok=True)
        raise


def acquire_pair(folder, fetch=None):
    """Atomic as a pair: clean up directory on any failure, keep divergent editions."""
    directory = private_new_folder(folder)
    keep = False
    try:
        first, second = official_sources()
        rows = [
            retrieve_one(first, directory, fetch=fetch),
            retrieve_one(second, directory, fetch=fetch),
        ]
        # Repeat hash verification through P55G before generating a receipt.
        again = p55g.capture_pair(
            directory / first["nom_fichier"],
            directory / second["nom_fichier"],
        )
        need(rows == again, "P55H_PDF_MODIFIE_DEPUIS_TELECHARGEMENT")
        p55g.valid_rows(rows)
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        manifest = {
            "schema_version": "P55H-RECU-PRIVE-1",
            "exercice": 2024,
            "collecte_http_utc": stamp,
            "sources": rows,
            "empreinte_metadonnees_sha256": p55g.joint_hash(rows),
            "copie_actuelle_authentifiee_par_emetteur": False,
            "signature_professionnelle_authentifiee": False,
            "reproduction_nfkc_effectuee": False,
            "decision": NO_GO,
        }
        p54z.write_new(directory / "RECU_P55H.json",
                       manifest, private=True)
        keep = True
        return rows
    finally:
        if not keep:
            shutil.rmtree(directory)


def public_report(rows=None):
    if rows is not None:
        p55g.valid_rows(rows)
    supplied = 0 if rows is None else 2
    matches = 0 if rows is None else sum(
        x["statut"] == p55g.MATCH for x in rows)
    different = 0 if rows is None else sum(
        x["statut"] == p55g.DIVERGENT for x in rows)
    return {
        "schema_version": "P55H-BILAN-PUBLIC-1",
        "exercice": 2024,
        "documents_publics_references": 2,
        "copies_locales_acquises_en_mode_volontaire": supplied,
        "copies_correspondant_au_sha_historique_non_authentifiees": matches,
        "editions_differentes_a_examiner": different,
        "copies_non_obtenues": 2 - supplied,
        "reproduction_nfkc_non_effectuee": True,
        "avis_professionnels_authentifies": 0,
        "mandats_signes": 0,
        "dossiers_p54e_ouverts": 4,
        "date_probable_non_certifiee": 1,
        "taches_p54n_non_attestees": 40,
        "blocages_p54o_non_leves": 10,
        "controles_p54b_non_attestes": 96,
        "controles_p54c_non_attestes": 8,
        "eliminations_existantes_comme_nouveau_gain": False,
        "redressement_2023_comme_economie_2024": False,
        "economies_certifiees_cad": None,
        "transmission_externe_autorisee": False,
        "fusion_main_autorisee": False,
        "decision": NO_GO,
    }


def public_plan():
    return {
        "schema_version": "P55H-PLAN-PUBLIC-1",
        "exercice": 2024,
        "sources_publiees_a_consulter": [
            {"code": s["code"], "url_officielle": s["url_officielle"]}
            for s in official_sources()
        ],
        "activation_reseau_automatique": False,
        "telechargement_donnees_privees": False,
        "controle_versions_historiques_requis": True,
        "relecture_visuelle_et_experts_requis": True,
        "etape_suivante_si_concordance": "P55G_RECU_ET_P55C_REPRODUCTION_LOCALES",
        "etape_suivante_si_divergence": "REVUE_HUMAINE_DES_EDITIONS",
        "decision": NO_GO,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autoriser-lecture-https-public", action="store_true")
    parser.add_argument("--destination-privee")
    parser.add_argument("--bilan-public")
    parser.add_argument("--plan-public")
    parser.add_argument("--exiger-authenticite", action="store_true")
    args = parser.parse_args(argv)
    try:
        configuration()
        need(args.autoriser_lecture_https_public == bool(args.destination_privee),
             "P55H_ACTIVATION_EXPLICITE_ET_DESTINATION_REQUISES")
        targets = [p for p in (args.bilan_public, args.plan_public) if p]
        files = [Path(p).expanduser().absolute() for p in targets]
        need(len({p.resolve() for p in files}) == len(files),
             "P55H_SORTIES_CONFONDUES")
        for file in files:
            need(file.parent.is_dir()
                 and not file.parent.is_symlink()
                 and not file.exists() and not file.is_symlink(),
                 "P55H_SORTIE_PUBLIQUE_REFUSEE")
        if args.destination_privee:
            dest = p54z.outside_repo(args.destination_privee)
            need(dest not in files
                 and not any(dest in f.parents for f in files),
                 "P55H_SORTIES_IMBRIQUEES")
        rows = None
        if args.autoriser_lecture_https_public:
            rows = acquire_pair(args.destination_privee)
        summary = public_report(rows)
        if args.bilan_public:
            p54z.write_new(args.bilan_public, summary)
        if args.plan_public:
            p54z.write_new(args.plan_public, public_plan())
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        if args.exiger_authenticite:
            return 3
        return 4 if rows and any(
            x["statut"] == p55g.DIVERGENT for x in rows) else 0
    except (ValueError, KeyError, TypeError, OSError, UnicodeError,
            json.JSONDecodeError, HTTPError, URLError, ssl.SSLError):
        print("P55H_REFUS: SOURCE_PUBLIQUE_OU_CHAINE_NON_CONFORME",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
