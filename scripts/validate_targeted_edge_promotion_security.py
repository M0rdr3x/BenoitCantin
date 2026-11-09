#!/usr/bin/env python3
"""Garde de promotion ciblée Edge : aucune connexion ni écriture dans ce programme."""
from __future__ import annotations
import argparse
import json
import re
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/sinjira-targeted-edge-hardening-release.yml"
PROJECT = "gpvivleexywljowcqkru"
TARGETS = frozenset(("revoke-my-contributions", "redeem-license-code"))
PUBLIC = frozenset(("get-document-url", "send-game-report", "life-story-delivery", "nova-civic-poll"))
SHA_CHECKOUT = "d23441a48e516b6c34aea4fa41551a30e30af803"
SHA_PYTHON = "ece7cb06caefa5fff74198d8649806c4678c61a1"
SHA_SUPABASE = "3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf"


def check(condition: bool, errors: list[str], label: str) -> None:
    if not condition:
        errors.append(label)


def verify_repository(root: Path, workflow: str) -> list[str]:
    errors: list[str] = []
    config = tomllib.loads((root / "supabase/config.toml").read_text("utf-8"))
    for slug in TARGETS:
        cfg = config.get("functions", {}).get(slug, {})
        check(cfg.get("verify_jwt") is True, errors, slug + ": JWT doit rester activé")
        source = (root / "supabase/functions" / slug / "index.ts").read_text("utf-8")
        for marker in ("requiredUser(req)", "readLimitedUtf8Body", "serviceClient()", "no-store"):
            check(marker in source, errors, slug + ": contrat absent " + marker)
        for marker in ("await req.json()", "await req.text()"):
            check(marker not in source, errors, slug + ": corps non borné " + marker)
        if slug == "revoke-my-contributions":
            for marker in ("MAX_REQUEST_BYTES=2048", "p_user_id: user.id", "code:'REVOCATION_FAILED'"):
                check(marker in source, errors, slug + ": garde retiré " + marker)
        else:
            for marker in ("MAX_REQUEST_BYTES=4096", "MIN_CODE_LENGTH=12",
                           "MAX_CODE_LENGTH=80", "p_user_id:user.id", "code:'LICENSE_REDEEM_FAILED'"):
                check(marker in source, errors, slug + ": garde retiré " + marker)

    dollar = "$"
    required = [
        "  pull_request:", "  push:", "  workflow_dispatch:",
        "permissions:\n  contents: read", "environment: production",
        "if: github.event_name == 'workflow_dispatch'",
        "needs: preflight", "cancel-in-progress: false",
        "test \"$GITHUB_REF\" = \"refs/heads/main\"",
        "DEPLOY-SINJIRA-EDGE-$FUNCTION_SLUG",
        'test "$REVIEWED_SHA" = "$GITHUB_SHA"',
        '[[ "$REVIEWED_SHA" =~ ^[0-9a-f]{40}$ ]]',
        "source_commit:",
        "EXPECTED_VERSION=2",
        "python3 scripts/validate_targeted_edge_promotion_security.py --self-test",
        "python3 scripts/validate_targeted_edge_promotion_security.py --verify-repo",
        "python3 scripts/validate_targeted_edge_promotion_security.py --phase pre",
        "python3 scripts/validate_targeted_edge_promotion_security.py --phase post",
        "scripts/validate_license_redemption_security.py",
        "scripts/validate_contribution_revocation_v24_5_52.py",
        "node scripts/test_sensitive_account_streaming.mjs",
        'supabase functions deploy "$FUNCTION_SLUG" --project-ref ' + PROJECT + " --use-api",
        'supabase functions download "$FUNCTION_SLUG" --project-ref ' + PROJECT,
        "ref: " + dollar + "{{ github.sha }}",
        "uses: actions/checkout@" + SHA_CHECKOUT,
        "uses: actions/setup-python@" + SHA_PYTHON,
        "uses: supabase/setup-cli@" + SHA_SUPABASE,
        "version: 2.111.0", "python-version: '3.12.14'",
    ]
    for marker in required:
        check(marker in workflow, errors, "workflow: garde absent " + marker)
    for marker in ("pull_request_target:", "workflow_run:", "schedule:", "--no-verify-jwt",
                   "--prune", "supabase db push", "supabase secrets set",
                   "secrets.SUPABASE_ACCESS_TOKEN"):
        check(marker not in workflow, errors, "workflow: fonctionnalité interdite " + marker)
    check(workflow.count("supabase functions deploy ") == 1, errors,
          "workflow: déploiement doit cibler une fonction exactement")
    check(workflow.count("uses: supabase/setup-cli@") == 1, errors,
          "workflow: CLI unique")
    check(workflow.count("uses: actions/checkout@") == 2, errors,
          "workflow: checkout figé attendu dans chaque tâche")
    check(workflow.count("persist-credentials: false") == 2, errors,
          "workflow: aucune persistance de credentials Git")
    check(workflow.count("environment: production") == 1, errors,
          "workflow: environnement production unique")
    check(workflow.count("ref: " + dollar + "{{ github.sha }}") == 1, errors,
          "workflow: SHA de release non figé")
    secret = dollar + "{{ secrets.SUPABASE_EDGE_DEPLOY_TOKEN }}"
    check(workflow.count("secrets.SUPABASE_EDGE_DEPLOY_TOKEN") == 3, errors,
          "workflow: le secret ne doit servir qu'aux trois étapes de publication")
    check(workflow.count("          SUPABASE_ACCESS_TOKEN: " + secret) == 3, errors,
          "workflow: les secrets doivent rester au niveau d'étape")
    check(re.search(r"(?m)^  release-production:\n    if: github.event_name == 'workflow_dispatch'\n    needs: preflight\n    runs-on: ubuntu-24.04\n    timeout-minutes: 20\n    environment: production", workflow) is not None,
          errors, "workflow: la tâche de production doit être strictement manuelle")
    return errors


