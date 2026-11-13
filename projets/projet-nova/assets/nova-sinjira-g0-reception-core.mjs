/**
 * NOVA–SINJIRA G0: rapport de recevabilité des 14 secteurs du registre,
 * en lecture seule. Ce registre NE contient PAS de signature d'audit externe.
 * Aucun champ fourni par un rédacteur ne peut donc homologuer seul G0–G4.
 */
export const GATES=Object.freeze(["G0","G1","G2","G3","G4"]);
export const DOMAINS=Object.freeze([
  "NV-01","NV-02","NV-03","NV-04","NV-05","NV-06","NV-07",
  "NV-08","NV-09","NV-10","NV-11","NV-12","NV-13","NV-14"
]);
export const COST_MODES=Object.freeze([
 "public_actuel","public_reorganise","prive","cooperative","obnl"
]);
export const BASELINE_FIELDS=Object.freeze([
 "source_de_jeu_de_donnees_precis","date_valeur","periode_observation",
 "territoire","population","nombre_unites","annee_de_prix"
]);
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const present=x=>typeof x==="string"&&x.trim().length>0&&x.trim()!=="A_VALIDER";
const calendar=x=>present(x)&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&
 !Number.isNaN(Date.parse(x+"T00:00:00Z"))&&new Date(x+"T00:00:00Z").toISOString().slice(0,10)===x;
export function auditerReceptionG0(registry){
 const anomalies=[];
 if(!object(registry)||registry.schema!=="nova-sinjira-registre-donnees-service/v1"||
  !Array.isArray(registry.dossiers)||registry.dossiers.length!==14)
 return {ok:false,anomalies:["REGISTRE_OU_14_SECTEURS_MANQUANTS"],
    taux_global_completion:null,approbation_programme:false};
 const dossiers=[],seen=new Set();
 registry.dossiers.forEach((d,i)=>{
  if(!object(d)||!present(d.id)||seen.has(d.id)||d.id!==DOMAINS[i]||
     !present(d.domaine))anomalies.push("DOSSIER_ID_INVALIDE:"+i);
  if(object(d)&&present(d.id))seen.add(d.id);
  if(!object(d)){return;}
  const missing=BASELINE_FIELDS.filter(k=>{
   const v=d[k];
   if(k==="date_valeur")return !calendar(v);
   if(k==="nombre_unites")return !Number.isSafeInteger(v)||v<=0;
   if(k==="annee_de_prix")return !Number.isSafeInteger(v)||v<1900||v>2100;
   return !present(v);
  });
  const modeMissing=COST_MODES.filter(m=>{
   const c=d.couts_par_mode?.[m];
   // Les coûts sont des enveloppes à expliquer et sourcer, pas un nombre isolé.
   return !object(c)||!Number.isFinite(c.cout_public_complet_cad)||
    c.cout_public_complet_cad<0||!present(c.source_ref)||
    !present(c.periode)||!present(c.population_reference);
  });
  if(!object(d.couts_par_mode)||COST_MODES.some(m=>!Object.hasOwn(d.couts_par_mode,m)))
    anomalies.push("MODES_COMPARAISON_ABSENTS:"+d.id);
  if(d.qualite_verifiee===true&&missing.length>0)
    anomalies.push("QUALITE_REVENDIQUEE_SANS_BASELINE:"+d.id);
  if(d.chiffrage_valide===true&&modeMissing.length>0)
    anomalies.push("CHIFFRAGE_REVENDIQUE_SANS_COUTS_COMPLETS:"+d.id);
  if(d.affectation_personnel_validee===true&&d.chiffrage_valide!==true)
    anomalies.push("RH_REVENDIQUEE_SANS_FINANCEMENT:"+d.id);
  if(d.diagnostic_non_financier?.porte_g0_franchie===true&&
    (d.qualite_verifiee!==true||missing.length>0))
    anomalies.push("G0_REVENDIQUE_SANS_BASELINE:"+d.id);
  const candidate=missing.length===0&&d.qualite_verifiee===true;
  const costCandidate=modeMissing.length===0&&d.chiffrage_valide===true;
  const staffCandidate=d.affectation_personnel_validee===true;
  dossiers.push({
   id:d.id,domaine:d.domaine,indicateur_propose:d.indicateurs_proposes,
   periode_comparable_et_source_validee:candidate,
   champs_baseline_manquants:missing,
   comparateurs_couts_complets_manquants:modeMissing,
   source_documentaire_partielle_declared:Boolean(d.diagnostic_non_financier)&&
     d.diagnostic_non_financier.diagnosis==="partiel",
   g0_candidat_pour_revue_humaine:candidate,
   g1_candidat_pour_revue_humaine:candidate&&costCandidate&&staffCandidate,
   portes_independamment_attestees:[],
   g0_reception_officielle:false,g1_autorise:false,g2_autorise:false,
   g3_pilote_autorise:false,g4_generalisation_autorisee:false,
   prochaine_action:missing.length?
     "Obtenir source primaire vérifiable, période, population, territoire, unité, millésime des prix et revue qualité":
     "Soumettre le diagnostic sourcé à une revue externe avec avis juridique et décision formelle"
  });
 });
 if(registry.status==="adopte"||registry.status==="deploiement_autorise")
  anomalies.push("REGISTRE_INVENTAIRE_PROMU_SANS_PREUVE");
 const total=dossiers.length;
 return {
  ok:anomalies.length===0,anomalies:[...new Set(anomalies)],
  reference_registry_date:registry.date_revue,
  methode:"RECEVABILITE_DOCUMENTAIRE_ET_LISTE_DE_MANQUES_NON_CERTIFICATIVE",
  nb_secteurs:total,
  dossiers_avec_base_documentee_pour_revue:dossiers.filter(x=>x.g0_candidat_pour_revue_humaine).length,
  dossiers_avec_couts_candidats_pour_revue:dossiers.filter(x=>x.g1_candidat_pour_revue_humaine).length,
  g0_independamment_atteste:0,
  g1_independamment_atteste:0,g2_independamment_atteste:0,
  g3_pilotes_autorises:0,g4_generalisations_autorisees:0,
  controle_externe_hors_champ_de_ce_registre:true,
  dossiers,
  taux_global_completion:null,
  maturite_non_mesuree_par_ce_registre:true,
  calendrier_de_fin_certifiable:false,
  approbation_programme:false,
  pret_a_deployer:false,
  remarque:"Les avis signés, autorisations G0–G4, coûts comparables, droits et résultats de pilotes exigent des pièces indépendantes hors de ce registre."
 };
}
