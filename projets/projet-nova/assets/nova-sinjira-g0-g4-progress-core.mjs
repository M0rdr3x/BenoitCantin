/**
 * Projet Nova–Sinjira — contrôleur purement documentaire, arrêté au 8 novembre 2026.
 * Ne peut pas homologuer un dossier, conclure un avis indépendant ni autoriser un pilote.
 */
export const STAGES=Object.freeze(["G0","G1","G2","G3","G4"]);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const unique=a=>Array.isArray(a)&&new Set(a).size===a.length;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const TEXT=Object.freeze({
  source:"data/registre-donnees-services-nova-sinjira.json",
  protocol:"official/working/plan-execution-nova-sinjira-v1.md",
  nova:"data/audit-completude-programme-nova-2026-11-05.json"
});
const expectedRequirements=Object.freeze({
  G0:["base_legale","source_primaire_datee","perimetre_population_territoire","serie_et_dictionnaire","qualite_donnees_verifiee"],
  G1:["maintien_et_amelioration_publics","alternative_prestation_documentee","comparaison_coûts_complets_et_qualite","risques_et_effets_territoriaux","revue_methodologique_independante"],
  G2:["avis_juridique_contexte_applicable","budget_coût_complet_et_financement","protection_des_travailleurs_et_droits","consultation_usagers","plan_continuite_recours"],
  G3:["protocole_et_population_du_pilote","autorisation_competente","protections_donnees_et_securite","indicateurs_et_evaluateur_independant","plan_retour_arriere"],
  G4:["rapport_resultats_pilote_et_effets_indesirables","verification_independante","equite_droits_et_couts_sous_stress","consultation_et_reponse_aux_objections","decision_officielle_documentee"]
});
export function analyserPortesNovaSinjira(matrix,source,audit,protocol){
 const problems=[],flag=x=>problems.push(x);
 if(!obj(matrix)||!obj(source)||!obj(audit)||typeof protocol!=="string")
  return {ok:false,errors:["ENTREE_INCOMPLETE"],pourcentage_achevement_autonome:null,
    date_de_fin_attestee:null,autorisation_de_pilote:false};
 if(matrix.schema!=="nova-sinjira-g0-g4-evidence-gates/v1"||
    matrix.reference_date!=="2026-11-08"||matrix.timezone!=="America/Toronto"||
    matrix.status!=="CADRAGE_DOCUMENTAIRE_NON_HOMOLOGUE"||
    matrix.source_dossiers!==TEXT.source||
    matrix.source_protocol!==TEXT.protocol||
    matrix.source_nova_audit!==TEXT.nova)
    flag("VERSION_ET_PROVENANCE");
 if(matrix.program!=="Projet Nova — modèle de réforme Nova–Sinjira"||
    matrix.programme_completion_percent!==undefined||
    matrix.independent_programme_completion_percent!==null||
    matrix.completion_date_certified!==null||
    matrix.target_completion_date!==null||
    matrix.completion_certified!==false||
    matrix.adoptable_or_implementable!==false||
    matrix.review_mandate_confirmed!==false||
    matrix.source_lines_are_references_not_independent_attestations!==true||
    matrix.project_sinjira_distinct_from_state_operator!==true||
    matrix.derived_completion_percent_prohibited!==true)
    flag("CERTIFICATION_INVENTEE");
 if(!same(matrix.contextes_a_etudier,["QUEBEC_DANS_LE_CANADA","QUEBEC_SOUVERAIN_HYPOTHETIQUE"])||
    matrix.contexts_financially_or_legally_certified!==false)
    flag("CONTEXTES_JURIDIQUES_CONFONDUS");
 if(source.schema!=="nova-sinjira-registre-donnees-service/v1"||
    source.date_revue!=="2026-11-03"||
    source.status!=="inventaire-des-besoins-sans-series-sectorielles-validees"||
    !Array.isArray(source.dossiers)||source.dossiers.length!==14||
    !unique(source.dossiers.map(d=>d?.id)))
    flag("SOURCE_SECTORIELLE_DERIVEE_INVALIDE");
 if(audit.schema!=="nova-programme-completude-v1"||
    audit.scoring?.earned!==47||
    audit.scoring?.maximum!==100||
    !Array.isArray(audit.sector_register)||
    audit.sector_register.length!==14||
    audit.sector_register.some(x=>x.completed_measure_sheets_confirmed!==0||
      x.independent_validation_confirmed!==null))
    flag("AUDIT_NOVA_CHANGE");
 if(!protocol.includes("G0 : diagnostic")||!protocol.includes("G1 : comparaison")||
    !protocol.includes("G2 : légalité + financement")||
    !protocol.includes("G3 : pilote")||!protocol.includes("G4 : généralisation")||
    !protocol.includes("étude non adoptée"))
    flag("PROTOCOLE_G0_G4_NON_ALIGNE");
 if(!Array.isArray(matrix.definitions)||matrix.definitions.length!==5||
    matrix.definitions.some((d,i)=>d?.id!==STAGES[i]||
     !same(d.required_artifacts,expectedRequirements[STAGES[i]])||
     typeof d.guardrail!=="string"||d.guardrail.length<55))
    flag("DEFINITION_DES_PORTES");
 if(matrix.total_sectors!==14||matrix.stages_per_sector!==5||
    matrix.total_stage_acceptance_gates!==70||
    matrix.verified_stage_acceptance_gates!==0||
    matrix.coverage_of_verified_stage_gates_percent!==0)
    flag("COMPTAGE_CERTIFICATIONS_NON_ATTESTEES");
 const sectors=Array.isArray(matrix.sectors)?matrix.sectors:[];
 if(sectors.length!==14||!unique(sectors.map(x=>x?.id)))
    flag("DOSSIERS_ABSENTS_OU_DUPLIQUES");
 let count=0, progressDocs=0;
 for(let i=0;i<14;i++){
  const entry=sectors[i],d=source.dossiers?.[i];
  if(!obj(entry)||!obj(d)){flag("DOSSIER_MANQUANT:"+i);continue;}
  if(entry.id!==d.id||entry.source_index!==i+1||entry.title!==d.domaine||
    entry.unit_of_comparison!==d.unite_comparaison_proposee||
    entry.source_data_status!==d.etat_donnees||
    entry.source_data_quality_confirmed!==d.qualite_verifiee||
    entry.source_financing_confirmed!==d.chiffrage_valide||
    entry.source_workforce_assessment_confirmed!==d.affectation_personnel_validee||
    entry.source_primary_dataset_reference!==d.source_de_jeu_de_donnees_precis||
    typeof entry.stage_work_notes!=="string"||entry.stage_work_notes.length<30)
   flag("DOSSIER_SOURCE_DIVERGENT:"+d.id);
  if(d.id==="NV-03")progressDocs++;
  if(!Array.isArray(entry.stages)||entry.stages.length!==5){
   flag("ETAPES_INCOMPLETES:"+d.id);continue;
  }
  for(let s=0;s<5;s++){
   const g=entry.stages[s];count++;
   if(!obj(g)||g.id!==STAGES[s]||g.status!=="NON_ATTESTE"||
      g.evidence_url!==null||g.evidence_checked_at!==null||
      g.independent_review_url!==null||g.competent_decision_url!==null||
      g.competent_decision_at!==null||
      g.review_of_original_sources_complete!==false||
      g.obligations_and_population_consulted_confirmed!==false)
    flag("PORTE_FAUSSEMENT_ATTESTEE:"+d.id+":"+STAGES[s]);
  }
 }
 return {
  ok:problems.length===0,
  errors:[...new Set(problems)],
  date_releve:"2026-11-08",
  nombre_dossiers_de_travail:sectors.length,
  nombre_portes_g0_g4_attendues:70,
  nombre_portes_structurellement_controlees:count,
  nombre_portes_attestees_au_releve:0,
  // 0/70 = nombre de validations attestées, PAS 0 % de programme rédigé.
  couverture_des_portes_attestees_pct:0,
  pourcentage_achevement_autonome:null,
  date_de_fin_attestee:null,
  autorisation_de_pilote:false,
  gain_de_points_Nova:0,
  controle_documentaire_seul:true
 };
}
