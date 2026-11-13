import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {auditerReceptionG0,DOMAINS,COST_MODES,GATES,BASELINE_FIELDS}
from "../assets/nova-sinjira-g0-reception-core.mjs";
const registry=JSON.parse(await readFile(
 new URL("../data/registre-donnees-services-nova-sinjira.json",import.meta.url),"utf8"));
const run=x=>auditerReceptionG0(x??registry);
const mutate=()=>structuredClone(registry);
function populate(d){
 d.source_de_jeu_de_donnees_precis="urn:source:fiche-fictive-de-test";
 d.date_valeur="2025-03-31";
 d.periode_observation="2024-2025";
 d.territoire="Québec";
 d.population="population admissible fictive";
 d.nombre_unites=120;
 d.annee_de_prix=2025;
 d.qualite_verifiee=true;
 for(const m of COST_MODES)d.couts_par_mode[m]={
   cout_public_complet_cad:1000,source_ref:"urn:scenario:test:"+m,
   periode:"2024-2025",population_reference:"population admissible fictive"
 };
 d.chiffrage_valide=true;
 d.affectation_personnel_validee=true;
}
test("registre réel: 14 secteurs uniques et statut documentaire sans faux pourcentage",()=>{
 const r=run();
 assert.equal(r.ok,true,r.anomalies.join(", "));
 assert.equal(r.nb_secteurs,14);
 assert.deepEqual(r.dossiers.map(x=>x.id),DOMAINS);
 assert.equal(r.taux_global_completion,null);
 assert.equal(r.approbation_programme,false);
 assert.equal(r.pret_a_deployer,false);
});
test("G0-G4: aucune porte homologuée ni pilote autorisé",()=>{
 const r=run();
 assert.deepEqual(GATES,["G0","G1","G2","G3","G4"]);
 for(const key of ["g0_independamment_atteste","g1_independamment_atteste","g2_independamment_atteste",
 "g3_pilotes_autorises","g4_generalisations_autorisees"]){
  assert.equal(r[key],0,key);
 }
 for(const d of r.dossiers)assert.deepEqual(d.portes_independamment_attestees,[]);
});
test("registre réel: les 14 dossiers ont des séries de base encore manquantes",()=>{
 const r=run();
 assert.equal(r.dossiers_avec_base_documentee_pour_revue,0);
 assert.equal(r.dossiers_avec_couts_candidats_pour_revue,0);
 for(const d of r.dossiers){
  assert.deepEqual(d.champs_baseline_manquants,BASELINE_FIELDS);
  assert.deepEqual(d.comparateurs_couts_complets_manquants,COST_MODES);
 }
});
test("santé: sources partielles gardées sans inventer G0 passé ni économies",()=>{
 const r=run();const h=r.dossiers.find(d=>d.id==="NV-03");
 assert.equal(h.source_documentaire_partielle_declared,true);
 assert.equal(h.g0_reception_officielle,false);
 assert.equal(h.g3_pilote_autorise,false);
 assert.equal(registry.dossiers[2].rh_original_evidence_g011.independent_institutional_review,false);
});
test("G0: la source seule, même datée, ne vaut pas l'audit",()=>{
 const x=mutate(),d=x.dossiers[0];
 d.source_de_jeu_de_donnees_precis="https://source.example/data";
 d.date_valeur="2025-03-31";
 assert.equal(run(x).dossiers[0].g0_candidat_pour_revue_humaine,false);
 assert.equal(run(x).dossiers[0].g0_reception_officielle,false);
});
test("provenance prétendument vérifiée sans population = anomalie",()=>{
 const x=mutate();x.dossiers[0].qualite_verifiee=true;
 assert.ok(run(x).anomalies.includes("QUALITE_REVENDIQUEE_SANS_BASELINE:NV-01"));
});
test("chiffrage revendiqué sans postes complets = anomalie",()=>{
 const x=mutate();x.dossiers[1].chiffrage_valide=true;
 assert.ok(run(x).anomalies.includes("CHIFFRAGE_REVENDIQUE_SANS_COUTS_COMPLETS:NV-02"));
});
test("affectation du personnel prétendument validée sans financement = anomalie",()=>{
 const x=mutate();x.dossiers[3].affectation_personnel_validee=true;
 assert.ok(run(x).anomalies.includes("RH_REVENDIQUEE_SANS_FINANCEMENT:NV-04"));
});
test("G0 de santé déclaré franchi sans base complète est rejeté",()=>{
 const x=mutate();x.dossiers[2].diagnostic_non_financier.porte_g0_franchie=true;
 assert.ok(run(x).anomalies.includes("G0_REVENDIQUE_SANS_BASELINE:NV-03"));
});
test("sources candidates complètement renseignées restent NON certifiées",()=>{
 const x=mutate();populate(x.dossiers[0]);
 const r=run(x),d=r.dossiers[0];
 assert.equal(r.ok,true,r.anomalies.join(", "));
 assert.equal(d.g0_candidat_pour_revue_humaine,true);
 assert.equal(d.g1_candidat_pour_revue_humaine,true);
 assert.equal(r.dossiers_avec_base_documentee_pour_revue,1);
 assert.equal(r.dossiers_avec_couts_candidats_pour_revue,1);
 assert.equal(r.g0_independamment_atteste,0);
 assert.equal(r.g1_independamment_atteste,0);
 assert.equal(d.g3_pilote_autorise,false);
 assert.equal(d.g4_generalisation_autorisee,false);
 assert.equal(r.taux_global_completion,null);
});
test("un coût sans pièce et période ne devient pas un coût comparé",()=>{
 const x=mutate();populate(x.dossiers[0]);
 delete x.dossiers[0].couts_par_mode.prive.source_ref;
 const r=run(x);
 assert.equal(r.dossiers[0].g1_candidat_pour_revue_humaine,false);
 assert.ok(r.anomalies.includes("CHIFFRAGE_REVENDIQUE_SANS_COUTS_COMPLETS:NV-01"));
});
test("date impossible et nombre d'unités nul sont refusés",()=>{
 const x=mutate();populate(x.dossiers[0]);
 x.dossiers[0].date_valeur="2025-02-30";
 x.dossiers[0].nombre_unites=0;
 const r=run(x);
 assert.deepEqual(r.dossiers[0].champs_baseline_manquants.sort(),
 ["date_valeur","nombre_unites"].sort());
 assert.equal(r.g0_independamment_atteste,0);
});
test("un dossier manquant ne donne pas un faux échantillon de 13 secteurs",()=>{
 const x=mutate();x.dossiers.pop();
 assert.deepEqual(run(x).anomalies,["REGISTRE_OU_14_SECTEURS_MANQUANTS"]);
 assert.equal(run(x).taux_global_completion,null);
});
test("l'identifiant d'un secteur ne peut être dupliqué ni permuté",()=>{
 const x=mutate();x.dossiers[3].id=x.dossiers[2].id;
 assert.ok(run(x).anomalies.some(v=>v.startsWith("DOSSIER_ID_INVALIDE:3")));
});
test("un statut adopté ou déployé dans l'inventaire sans preuve est rejeté",()=>{
 const x=mutate();x.status="adopte";
 assert.ok(run(x).anomalies.includes("REGISTRE_INVENTAIRE_PROMU_SANS_PREUVE"));
 assert.equal(run(x).approbation_programme,false);
});
test("source primaire vide et lieu absent restent inconnus, jamais zéro",()=>{
 const r=run();
 assert.equal(r.dossiers[0].champs_baseline_manquants.includes("territoire"),true);
 assert.equal(r.dossiers[0].champs_baseline_manquants.includes("source_de_jeu_de_donnees_precis"),true);
 assert.equal(r.dossiers_avec_base_documentee_pour_revue,0);
});
test("aucun délai de fin n'est certifié par une bonne CI",()=>{
 const r=run();
 assert.equal(r.calendrier_de_fin_certifiable,false);
 assert.equal(r.controle_externe_hors_champ_de_ce_registre,true);
 assert.equal(r.maturite_non_mesuree_par_ce_registre,true);
});