def rows(path: Path) -> list[dict]:
    data = json.loads(path.read_text("utf-8"))
    if isinstance(data, dict):
        data = data.get("functions")
    if not isinstance(data, list) or not 13 <= len(data) <= 128:
        raise ValueError("Inventaire de fonctions invalide")
    slugs = [x.get("slug") if isinstance(x, dict) else None for x in data]
    if not all(isinstance(x, str) and re.fullmatch(r"[a-z0-9-]+", x) for x in slugs):
        raise ValueError("Slug Edge non fiable")
    if len(set(slugs)) != len(slugs):
        raise ValueError("Fonctions Edge dupliquées")
    return data


def verify_snapshot(current: list[dict], slug: str, phase: str,
                    previous: list[dict] | None = None) -> list[str]:
    if slug not in TARGETS:
        return ["Fonction hors liste blanche"]
    errors: list[str] = []
    entries = {x["slug"]: x for x in current}
    check(TARGETS | PUBLIC <= entries.keys(), errors, "Fonction critique manquante")
    for name, row in entries.items():
        check(row.get("status") == "ACTIVE", errors, name + ": statut non actif")
        check(type(row.get("verify_jwt")) is bool, errors, name + ": JWT invalide")
    check({n for n,v in entries.items() if v.get("verify_jwt") is False} == PUBLIC,
          errors, "Exceptions sans JWT modifiées")
    info = entries.get(slug, {})
    check(info.get("verify_jwt") is True, errors, "JWT cible désactivé")
    version = info.get("version")
    check(type(version) is int, errors, "Version cible manquante")
    if phase == "pre":
        check(version == 2, errors, "Version pré-déploiement inattendue : arrêt")
    elif phase == "post":
        if previous is None:
            return errors + ["Métadonnées pré-déploiement absentes"]
        prior = {x["slug"]: x for x in previous}
        check(prior.get(slug, {}).get("version") == 2, errors, "Baseline pré-déploiement invalide")
        check(type(version) is int and version > 2, errors, "Version non mise à jour")
        check(prior.keys() == entries.keys(), errors, "Inventaire Edge modifié pendant release")
        for other in prior.keys() & entries.keys() - {slug}:
            for field in ("version", "verify_jwt", "status"):
                check(prior[other].get(field) == entries[other].get(field),
                      errors, other + ": changement concurrent " + field)
    else:
        errors.append("Phase invalide")
    return errors


