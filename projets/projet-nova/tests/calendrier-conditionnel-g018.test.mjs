import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspecterCalendrier,MILESTONES} from "../assets/calendrier-conditionnel-g018-core.mjs";
import {inspectNOVACompletionGate} from "../assets/closure-gate-programme-core.mjs";
const load=async f=>JSON.parse(await readFile(new URL("../data/"+f,import.meta.url),"utf8"));
const [plan,audit,g15,g13,g16e]=await Promise.all([
 load("calendrier-conditionnel-g018-2026-11-08.json"),
 load("audit-completude-programme-nova-2026-11-05.json"),
 load("matrice-preuves-g0-15-fiscalite.json"),
 load("cadre-financier-g0-13-2026-2036.json"),
 load("pont-financier-g0-16e-2021-2026.json")
]);
const closure=inspectNOVACompletionGate(audit,g15,g13,g16e);
const inspect=(p=plan,a=audit,c=closure)=>inspecterCalendrier(p,a,c);
test("G0.18 : 47/100, 53 manquants, cible non certifiée",()=>{
 const r=inspect();assert.equal(r.ok,true,r.erreurs.join(","));
 assert.equal(r.score_reference,47);assert.equal(r.date_cible_de_planification,"2027-12-31");
 assert.equal(r.cible_garantie,false);assert.equal(r.date_de_fin_certifiee,null);
 assert.equal(r.fin_de_programme_certifiee,false);
 assert.equal(closure.gates_passed,0);assert.equal(closure.gates_total,7);
});
test("7 jalons uniques, aucune personne, preuve ni décision inventée",()=>{
 assert.deepEqual(plan.milestones.map(x=>x.id),MILESTONES);
 assert.equal(inspect().jalons_attestes_par_declaration,0);
 assert.deepEqual(inspect().prochaines_dependances,["M01"]);
 for(const x of plan.milestones){
  assert.equal(x.owner_real_name,null);assert.equal(x.completion_date,null);
  assert.equal(x.budget_authorized,null);assert.deepEqual(x.proof_urls,[]);
 }
});
test("75% rédactionnel n'est pas le score global",()=>{
 assert.equal(plan.documentation_maturity_estimate_percent,75);
 assert.equal(plan.documentation_maturity_is_certification,false);
 assert.equal(plan.programme_completion_score,47);
});
test("une date devenue garantie est rejetée",()=>{
 const p=structuredClone(plan);p.target_is_binding=true;
 assert.ok(inspect(p).erreurs.includes("DATE_CIBLE_PRESENTEE_COMME_PROMESSE"));
 p.target_is_binding=false;p.projected_completion_certified_date="2027-12-31";
 assert.ok(inspect(p).erreurs.includes("DATE_CIBLE_PRESENTEE_COMME_PROMESSE"));
});
test("une étape déclarée terminée sans mandat n'est pas reconnue",()=>{
 const p=structuredClone(plan);p.milestones[0].status="TERMINE_DECLARÉ";
 assert.ok(inspect(p).erreurs.includes("ATTESTATION_INCOMPLETE:M01"));
});
test("une preuve fictive sur M02 ne contourne pas M01",()=>{
 const p=structuredClone(plan),m=p.milestones[1];
 m.status="TERMINE_DECLARÉ";m.owner_real_name="Réviseur de test";
 m.owner_mandate_reference="https://exemple.invalid/mandat";
 m.budget_authorized=true;m.completion_date="2027-03-30";
 m.proof_urls=["https://exemple.invalid/preuve"];
 m.reviewer_independence_verified=true;m.decision_by_competent_body=true;
 assert.ok(inspect(p).erreurs.includes("DEPENDANCE_NON_TERMINEE:M02"));
 assert.equal(inspect(p).fin_de_programme_certifiee,false);
});
test("inversion de date et duplicata sont refusés",()=>{
 const p=structuredClone(plan);p.milestones[1].target_date="2026-01-01";
 assert.ok(inspect(p).erreurs.includes("DEPENDANCES_INCOHERENTES:M02"));
 const q=structuredClone(plan);q.milestones[1].id="M01";
 assert.ok(inspect(q).erreurs.includes("JALONS_INCORRECTS"));
});
test("score manipulé et faux audit G0.17 sont rejetés",()=>{
 const a=structuredClone(audit);a.scoring.earned=100;
 assert.ok(inspect(plan,a).erreurs.includes("AUDIT_SOURCE_DIFFERENT"));
 assert.ok(inspect(plan,audit,{...closure,checked_score:100}).erreurs.includes("PORTES_DE_CLOTURE_INCOHERENTES"));
});
test("dates impossibles et fausses décisions sont rejetées",()=>{
 const p=structuredClone(plan);p.milestones[2].target_date="2027-02-30";
 assert.ok(inspect(p).erreurs.includes("JALON_MALFORME:M03"));
 const q=structuredClone(plan);q.milestones[2].decision_by_competent_body=true;
 assert.ok(inspect(q).erreurs.includes("FAUSSE_DECISION:M03"));
 assert.equal(inspect(null).ok,false);
});
