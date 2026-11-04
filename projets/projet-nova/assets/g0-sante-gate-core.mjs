/**
 * Projet Nova — G0.5 santé.
 * Contrôle de complétude méthodologique, jamais une autorisation juridique ou clinique.
 * Module sans accès réseau, sans dépendances et sans données de patients.
 */
export const REQUIRED_G0_CODES=Object.freeze([
  "PERIMETRE","ACCES_REEL","QUALITE","EQUITE","PERSONNEL",
  "COUT_COMPLET","DROITS","CONTREFACTUEL"
]);
export const EVIDENCE_ACCEPTED_STATUS="VALIDEE_INDEPENDAMMENT";
export const GATE_NOT_PASSED="NON_FRANCHI";
export const REVIEW_ONLY="REVUE_FORMELLE_REQUISE";

const isPlainObject=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const isNonBlank=x=>typeof x==="string"&&x.trim().length>0;
const isHttps=x=>isNonBlank(x)&&x.startsWith("https://");
const validRss=x=>typeof x==="string"&&/^(0[1-9]|1[0-8])$/.test(x);

/**
 * Validate a single dimension in an auditable region row.
 * A status string alone is NEVER sufficient proof.
 */
export function inspectEvidence(entry){
  const missing=[];
  if(!isPlainObject(entry))return {complete:false,missing:["evidence_entry"]};
  if(entry.status!==EVIDENCE_ACCEPTED_STATUS)missing.push("statut_de_preuve");
  if(!isNonBlank(entry.official_source_id))missing.push("source_officielle");
  if(!isNonBlank(entry.reference_period))missing.push("periode");
  if(!isHttps(entry.evidence_url))missing.push("lien_de_preuve_https");
  if(entry.perimeter_approved!==true)missing.push("perimetre_valide");
  if(entry.methodological_validated!==true)missing.push("methode_validee");
  if(entry.independently_validated!==true)missing.push("validation_independante");
  if(!isNonBlank(entry.reviewer))missing.push("identite_controleur");
  return {complete:missing.length===0,missing};
}

/**
 * Readiness never means the gate has passed. Manual approval is unavoidable.
 * Fail closed when the row is malformed, not part of the defined territory,
 * or when any mandatory evidence dimension is missing/partial.
 */
export function assessRegionalG0(row){
  if(!isPlainObject(row)||!validRss(row.rss_id)||!isPlainObject(row.preuves)){
    return {rss_id:isPlainObject(row)?row.rss_id??null:null,ready_for_review:false,
      decision:GATE_NOT_PASSED,validated_dimensions:0,required_dimensions:REQUIRED_G0_CODES.length,
      blockers:[{code:"SCHEMA",missing:["schema_territorial"]}],
      pilot_authorized:false,budget_authorized:false};
  }
  const blockers=[];let validated=0;
  for(const code of REQUIRED_G0_CODES){
    const check=inspectEvidence(row.preuves[code]);
    if(check.complete)validated++;
    else blockers.push({code,missing:check.missing});
  }
  if(row.survey_included===false&&row.observed_affiliation_2025_percent!==null) {
    blockers.push({code:"HORS_CHAMP",missing:["taux_enquete_impossible_pour_ce_territoire"]});
  }
  if(row.survey_included===true&&!Number.isFinite(row.observed_affiliation_2025_percent)){
    blockers.push({code:"REFERENTIEL",missing:["observation_affiliation_non_definie"]});
  }
  const reviewReady=blockers.length===0;
  return {
    rss_id:row.rss_id,
    ready_for_review:reviewReady,
    decision:reviewReady?REVIEW_ONLY:GATE_NOT_PASSED,
    validated_dimensions:validated,
    required_dimensions:REQUIRED_G0_CODES.length,
    blockers,
    pilot_authorized:false,
    budget_authorized:false
  };
}
export function assessAllRegions(matrix){
  if(!isPlainObject(matrix)||!Array.isArray(matrix.regions)||!Array.isArray(matrix.categories)){
    throw new TypeError("Matrice G0 invalide");
  }
  const ids=matrix.regions.map(x=>x?.rss_id);
  if(matrix.regions.length!==18||new Set(ids).size!==18||
     REQUIRED_G0_CODES.some(c=>!matrix.categories.some(y=>y.code===c))){
    throw new Error("18 RSS distinctes et 8 critères requis");
  }
  const results=matrix.regions.map(assessRegionalG0);
  const ready=results.filter(x=>x.ready_for_review).length;
  return {
    total_regions:results.length,
    regions_with_affiliation:matrix.regions.filter(x=>x.survey_included===true&&
      Number.isFinite(x.observed_affiliation_2025_percent)).length,
    territories_outside_survey:matrix.regions.filter(x=>x.survey_included===false).length,
    dimensions_required:REQUIRED_G0_CODES.length,
    validated_cells:results.reduce((a,x)=>a+x.validated_dimensions,0),
    cells_required:results.length*REQUIRED_G0_CODES.length,
    ready_for_formal_review:ready,
    gate:GATE_NOT_PASSED,
    pilot_authorized:false,
    savings_certified:false,
    decisions:results
  };
}