def verify_deployed_code(local: Path, remote: Path, slug: str) -> list[str]:
    if slug not in TARGETS:
        return ["Fonction hors liste blanche"]
    rel = Path("supabase/functions") / slug / "index.ts"
    source = remote / rel
    # Refuser aussi les parents symboliques : un simple is_symlink() sur index.ts ne suffit pas.
    chain = (remote, remote / "supabase", remote / "supabase/functions",
             remote / "supabase/functions" / slug, source)
    if any(item.is_symlink() for item in chain) or not source.is_file():
        return ["Source téléchargée absente ou lien symbolique"]
    if source.stat().st_size > 250_000:
        return ["Source téléchargée anormalement grande"]
    normalize = lambda p: p.read_text("utf-8", errors="strict").replace("\r\n", "\n").rstrip("\n")
    return [] if normalize(local / rel) == normalize(source) else ["Code déployé différent de main"]


def self_test() -> None:
    records = [{"slug": slug, "status": "ACTIVE", "verify_jwt": slug not in PUBLIC,
                "version": 2 if slug in TARGETS else 4} for slug in sorted(TARGETS | PUBLIC)]
    assert not verify_snapshot(records, "revoke-my-contributions", "pre")
    after = [{**x, "version": 3} if x["slug"] == "revoke-my-contributions" else dict(x) for x in records]
    assert not verify_snapshot(after, "revoke-my-contributions", "post", records)
    for mutated in (
        [{**x,"verify_jwt":False} if x["slug"]=="revoke-my-contributions" else x for x in records],
        [{**x,"version":3} if x["slug"]=="revoke-my-contributions" else x for x in records],
        records+[{"slug":"unexpected", "status":"ACTIVE","verify_jwt":False,"version":1}],
    ):
        assert verify_snapshot(mutated, "revoke-my-contributions", "pre")
    assert verify_snapshot(records, "unexpected", "pre")
    unrelated_changed = [
        {**x, "version": 99} if x["slug"] == "send-game-report" else x
        for x in after
    ]
    assert verify_snapshot(unrelated_changed, "revoke-my-contributions", "post", records)
    with tempfile.TemporaryDirectory() as tmp:
        metadata=Path(tmp)/"edge.json"
        extra=[
            {"slug": "retired-" + str(i), "status": "ACTIVE",
             "verify_jwt": True, "version": 1}
            for i in range(7)
        ]
        synthetic=records+extra
        metadata.write_text(json.dumps(synthetic), "utf-8")
        assert len(rows(metadata)) == 13
        for bad in (synthetic+[synthetic[0]], records, {"bad": "shape"}):
            metadata.write_text(json.dumps(bad), "utf-8")
            try:
                rows(metadata)
            except ValueError:
                pass
            else:
                raise AssertionError("Inventaire Edge invalide accepté")

    with tempfile.TemporaryDirectory() as tmp:
        local,remote=(Path(tmp)/"local",Path(tmp)/"remote")
        for root in (local,remote):
            f=root/"supabase/functions/revoke-my-contributions/index.ts"
            f.parent.mkdir(parents=True)
            f.write_text("hardened();\n","utf-8")
        assert not verify_deployed_code(local,remote,"revoke-my-contributions")
        (remote/"supabase/functions/revoke-my-contributions/index.ts").write_text("unsafe();\n","utf-8")
        assert verify_deployed_code(local,remote,"revoke-my-contributions")
    workflow=WORKFLOW.read_text("utf-8")
    assert not verify_repository(ROOT,workflow),verify_repository(ROOT,workflow)
    for label,src in {
        "PR can deploy":workflow.replace("if: github.event_name == 'workflow_dispatch'",
                                         "if: github.event_name == 'pull_request'",1),
        "No prod environment":workflow.replace("environment: production","",1),
        "JWT disabled":workflow.replace(" --use-api"," --use-api --no-verify-jwt",1),
        "Bulk deploy":workflow.replace('deploy "$FUNCTION_SLUG"','deploy',1),
        "Unbound commit":workflow.replace('test "$REVIEWED_SHA" = "$GITHUB_SHA"','true',1),
    }.items():
        assert verify_repository(ROOT,src), "Modification dangereuse non détectée : " + label
    print("OK sécurité: JWT, limites, rôles, confirmation et dérives de release testés.")


