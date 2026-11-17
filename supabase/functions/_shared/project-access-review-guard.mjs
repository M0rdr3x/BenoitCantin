/**
 * Contrôles de frontière des décisions d'accès aux projets SINJIRA.
 * Une demande résolue ou annulée ne doit jamais réaccorder des droits.
 * L'identité, le projet et le niveau proviennent de la ligne SQL sous
 * contrôle administrateur (AAL2), pas du corps de la requête.
 */
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const LEVELS=new Set(['player','tester']);
const DECISIONS=new Set(['approved','refused']);

export function validProjectAccessReviewDecision(value) {
  return typeof value === 'string' && DECISIONS.has(value);
}

export function isReviewableProjectAccessRequest(record) {
  return record !== null &&
    typeof record === 'object' &&
    !Array.isArray(record) &&
    record.status === 'pending' &&
    typeof record.id === 'string' && UUID_RE.test(record.id) &&
    typeof record.user_id === 'string' && UUID_RE.test(record.user_id) &&
    typeof record.project_id === 'string' && UUID_RE.test(record.project_id) &&
    typeof record.requested_level === 'string' && LEVELS.has(record.requested_level);
}
