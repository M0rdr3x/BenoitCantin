/**
 * Projet Nova — G0.6 : RH & capacité clinique.
 * Contrôles documentaires, jamais une autorisation de projet pilote.
 * Ne jamais additionner une personne en emploi, un professionnel RAMQ et un ETP.
 */
const NON_VALIDE="NON_VALIDE";
const AVIS_FORMEL="REVUE_FORMELLE_REQUISE";

const finiteNonNegative=x=>typeof x==="number"&&Number.isFinite(x)&&x>=0;
const textOk=x=>typeof x==="string"&&x.trim()!=="";
const https=x=>textOk(x)&&x.startsWith("https://");
const fixed=n=>Math.round((n+Number.EPSILON)*1e9)/1e9;

/** Examen des sources, du grain temporel et des unités avant toute comparaison. */
export function inspectRHCohort(data){
 const missing=[];
 if(!data||typeof data!=="object"||Array.isArray(data))return {valid:false,missing:["schema"]};
 if(!/^\d{2}$/.test(data.rss_id??"")||Number(data.rss_id)<1||Number(data.rss_id)>18)missing.push("rss_code");
 if(!textOk(data.period_start)||!textOk(data.period_end)||data.period_end<data.period_start)missing.push("period");
 if(!textOk(data.profession)||!textOk(data.clinical_scope))missing.push("scope");
 if(data.same_population_and_time!==true)missing.push("comparability");
 if(data.no_overlap_documented!==true)missing.push("de_duplicated");
 if(data.includes_ramq_professionals!==true||data.includes_salaried_clinicians!==true)missing.push("coverage");
 if(data.first_line_activity_verified!==true)missing.push("first_line");
 if(data.audit_independent!==true)missing.push("audit");
 if(!https(data.evidence_url))missing.push("evidence_url");
 if(!textOk(data.source_sha256)||!/^[a-f0-9]{64}$/i.test(data.source_sha256))missing.push("source_sha256");
 return {valid:missing.length===0,missing};
}

/**
 * Neutral numerical identity only. It cannot establish service capacity, quality
 * or a causal effect. The 4 groups must use the same unit of FTE, period,
 * territorial denominator, included professions and effort definition.
 */
export function calculateETPReallocation(inputs){
 if(!inputs||typeof inputs!=="object"||Array.isArray(inputs))throw new TypeError("Entrées RH manquantes");
 const required=["public_before","nonpublic_before","public_after","nonpublic_after"];
 if(required.some(k=>!finiteNonNegative(inputs[k])))throw new RangeError("Les quatre ETP sont obligatoires, finis et positifs ou nuls");
 if(inputs.unit!=="ETP_CLINIQUES_PRESENTS_PREMIERE_LIGNE")throw new TypeError("Unité de comparaison ETP cliniques présents obligatoire");
 if(inputs.same_professions!==true||inputs.same_periods_comparable!==true||
    inputs.same_rss!==true||inputs.no_overlap_documented!==true)throw new Error("Périmètres et unités non comparables ou doubles comptes");
 const b=inputs.public_before+inputs.nonpublic_before;
 const a=inputs.public_after+inputs.nonpublic_after;
 return {baseline_total_fte:fixed(b),after_total_fte:fixed(a),
   delta_public_fte:fixed(inputs.public_after-inputs.public_before),
   delta_nonpublic_fte:fixed(inputs.nonpublic_after-inputs.nonpublic_before),
   delta_total_fte:fixed(a-b),
   additional_clinical_encounters:null,quality_effect:null,public_savings:null,
   pilot_authorized:false,
   warning:"Identité comptable synthétique seulement. Les ETP ne prouvent ni actes additionnels, ni accès, ni productivité ni économiе. Les chiffres exigent une source et un audit avant usage public."
 };
}

/** Un registre vide n'est ni une capacité de zéro ni une preuve contre une région. */
export function inspectRegistry(reg){
 if(!reg||!Array.isArray(reg.regions)||reg.regions.length!==18)throw new Error("18 RSS nécessaires");
 const seen=new Set();let empty=0;
 for(const r of reg.regions){
  if(!/^\d{2}$/.test(r.rss_id)||seen.has(r.rss_id))throw new Error("Code RSS incorrect ou dupliqué");
  seen.add(r.rss_id);
  const keys=["employment_count","absence_count","present_count","etp_clinical_first_line",
    "ramq_paid_professionals_count","overtime_hours","mandatory_overtime_hours",
    "external_net_hires_etp","internal_transfers_etp","regional_net_change_etp",
    "clinical_episodes_done","unit_cost_complete"];
  if(keys.every(k=>r[k]===null))empty++;
 }
 return {regions:reg.regions.length,regions_without_validated_rh:empty,
    available_region_costs:reg.regions.filter(r=>finiteNonNegative(r.unit_cost_complete)&&r.independent_review===true).length,
    gate:"NON_FRANCHI",pilot_authorized:false,region_ranking_authorized:false};
}