def main() -> int:
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--verify-repo",action="store_true")
    mode.add_argument("--phase",choices=("pre","post"))
    parser.add_argument("--slug")
    parser.add_argument("--metadata",type=Path)
    parser.add_argument("--pre-metadata",type=Path)
    parser.add_argument("--downloaded-root",type=Path)
    args=parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.verify_repo:
        errors=verify_repository(ROOT,WORKFLOW.read_text("utf-8"))
    else:
        if not args.slug or not args.metadata:
            parser.error("--slug et --metadata requis")
        try:
            actual=rows(args.metadata)
            previous=rows(args.pre_metadata) if args.pre_metadata and args.phase=="post" else None
            errors=verify_snapshot(actual,args.slug,args.phase,previous)
            if args.phase=="post" and not errors:
                if not args.downloaded_root:
                    parser.error("--downloaded-root requis pour postflight")
                errors+=verify_deployed_code(ROOT,args.downloaded_root,args.slug)
        except (ValueError,OSError,UnicodeError) as exc:
            errors=["Impossible de valider la production : "+str(exc)]
    if errors:
        for error in errors:
            print("NO_GO: "+error)
        return 1
    print("PASS: promotion ciblée conforme aux gardes de sécurité.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
 + '{{ secrets.SUPABASE_EDGE_DEPLOY_TOKEN }}',
            '      SUPABASE_ACCESS_TOKEN: ' + '
        "Unbound commit":workflow.replace('test "$REVIEWED_SHA" = "$GITHUB_SHA"','true',1),
    }.items():
        assert verify_repository(ROOT,src), "Modification dangereuse non détectée : " + label
    print("OK sécurité: JWT, limites, rôles, confirmation et dérives de release testés.")


def main() -> int:
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--verify-repo",action="store_true")
    mode.add_argument("--phase",choices=("pre","post"))
    parser.add_argument("--slug")
    parser.add_argument("--metadata",type=Path)
    parser.add_argument("--pre-metadata",type=Path)
    parser.add_argument("--downloaded-root",type=Path)
    args=parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.verify_repo:
        errors=verify_repository(ROOT,WORKFLOW.read_text("utf-8"))
    else:
        if not args.slug or not args.metadata:
            parser.error("--slug et --metadata requis")
        try:
            actual=rows(args.metadata)
            previous=rows(args.pre_metadata) if args.pre_metadata and args.phase=="post" else None
            errors=verify_snapshot(actual,args.slug,args.phase,previous)
            if args.phase=="post" and not errors:
                if not args.downloaded_root:
                    parser.error("--downloaded-root requis pour postflight")
                errors+=verify_deployed_code(ROOT,args.downloaded_root,args.slug)
        except (ValueError,OSError,UnicodeError) as exc:
            errors=["Impossible de valider la production : "+str(exc)]
    if errors:
        for error in errors:
            print("NO_GO: "+error)
        return 1
    print("PASS: promotion ciblée conforme aux gardes de sécurité.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
 + '{{ secrets.SUPABASE_EDGE_DEPLOY_TOKEN }}',1
        ),
        "Unbound commit":workflow.replace('test "$REVIEWED_SHA" = "$GITHUB_SHA"','true',1),
    }.items():
        assert verify_repository(ROOT,src), "Modification dangereuse non détectée : " + label
    print("OK sécurité: JWT, limites, rôles, confirmation et dérives de release testés.")


def main() -> int:
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--verify-repo",action="store_true")
    mode.add_argument("--phase",choices=("pre","post"))
    parser.add_argument("--slug")
    parser.add_argument("--metadata",type=Path)
    parser.add_argument("--pre-metadata",type=Path)
    parser.add_argument("--downloaded-root",type=Path)
    args=parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.verify_repo:
        errors=verify_repository(ROOT,WORKFLOW.read_text("utf-8"))
    else:
        if not args.slug or not args.metadata:
            parser.error("--slug et --metadata requis")
        try:
            actual=rows(args.metadata)
            previous=rows(args.pre_metadata) if args.pre_metadata and args.phase=="post" else None
            errors=verify_snapshot(actual,args.slug,args.phase,previous)
            if args.phase=="post" and not errors:
                if not args.downloaded_root:
                    parser.error("--downloaded-root requis pour postflight")
                errors+=verify_deployed_code(ROOT,args.downloaded_root,args.slug)
        except (ValueError,OSError,UnicodeError) as exc:
            errors=["Impossible de valider la production : "+str(exc)]
    if errors:
        for error in errors:
            print("NO_GO: "+error)
        return 1
    print("PASS: promotion ciblée conforme aux gardes de sécurité.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
