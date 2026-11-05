/**
 * Projet Nova G0.10 — Vérification de la transcription secondaire MSSS Feuille A - 2.
 * Aucune estimation d'ETP clinique, de demande servie, de coût ou d'économie.
 */
const integer=x=>Number.isSafeInteger(x)&&x>=0;
const rss=x=>typeof x==="string"&&/^(0[1-9]|1[0-8])$/.test(x);
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
export function inspectProvisionalRhPortrait(d) {
 const errors=[];
 if(!object(d)||d.schema!=="nova-rh-msss-g0-10-secondary-transcription/v1"||
    !Array.isArray(d.regions)) return {ok:false,errors:["INVALID_SCHEMA"],release_authorized:false};
 if(d.regions.length!==18)errors.push("REQUIRES_18_RSS");
 const seen=new Set();let persons=0,prev=0,etcs=0;
 for(const x of d.regions){
   if(!object(x)||!rss(x.rss_id)||seen.has(x.rss_id)){errors.push("INVALID_RSS");continue}
   seen.add(x.rss_id);
   if(!integer(x.persons_2025)||!integer(x.persons_2024)||!integer(x.etc_2024_2025)){
     errors.push("INVALID_REGIONAL_NUMERIC");continue}
   if(x.clinical_fte!==null||x.cost_per_episode!==null||
     x.independently_reviewed!==false)errors.push("FALSE_CLINICAL_OR_REVIEW_CLAIM");
   persons+=x.persons_2025;prev+=x.persons_2024;etcs+=x.etc_2024_2025;
 }
 for(let n=1;n<=18;n++)if(!seen.has(String(n).padStart(2,"0")))errors.push("RSS_MISSING");
 const h=d.separate_hq,t=d.totals;
 if(!object(h)||h.code!=="00"||!integer(h.persons_2025)||!integer(h.etc_2024_2025))errors.push("HQ_INVALID");
 if(!object(t))errors.push("TOTALS_MISSING");
 if(object(t)&&object(h)){
   if(!integer(t.people_2025_reported)||persons+h.persons_2025!==t.people_2025_reported||
     persons!==t.people_2025_sum_regions||persons!==343252||
     t.people_2025_reported!==344056||h.persons_2025!==804||
     t.people_2025_reconciles!==true)
     errors.push("PERSONS_TOTALS_DO_NOT_RECONCILE");
   if(prev!==t.people_2024_sum_regions || !integer(t.people_2024_reported)||
     t.people_2024_reported!==prev)
     errors.push("HISTORICAL_PEOPLE_TOTALS_NOT_RECONCILED");
   const diff=t.etc_2024_2025_reported-(etcs+h.etc_2024_2025);
   if(!integer(etcs)||!integer(t.etc_2024_2025_reported)||
      t.etc_2024_2025_reported!==283740||
      t.etc_2024_2025_sum_regions!==etcs||
      t.etc_2024_2025_delta_reported_minus_rounded_lines!==diff||
      diff!==2||
      t.etc_2024_2025_exact_reconciliation!==false)
     errors.push("ETC_DIFFERENCE_NOT_TRANSPARENT");
 }
 if(!object(d.source)||d.source.original_sha256!==null||
    d.source.original_file_bytes_retained!==false||
    d.source.verified_excel_cell_addresses!==false||
    d.source.independent_audit!==false)
   errors.push("SOURCE_VERIFICATION_FALSIFIED");
 if(!object(d.decision)||d.decision.certification_complete!==false||
    d.decision.g0_passed!==false||d.decision.pilot_authorized!==false||
    d.decision.financial_savings_verified!==null)
   errors.push("INAPPROPRIATE_AUTHORIZATION");
 return {
  ok:errors.length===0,errors:[...new Set(errors)],
  rss_count:d.regions.length,
  persons_regions:persons,persons_hq:h?.persons_2025??null,
  persons_reported:t?.people_2025_reported??null,
  etc_regions:etcs,etc_hq:h?.etc_2024_2025??null,
  etc_reported:t?.etc_2024_2025_reported??null,
  etc_discrepancy:t&&h?t.etc_2024_2025_reported-(etcs+h.etc_2024_2025):null,
  independent_review_complete:false,
  original_file_hash_verified:false,
  clinically_available_fte_verified:false,
  release_authorized:false,
  g0_passed:false,pilot_authorized:false,
  note:"Revue technique de transcription seulement; le total ETC conserve un écart de 2 non résolu."
 };
}
export function makePublicTable(d){
 const report=inspectProvisionalRhPortrait(d);
 if(!report.ok)throw new Error("SOURCE_TRANSCRIPTION_INVALID:"+report.errors.join(","));
 return d.regions.map(x=>({
  rss_id:x.rss_id,
  region:x.region_source_name,
  people_2025:x.persons_2025,
  etc_paid_2024_2025:x.etc_2024_2025,
  status:"TRANSCRIPTION_SECONDAIRE_NON_CERTIFIEE"
 }));
}
