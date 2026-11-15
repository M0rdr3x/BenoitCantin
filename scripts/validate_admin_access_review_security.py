#!/usr/bin/env python3
"""Refuse les rejeux de décisions d'accès aux projets dans admin-console.

Pas de réseau, pas de données réelles. Tests du source suivi et de mutations
qui suppriment les protections; le workflow Node exécute la branche réelle.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADMIN = ROOT / 'supabase/functions/admin-console/index.ts'
GUARD = ROOT / 'supabase/functions/_shared/project-access-review-guard.mjs'
WORKFLOW = ROOT / '.github/workflows/sinjira-admin-access-review-security.yml'
TESTS = ROOT / 'scripts/test_admin_access_review_security.mjs'

ADMIN_GATES = (
    "if(!UUID_RE.test(requestId)||!validProjectAccessReviewDecision(body.decision))",
    "service.from('access_requests')",
    ".eq('id',requestId).maybeSingle()",
    "if(!isReviewableProjectAccessRequest(r))",
    "service.from('access_requests').update({",
    ".eq('id',r.id).eq('status','pending').select('id').maybeSingle()",
    "if(!transition)return privateJson(",
    "if(decision==='approved'){",
    "service.from('project_access').upsert({",
    "user_id:r.user_id,project_id:r.project_id,access_level:r.requested_level",
)
ADMIN_REQUIRED = (
    "import { validProjectAccessReviewDecision, isReviewableProjectAccessRequest } from '../_shared/project-access-review-guard.mjs';",
    "const {user,service}=await requiredAdmin(req);",
    "'Cache-Control':'private, no-store, max-age=0'",
    "if(rerr)throw new Error('ACCESS_REVIEW_LOOKUP_FAILED');",
    "if(!r)return privateJson(",
    "code:'ACCESS_REQUEST_NOT_PENDING'},409)",
    "code:'ACCESS_REQUEST_CHANGED'},409)",
    "if(transitionError)throw new Error('ACCESS_REVIEW_TRANSITION_FAILED');",
    "if(grantError){",
    "status:'pending',reviewed_by:r.reviewed_by??null,reviewed_at:r.reviewed_at??null,review_note:r.review_note??null",
    ".eq('id',r.id).eq('status','approved')",
    "if(rollbackError)throw new Error('ACCESS_REVIEW_ROLLBACK_FAILED');",
    "throw new Error('ACCESS_REVIEW_GRANT_FAILED');",
)
GUARD_REQUIRED = (
    "export function validProjectAccessReviewDecision(value)",
    "export function isReviewableProjectAccessRequest(record)",
    "record.status === 'pending'",
    "LEVELS.has(record.requested_level)",
    "DECISIONS.has(value)",
    "UUID_RE.test(record.id)",
    "UUID_RE.test(record.user_id)",
    "UUID_RE.test(record.project_id)",
)
WORKFLOW_REQUIRED = (
    "'supabase/functions/admin-console/**'",
    "'supabase/functions/_shared/project-access-review-guard.mjs'",
    "'scripts/test_admin_access_review_security.mjs'",
    "run: node --test scripts/test_admin_access_review_security.mjs\n",
    "run: python3 scripts/validate_admin_access_review_security.py --self-test\n",
    "run: python3 scripts/validate_admin_access_review_security.py\n",
)

def review_section(src: str) -> str:
    marker = "    if(action==='review_access_request'){"
    end_marker = "    if(action==='list_users'){"
    return src.split(marker, 1)[1].split(end_marker, 1)[0] if marker in src and end_marker in src.split(marker, 1)[1] else ""

def audit(admin: str, guard: str, workflow: str, test: str) -> list[str]:
    failures: list[str] = []
    for marker in ADMIN_REQUIRED:
        if marker not in admin:
            failures.append('Fonction admin : contrôle manquant: ' + marker)
    section = review_section(admin)
    if not section:
        failures.append('Branche revue des accès introuvable')
    positions = [section.find(s) for s in ADMIN_GATES]
    if any(p < 0 for p in positions) or positions != sorted(positions):
        failures.append('Ordre attendu : décision, lecture SQL, pending, CAS, confirmation, grant')
    if "status:decision,reviewed_by:user.id" not in section:
        failures.append('Transition de statut contrôlée absente')
    if "if(decision==='approved'){" not in section:
        failures.append("Attribution d'accès conditionnée à une approbation explicite requise")
    if 'access_level:body.' in section or 'user_id:body.' in section or 'project_id:body.' in section:
        failures.append('Privilège ou identité fourni par le navigateur interdit')
    if "body.decision==='approved'?'approved':'refused'" in section:
        failures.append('Décision invalide silencieusement convertie en refus')
    if section.count("service.from('project_access').upsert({") != 1:
        failures.append('La branche doit contenir exactement un grant')
    for marker in GUARD_REQUIRED:
        if marker not in guard:
            failures.append('Helper : contrôle manquant: ' + marker)
    if 'user_metadata' in guard or '.email' in guard:
        failures.append('Le niveau d’accès ne doit pas découler de claims modifiables')
    for marker in WORKFLOW_REQUIRED:
        if marker not in workflow:
            failures.append('Workflow : contrôle CI manquant: ' + marker)
    if 'AsyncFunction' not in test or "const snippet=admin.slice(start,end)" not in test:
        failures.append('Les tests doivent exécuter la branche réelle, pas un faux modèle')
    return failures

def self_test(admin: str, guard: str, workflow: str, test: str) -> int:
    good = audit(admin, guard, workflow, test)
    if good:
        raise AssertionError('Le contrat sain a échoué : ' + ' | '.join(good))
    cases = {
        'suppression vérification décision': ('admin',
            "if(!UUID_RE.test(requestId)||!validProjectAccessReviewDecision(body.decision))",
            "if(false)"),
        'acceptation état résolu': ('admin',
            "if(!isReviewableProjectAccessRequest(r))",
            "if(false)"),
        'contrôle CAS retiré': ('admin',
            ".eq('id',r.id).eq('status','pending').select('id').maybeSingle()",
            ".eq('id',r.id).select('id').maybeSingle()"),
        'rejet de CAS retiré': ('admin',
            "if(!transition)return privateJson(", "if(false)return privateJson("),
        'grant avant CAS': ('admin',
            "if(decision==='approved'){\n        const {error:grantError}",
            "if(decision==='approved'){\n        const {error:grantError} // GRANT_BEFORE_CAS"),
        'rôle navigateur': ('admin',
            "access_level:r.requested_level,granted_by:user.id",
            "access_level:body.access_level,granted_by:user.id"),
        'identité navigateur': ('admin',
            "user_id:r.user_id,project_id:r.project_id,access_level:r.requested_level",
            "user_id:body.user_id,project_id:r.project_id,access_level:r.requested_level"),
        'décision implicite': ('admin',
            "const decision=body.decision;", "const decision=body.decision==='approved'?'approved':'refused';"),
        'rollback supprimé': ('admin',
            "if(rollbackError)throw new Error('ACCESS_REVIEW_ROLLBACK_FAILED');",
            "if(false)throw new Error('ACCESS_REVIEW_ROLLBACK_FAILED');"),
        'retour 409 absent': ('admin',
            "code:'ACCESS_REQUEST_NOT_PENDING'},409)",
            "code:'ACCESS_REQUEST_NOT_PENDING'},200)"),
        'guard état pending affaibli': ('guard',
            "record.status === 'pending'",
            "record.status !== 'new'"),
        'guard niveaux trop larges': ('guard',
            "LEVELS.has(record.requested_level)",
            "Boolean(record.requested_level)"),
        'guard décisions trop larges': ('guard',
            "DECISIONS.has(value)", "Boolean(value)"),
        'UUID projet ignoré': ('guard',
            "UUID_RE.test(record.project_id)", "Boolean(record.project_id)"),
        'test réel supprimé': ('workflow',
            "run: node --test scripts/test_admin_access_review_security.mjs\n",
            "run: echo skipped-review-branch-tests\n"),
        'test mutants supprimé': ('workflow',
            "run: python3 scripts/validate_admin_access_review_security.py --self-test\n",
            "run: echo skipped-review-negative-tests\n"),
    }
    for label, (target, old, new) in cases.items():
        source = {'admin':admin,'guard':guard,'workflow':workflow}[target]
        if old not in source:
            raise AssertionError('Mutation inexistante : '+label)
        replacement = source.replace(old,new,1)
        a,g,w = (replacement if target=='admin' else admin,
                 replacement if target=='guard' else guard,
                 replacement if target=='workflow' else workflow)
        # La modification d'ordre est simulée en déplaçant le grant devant la transition.
        if label=='grant avant CAS':
            sec=review_section(admin)
            start=sec.index("      if(decision==='approved'){\n        const {error:grantError}")
            first=sec.index("      const {data:transition,error:transitionError}")
            grant=sec[start:sec.index("      return privateJson({ok:true});",start)]
            original=sec[first:start]
            replacement_sec=sec[:first]+grant+original+sec[sec.index("      return privateJson({ok:true});",start):]
            a=admin.replace(sec,replacement_sec,1)
        if not audit(a,g,w,test):
            raise AssertionError('Affaiblissement non détecté : '+label)
    print(f'OK : {len(cases)} régressions anti-rejeu/permissions refusées.')
    return len(cases)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test',action='store_true')
    opts=parser.parse_args()
    admin=ADMIN.read_text('utf-8')
    guard=GUARD.read_text('utf-8')
    wf=WORKFLOW.read_text('utf-8')
    test=TESTS.read_text('utf-8')
    if opts.self_test:
        self_test(admin,guard,wf,test)
    problems=audit(admin,guard,wf,test)
    if problems:
        for item in problems:print('NO_GO : '+item)
        return 1
    print('OK : approbation conditionnelle seulement sur pending; CAS avant grant, validation identité et refus des rejeux.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
