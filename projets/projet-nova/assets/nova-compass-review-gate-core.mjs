/**
 * Boussole Nova : inventaire documentaire NON CERTIFICATIF.
 * IMPORTANT : "secondIndependentReview" est le NOM HISTORIQUE d'une case
 * qui contient des relectures ChatGPT. Ce n'est pas une signature externe.
 * Une vraie approbation indépendante doit être vérifiée dans un processus
 * externe, avec revue humaine contradictoire, vérification URL et décision.
 */
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const https=x=>{
 try {
  if(typeof x!=="string")return false;
  const u=new URL(x);
  return u.protocol==="https:"&&!u.username&&!u.password;
 }catch{return false;}
};
const allowed=new Set(["unknown","documented_support","documented_opposition",
 "documented_mixed_or_conditional","ambiguous","contradictory"]);
const evidenceStatus=new Set(["documented_support","documented_opposition",
 "documented_mixed_or_conditional","ambiguous","contradictory"]);
export function inspectReviewGate({questionnaire,parties,sources,preuves}={}){
 const errors=[];
 if(!Array.isArray(questionnaire?.questions)||questionnaire.questions.length!==64||
    !Array.isArray(parties?.parties)||parties.parties.length!==22||
    !Array.isArray(sources?.parties)||sources.parties.length!==22||
    !Array.isArray(preuves?.partyIds)||preuves.partyIds.length!==22||
    !Array.isArray(preuves?.questions)||preuves.questions.length!==64||
    !Array.isArray(preuves?.evidenceRecords)){
  return {ok:false,errors:["CORPUS_REQUIS_INCOMPLET"],
   independent_human_reviews_attested_in_this_audit:0,
   release_documentary_gate_passed:false,party_comparison_authorized:false,
   percent_complete:null};
 }
 const qids=new Set(questionnaire.questions.map(x=>x.id));
 const ids=new Set(parties.parties.map(x=>x.id));
 if(qids.size!==64||ids.size!==22||
    sources.parties.some(p=>!ids.has(p.id))||
    preuves.partyIds.some(id=>!ids.has(id))||
    new Set(preuves.partyIds).size!==22)
 errors.push("IDENTITES_CORPUS_INCOHERENTES");
 const matrix=new Map(), matrixCount={};
 for(const row of preuves.questions){
  if(!qids.has(row.questionId)||!obj(row.statuses)||
    Object.keys(row.statuses).length!==22||Object.keys(row.statuses).some(id=>!ids.has(id)))
     errors.push("MATRICE_INCOMPLETE");
  for(const [pid,status] of Object.entries(row.statuses||{})){
   if(!allowed.has(status))errors.push("STATUT_INCONNU");
   const k=row.questionId+"::"+pid;
   if(matrix.has(k))errors.push("POSITION_DUPLIQUEE");
   matrix.set(k,status);
   if(status!=="unknown")matrixCount[k]=(matrixCount[k]||0)+1;
  }
 }
 const counts={ai_documentary_second_reads:0,
  declared_finalizable:0,described_second_reads:0,
  source_urls_structurally_valid:0,non_unknown_matrix_cells:0,
  evidence_candidate_count:preuves.evidenceRecords.length};
 const byKey=new Set(),rids=new Set(),reviewerCategories={ai:0,non_ai_named:0,missing:0};
 for(const r of preuves.evidenceRecords){
  const k=r.questionId+"::"+r.partyId;
  if(rids.has(r.recordId)||byKey.has(k))errors.push("FICHE_PREUVE_DUPLIQUEE");
  rids.add(r.recordId);byKey.add(k);
  if(!qids.has(r.questionId)||!ids.has(r.partyId)||
     !evidenceStatus.has(r.proposedStatus)||matrix.get(k)!==r.proposedStatus)
    errors.push("FICHE_MATRICE_NON_CONCORDANTE");
  if(!https(r.sourceUrl))errors.push("SOURCE_URL_NON_SECURISÉE");
  else counts.source_urls_structurally_valid++;
  if(r.finalizable===true)counts.declared_finalizable++;
  if(r.secondIndependentReview?.status==="completed")counts.described_second_reads++;
  const reviewer=String(r.secondIndependentReview?.reviewer||"").trim();
  if(!reviewer)reviewerCategories.missing++;
  else if(/chatgpt|openai|\b(ai|ia|llm)\b|mod[eè]le de langage/i.test(reviewer)){
    counts.ai_documentary_second_reads++;
    reviewerCategories.ai++;
  } else reviewerCategories.non_ai_named++;
 }
 for(const [k,status] of matrix){
  if(status!=="unknown"){
   counts.non_unknown_matrix_cells++;
   if(!byKey.has(k))errors.push("MATRICE_SANS_FICHE");
  }
 }
 if(parties.parties.some(p=>p.comparisonEligible!==false||
      Object.keys(p.positions||{}).length!==0))
   errors.push("COMPARAISON_POLITIQUE_ACTIVEE_SANS_RECEPTEUR_INDEPENDANT");
 if(preuves.evidenceRules?.secondIndependentReviewRequiredBeforeFinalization!==true)
   errors.push("REGLE_DE_RELECTURE_OMISE");
 // Ne JAMAIS auto-accepter une signature dans le corpus lui-même : ce serait
 // une auto-certification. Seule une procédure externe contradictoire peut
 // attester un codeur indépendant et l'actualité des sources.
 return {
  ok:errors.length===0,errors:[...new Set(errors)],
  data_snapshot:preuves.updated,
  counts,reviewerCategories,
  independent_human_reviews_attested_in_this_audit:0,
  external_reviewer_identity_authentication_performed:false,
  external_source_content_verification_performed:false,
  party_comparison_authorized:false,
  release_documentary_gate_passed:false,
  signoff_required:"TWO_SEPARATE_HUMAN_REVIEWERS_PRIMARY_SOURCES_ATTESTED",
  percent_complete:null,
  decision:"NO_GO_REVIEW_HUMAN_ATTESTATION_NOT_PRESENT",
  interpretation:"Les relectures automatisées sont des preuves de travail, pas des avis humains indépendants. Le champ finalizable ne certifie ni le parti ni les positions."
 };
}
