// Contrats de frontière pour l'espace personnel Histoire de vie SINJIRA.
// Les RLS/RPC PostgreSQL restent seuls responsables des autorisations.
// Ce module empêche les identifiants/jetons inattendus d'atteindre les DOM et les RPC.
export function isSafeLifeStoryId(value) {
  return typeof value === 'string' &&
    /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(value);
}

export function isSafeDeathReportCode(value) {
  // Le RPC life_story_create_report_code produit 32 octets encodés en hex.
  // Aucun code tronqué, opaque, mal formé ou script ne peut être affiché/copier.
  return typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
}
