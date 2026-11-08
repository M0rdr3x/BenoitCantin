// Projet Nova G0.18 : échéancier de planification, aucun calendrier d'adoption garanti.
export const MILESTONES=Object.freeze(["M01","M02","M03","M04","M05","M06","M07"]);
const objet=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const dateOk=x=>{
 if(typeof x!=="string"||!/^\d{4}-\d{2}-\d{2}$/.test(x))return false;
 const d=new Date(x+"T00:00:00Z");
 return Number.isFinite(d.valueOf())&&d.toISOString().slice(0,10)===x;
};
const urlOk=x=>typeof x==="string"&&/^https:\/\/[^\s/]+\/[^\s]*$/.test(x);
const valideEtape=m=>typeof m.owner_real_name==="string"&&m.owner_real_name.trim()!==""&&
 typeof m.owner_mandate_reference==="string"&&urlOk(m.owner_mandate_reference)&&
 m.budget_authorized===true&&dateOk(m.completion_date)&&
 m.reviewer_independence_verified===true&&m.decision_by_competent_body===true&&
 Array.isArray(m.proof_urls)&&m.proof_urls.length>0&&m.proof_urls.every(urlOk);
export function inspecterCalendrier(plan,audit,closure){
 const erreurs=[];
 if(!objet(plan)||plan.schema!=="nova-g018-calendrier-conditionnel/v1")
   return {ok:false,erreurs:["SCHEMA_INVALIDE"],jalons_attestes_par_declaration:0,
      date_de_fin_certifiee:null,fin_de_programme_certifiee:false};
 if(plan.snapshot_date!=="2026-11-08"||plan.reference_audit_date!=="2026-11-05"||
    plan.programme_completion_score!==47||plan.maximum_score!==100||
    plan.points_to_obtain!==53||plan.documentation_maturity_estimate_percent!==75)
   erreurs.push("REFERENCE_D_AUDIT_ALTEREE");
 if(plan.target!=="2027-12-31"||plan.target_is_binding!==false||
    plan.projected_completion_certified_date!==null||plan.status!=="PLANIFICATION_CONDITIONNELLE_NON_ADOPTEE")
   erreurs.push("DATE_CIBLE_PRESENTEE_COMME_PROMESSE");
 if(!objet(audit)||audit.schema!=="nova-programme-completude-v1"||
    audit.date!==plan.reference_audit_date||audit.scoring?.earned!==47||
    audit.scoring?.maximum!==100)
   erreurs.push("AUDIT_SOURCE_DIFFERENT");
 if(!objet(closure)||closure.checked_score!==47||closure.points_remaining!==53||
    closure.completion_certified!==false||closure.gates_total!==7||closure.gates_passed!==0)
   erreurs.push("PORTES_DE_CLOTURE_INCOHERENTES");
 const items=Array.isArray(plan.milestones)?plan.milestones:[];
 if(items.length!==7||new Set(items.map(x=>x?.id)).size!==7||
    MILESTONES.some((id,i)=>items[i]?.id!==id))erreurs.push("JALONS_INCORRECTS");
 let attestes=0;
 for(const m of items){
  if(!objet(m)||!dateOk(m.target_date)||!Array.isArray(m.depends_on)||
    !["A_PLANIFIER","EN_COURS","TERMINE_DECLARÉ"].includes(m.status)||
    !Array.isArray(m.deliverables)||m.deliverables.length===0)
    {erreurs.push("JALON_MALFORME:"+String(m?.id));continue;}
  const precedent=items.filter(x=>m.depends_on.includes(x?.id));
  if(precedent.length!==new Set(m.depends_on).size||
     precedent.some(x=>x.id===m.id||x.target_date>m.target_date))
    erreurs.push("DEPENDANCES_INCOHERENTES:"+m.id);
  if(m.status==="TERMINE_DECLARÉ"){
    if(!valideEtape(m))erreurs.push("ATTESTATION_INCOMPLETE:"+m.id);
    else if(m.depends_on.some(id=>items.find(x=>x.id===id)?.status!=="TERMINE_DECLARÉ"))
      erreurs.push("DEPENDANCE_NON_TERMINEE:"+m.id);
    else attestes++;
  }else if(m.completion_date!==null||m.decision_by_competent_body===true)
    erreurs.push("FAUSSE_DECISION:"+m.id);
 }
 return {ok:erreurs.length===0,erreurs,jalons_totaux:7,
    jalons_attestes_par_declaration:attestes,
    date_cible_de_planification:plan.target,
    // Les URLs et décisions déclarées n'équivalent jamais à une certification de source.
    date_de_fin_certifiee:null,
    fin_de_programme_certifiee:false,
    cible_garantie:false,
    score_reference:47,
    prochaines_dependances:items.filter(x=>x.depends_on.every(id=>items.find(y=>y.id===id)?.status==="TERMINE_DECLARÉ"))
     .filter(x=>x.status!=="TERMINE_DECLARÉ").map(x=>x.id),
    controle_humain_independant_exige:true
 };
}
