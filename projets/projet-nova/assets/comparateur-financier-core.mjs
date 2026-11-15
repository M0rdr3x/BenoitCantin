/**
 * Projet Nova — comparateur financier des services, version de travail v1.
 * Moteur purement arithmétique; AUCUNE valeur par défaut ni économie réelle implicite.
 * Les paiements publics et les ressources réelles sont des perspectives distinctes.
 */
export const UNIT_FIELDS = Object.freeze([
  "paiementPublic", "administrationPublique", "coutAvalPublic",
  "ressourcesReelles", "capitalAnnualise", "fraisUsagers", "tempsProches"
]);
export const FIXED_FIELDS = Object.freeze(["transitionAnnuelle", "reserveAnnuelle"]);
export const ALL_FIELDS = Object.freeze([...UNIT_FIELDS, ...FIXED_FIELDS]);
export const MODELS = Object.freeze(["public_actuel", "public_reorganise", "prive", "cooperative", "obnl"]);

function ensureAmount(value, label) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1e12)
    throw new RangeError(`Montant invalide pour ${label}. Il faut un nombre entre 0 et 1 000 milliards $CA.`);
  return value;
}
export function evaluerScenario(volume, valeurs) {
  if (!Number.isSafeInteger(volume) || volume < 1 || volume > 100000000)
    throw new RangeError("Volume annuel invalide (entier de 1 à 100 millions).");
  if (!valeurs || typeof valeurs !== "object") throw new TypeError("Scénario manquant.");
  const s = {};
  for (const f of ALL_FIELDS) s[f] = ensureAmount(valeurs[f], f);
  const payerParUnite = s.paiementPublic + s.administrationPublique + s.coutAvalPublic;
  const societeParUnite = s.ressourcesReelles + s.capitalAnnualise +
     s.administrationPublique + s.coutAvalPublic + s.fraisUsagers + s.tempsProches;
  const communAnnuel = s.transitionAnnuelle + s.reserveAnnuelle;
  const coutPublicAnnuel = volume * payerParUnite + communAnnuel;
  const coutSocialAnnuel = volume * societeParUnite + communAnnuel;
  if (![payerParUnite, societeParUnite, coutPublicAnnuel, coutSocialAnnuel].every(Number.isFinite))
    throw new RangeError("Résultat hors limites.");
  return Object.freeze({
    volume, coutPublicAnnuel, coutSocialAnnuel,
    coutPublicMoyen: coutPublicAnnuel / volume,
    coutSocialMoyen: coutSocialAnnuel / volume
  });
}
/** Ecart alternatif - référence. Montant négatif = coût moindre selon les montants saisis. */
export function comparerScenarios(volume, reference, alternative) {
  const a = evaluerScenario(volume, reference);
  const b = evaluerScenario(volume, alternative);
  const deltaPublic = b.coutPublicAnnuel - a.coutPublicAnnuel;
  const deltaSocial = b.coutSocialAnnuel - a.coutSocialAnnuel;
  return Object.freeze({
    reference: a,
    alternative: b,
    deltaPublicAnnuel: deltaPublic,
    deltaSocialAnnuel: deltaSocial,
    deltaPublicUnitaire: deltaPublic / volume,
    deltaSocialUnitaire: deltaSocial / volume,
    statut: "SIMULATION_NON_CERTIFIEE"
  });
}
