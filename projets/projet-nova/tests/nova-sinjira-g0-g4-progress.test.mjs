import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {analyserPortesNovaSinjira,STAGES}
 from "../assets/nova-sinjira-g0-g4-progress-core.mjs";
const load=async path=>readFile(new URL("../"+path,import.meta.url),"utf8");
const [matrix,source,audit,protocol]=await Promise.all([
 load("data/matrice-avancement-nova-sinjira-g0-g4-2026-11-08.json").then(JSON.parse),
 load("data/registre-donnees-services-nova-sinjira.json").then(JSON.parse),
 load("data/audit-completude-programme-nova-2026-11-05.json").then(JSON.parse),
 load("official/working/plan-execution-nova-sinjira-v1.md")
]);
const check=(m=matrix,s=source,a=audit,p=protocol)=>analyserPortesNovaSinjira(m,s,a,p);
const copy=structuredClone;
test("G0–G4 : 14 dossiers, 70 portes explicites, aucune attestation inventée",()=>{
 const r=check();
 assert.equal(r.ok,true,r.errors.join(", "));
 assert.equal(r.nombre_dossiers_de_travail,14);
 assert.equal(r.nombre_portes_g0_g4_attendues,70);
 assert.equal(r.nombre_portes_structurellement_controlees,70);
 assert.equal(r.nombre_portes_attestees_au_releve,0);
});
test("0/70 validations attestées ne veut PAS dire que le programme est rédigé à zéro",()=>{
 const r=check();
 assert.equal(r.pourcentage_achevement_autonome,null);
 assert.equal(r.couverture_des_portes_attestees_pct,0);
 assert.equal(r.controle_documentaire_seul,true);
 assert.equal(r.gain_de_points_Nova,0);
 assert.equal(audit.scoring.earned,47);
});
test("source sectorielle : 14 IDs, comparateurs et domaines correctement conservés",()=>{
 assert.deepEqual(matrix.sectors.map(x=>x.id),source.dossiers.map(x=>x.id));
 assert.equal(matrix.sectors[2].title,"Santé première ligne");
 assert.deepEqual(matrix.sectors[2].stages.map(x=>x.id),STAGES);
 assert.equal(check().ok,true);
});
test("les bases de données partielles en santé ne sont pas homologuées",()=>{
 const r=matrix.sectors[2];
 assert.match(r.stage_work_notes,/partiel/);
 assert.equal(r.source_data_quality_confirmed,false);
 assert.equal(r.source_primary_dataset_reference,null);
 assert.equal(r.stages[0].status,"NON_ATTESTE");
});
test("aucune date de fin, de pilote ni de généralisation par le seul outil",()=>{
 const r=check();
 assert.equal(r.date_de_fin_attestee,null);
 assert.equal(r.autorisation_de_pilote,false);
 assert.equal(matrix.target_completion_date,null);
 assert.equal(matrix.completion_certified,false);
 assert.equal(matrix.adoptable_or_implementable,false);
});
test("les deux contextes constitutionnels doivent rester séparés",()=>{
 assert.deepEqual(matrix.contextes_a_etudier,["QUEBEC_DANS_LE_CANADA","QUEBEC_SOUVERAIN_HYPOTHETIQUE"]);
 const m=copy(matrix);m.contexts_financially_or_legally_certified=true;
 assert.ok(check(m).errors.includes("CONTEXTES_JURIDIQUES_CONFONDUS"));
});
test("inventer une preuve, un avis externe ou une décision crée une anomalie",()=>{
 for(const key of ["evidence_url","independent_review_url","competent_decision_url"]){
  const m=copy(matrix);m.sectors[0].stages[0][key]="https://exemple.invalid/"+key;
  assert.ok(check(m).errors.includes("PORTE_FAUSSEMENT_ATTESTEE:NV-01:G0"));
 }
});
test("modifier le statut G0 en attesté sans examen humain est refusé",()=>{
 const m=copy(matrix);m.sectors[2].stages[0].status="ATTESTE";
 assert.ok(check(m).errors.includes("PORTE_FAUSSEMENT_ATTESTEE:NV-03:G0"));
});
test("une fiche manquante ou dupliquée est refusée",()=>{
 const a=copy(matrix);a.sectors.pop();
 assert.ok(check(a).errors.includes("DOSSIERS_ABSENTS_OU_DUPLIQUES"));
 const b=copy(matrix);b.sectors[1].id="NV-01";
 assert.ok(check(b).errors.includes("DOSSIERS_ABSENTS_OU_DUPLIQUES"));
});
test("supprimer une porte, inverser G0/G1 ou annoncer 1/70 est refusé",()=>{
 const a=copy(matrix);a.sectors[0].stages.pop();
 assert.ok(check(a).errors.includes("ETAPES_INCOMPLETES:NV-01"));
 const b=copy(matrix);b.sectors[0].stages[0].id="G1";
 assert.ok(check(b).errors.includes("PORTE_FAUSSEMENT_ATTESTEE:NV-01:G0"));
 const c=copy(matrix);c.verified_stage_acceptance_gates=1;
 assert.ok(check(c).errors.includes("COMPTAGE_CERTIFICATIONS_NON_ATTESTEES"));
});
test("changer discrètement les coûts ou le financement dans la copie est refusé",()=>{
 const m=copy(matrix);m.sectors[0].source_financing_confirmed=true;
 assert.ok(check(m).errors.includes("DOSSIER_SOURCE_DIVERGENT:NV-01"));
 const d=copy(source);d.dossiers[0].chiffrage_valide=true;
 assert.ok(check(matrix,d).errors.includes("DOSSIER_SOURCE_DIVERGENT:NV-01"));
});
test("les coûts des 14 dossiers Nova restent non certifiés par cette grille",()=>{
 const a=copy(audit);a.scoring.earned=100;
 assert.ok(check(matrix,source,a).errors.includes("AUDIT_NOVA_CHANGE"));
 const b=copy(audit);b.sector_register[0].independent_validation_confirmed=true;
 assert.ok(check(matrix,source,b).errors.includes("AUDIT_NOVA_CHANGE"));
});
test("une définition G2 sans protection des salariés est refusée",()=>{
 const m=copy(matrix);
 m.definitions[2].required_artifacts=m.definitions[2].required_artifacts.filter(x=>x!=="protection_des_travailleurs_et_droits");
 assert.ok(check(m).errors.includes("DEFINITION_DES_PORTES"));
});
test("un texte de protocole incomplet bloque le contrôle de conformité",()=>{
 const bad=protocol.replace("G4 : généralisation","G4 : autre");
 assert.ok(check(matrix,source,audit,bad).errors.includes("PROTOCOLE_G0_G4_NON_ALIGNE"));
});
test("un pourcentage autonome arbitraire est refusé",()=>{
 const m=copy(matrix);m.independent_programme_completion_percent=60;
 assert.ok(check(m).errors.includes("CERTIFICATION_INVENTEE"));
 const n=copy(matrix);n.programme_completion_percent=60;
 assert.ok(check(n).errors.includes("CERTIFICATION_INVENTEE"));
});
test("une entrée absente bloque le calcul sans aucun effet de production",()=>{
 assert.equal(check(null).ok,false);
 const r=check(matrix,source,audit,null);
 assert.equal(r.ok,false);assert.equal(r.autorisation_de_pilote,false);
});
