// Projet Nova — contrôle structurel des preuves juridiques P0.
// ATTENTION : ce code ne peut ni certifier un avis ni adopter un texte.
export const DOSSIERS=Object.freeze(Array.from({length:12},(_,i)=>"J"+String(i+1).padStart(2,"0")));
export const CONTEXTES=Object.freeze(["QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN_HYPOTHETIQUE"]);
export const STATUTS=Object.freeze(["NON_VERIFIE","EXAMEN_EN_COURS","AVIS_FAVORABLE","AVIS_DEFAVORABLE"]);
export const PIECES=Object.freeze([
  "opinion_reference_url","opinion_date","independent_reviewer_mandate_reference_url",
  "reviewer_independence_checked","rights_and_remedies_reference_url",
  "budget_and_workforce_reference_url","consultations_report_reference_url"
]);
const objet=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const texte=x=>typeof x==="string"&&x.trim().length>0;
const urlSource=x=>typeof x==="string"&&/^https:\/\/[^\s/]+(?:\/[^\s]*)?$/.test(x);
const dateValide=x=>{
 if(typeof x!=="string"||!/^\d{4}-\d{2}-\d{2}$/.test(x))return false;
 const d=new Date(x+"T00:00:00Z");
 return Number.isFinite(d.valueOf())&&d.toISOString().slice(0,10)===x;
};
export function inspecterMatriceJuridique(m){
 const erreurs=[];
 if(!objet(m)||m.schema!=="nova-matrice-juridique-p0/v1"){
   return {ok:false,erreurs:["SCHEMA_INVALIDE"],dossiers:0,contextes_examens_declares:0,
     certification_automatique_autorisee:false,points_supplementaires_autorises:0};
 }
 if(m.date!=="2026-11-08"||m.baseline_points!==47||m.maximum_points!==100||
   m.increment_at_creation!==0)erreurs.push("REFERENCE_SCORE_ALTEREE");
 if(m.independent_juridical_audit_completed!==false)erreurs.push("AUDIT_EXTERNE_NON_ETABLI");
 if(!Array.isArray(m.jurisdictions)||m.jurisdictions.length!==2||
   CONTEXTES.some((c,i)=>m.jurisdictions[i]!==c))erreurs.push("CONTEXTES_INCORRECTS");
 const cases=Array.isArray(m.cases)?m.cases:[];
 if(cases.length!==12||new Set(cases.map(d=>d?.id)).size!==12||
   DOSSIERS.some((id,i)=>cases[i]?.id!==id))erreurs.push("DOUZE_DOSSIERS_INCOMPLETS");
 let contextesExaminesDeclares=0;
 for(const row of cases){
   if(!objet(row)||!texte(row.objet)||!texte(row.domaine)||
      !row.source?.startsWith("official/")||!texte(row.required_evidence)||
      !["A_EXAMINER","EN_INSTRUCTION","AVIS_DOCUMENTE"].includes(row.statut)){
     erreurs.push("DOSSIER_MALFORME:"+String(row?.id));continue;
   }
   let avis=0;
   for(const contexte of CONTEXTES){
     const item=row[contexte],code=String(row.id)+":"+contexte;
     if(!objet(item)||!STATUTS.includes(item.legal_status)||!texte(item.question)){
       erreurs.push("CONTEXTE_MALFORME:"+code);continue;
     }
     if(!objet(item.review_evidence)||PIECES.some(k=>!(k in item.review_evidence))){
       erreurs.push("PREUVES_NON_STRUCTUREES:"+code);continue;
     }
     const status=item.legal_status;
     const e=item.review_evidence;
     if(status==="AVIS_FAVORABLE"||status==="AVIS_DEFAVORABLE"){
       const urls=PIECES.filter(x=>x.endsWith("_url"));
       if(urls.some(k=>!urlSource(e[k]))||
          !dateValide(e.opinion_date)||e.reviewer_independence_checked!==true){
          erreurs.push("AVIS_SANS_PIECES_EXIGIBLES:"+code);continue;
       }
       contextesExaminesDeclares++;
       avis++;
     } else {
       if(e.reviewer_independence_checked===true&&!urlSource(e.independent_reviewer_mandate_reference_url))
         erreurs.push("INDEPENDANCE_SANS_MANDAT:"+code);
       if(e.opinion_date!==null&&!dateValide(e.opinion_date))
         erreurs.push("DATE_OPINION_INVALIDE:"+code);
     }
   }
   if(avis>0&&row.statut==="A_EXAMINER")erreurs.push("STATUT_DOSSIER_INCOHERENT:"+row.id);
   if(!Array.isArray(row.evidence_urls)||row.evidence_urls.some(v=>!urlSource(v)))
     erreurs.push("SOURCES_NON_VALIDES:"+row.id);
   if(row.adoption_decision!==null&&m.independent_juridical_audit_completed!==true)
     erreurs.push("ADOPTION_NON_PROUVEE:"+row.id);
 }
 return {
   ok:erreurs.length===0,erreurs,dossiers:cases.length,
   contextes_attendus:24,contextes_examens_declares:contextesExaminesDeclares,
   // Une URL et une déclaration ne prouvent pas l'authenticité d'un avis.
   certification_automatique_autorisee:false,
   points_supplementaires_autorises:0,
   evaluation_humaine_requise:true
 };
}
