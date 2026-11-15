import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {assessG016Preflight} from "../assets/g016-microsimulation-gate-core.mjs";
const manifest=JSON.parse(await readFile(new URL(
 "../data/matrice-preuves-g0-15-fiscalite.json",import.meta.url),"utf8"));
const audit=JSON.parse(await readFile(new URL(
 "../data/audit-completude-programme-nova-2026-11-05.json",import.meta.url),"utf8"));
const copy=()=>structuredClone(manifest);
test("47/100 reste le score : les 15 preuves G0.15 manquent",()=>{
 const x=assessG016Preflight(manifest,audit);
 assert.equal(x.valid,true,x.errors.join(","));
 assert.equal(x.programme_percent,47);
 assert.equal(x.required,15);assert.equal(x.documented,0);
 assert.equal(x.missing.length,15);assert.equal(x.stage,"EVIDENCE_MISSING");
 assert.equal(x.simulation_authorized,false);
});
test("l'inventaire ne tolère pas la disparition d'une preuve",()=>{
 const d=copy();d.proofs.pop();
 assert.ok(assessG016Preflight(d,audit).errors.includes("PROOF_INVENTORY_CHANGED"));
});
test("une preuve dupliquée n'augmente pas artificiellement la couverture",()=>{
 const d=copy();d.proofs[1].id="V01";
 assert.ok(assessG016Preflight(d,audit).errors.includes("PROOF_INVENTORY_CHANGED"));
});
test("le groupe fiscal de chaque preuve est obligatoire",()=>{
 const d=copy();d.proofs[0].group="BUDGET";
 assert.ok(assessG016Preflight(d,audit).errors.includes("PROOF_INVENTORY_CHANGED"));
});
test("une revue déclarée sans pièce primaire ne devient pas acquise",()=>{
 const d=copy();d.proofs[0].status="REVUE_INDEPENDANTE";
 d.proofs[0].reviewed_independently=true;
 assert.equal(assessG016Preflight(d,audit).documented,0);
 assert.ok(assessG016Preflight(d,audit).errors.includes("UNSUPPORTED_INDEPENDENT_REVIEW:V01"));
});
test("un lien de preuve HTTP ou avec identifiants ne peut être validé",()=>{
 for(const bad of ["http://example.org/preuve","https://identifiant:secret@example.org/doc","javascript:alert(1)"]){
  const d=copy(),p=d.proofs[0];
  Object.assign(p,{status:"REVUE_INDEPENDANTE",reviewed_independently:true,
    primary_source:bad,year:2026,document_ref:"preuve-archivée-2026"});
  assert.ok(assessG016Preflight(d,audit).errors.includes("UNSUPPORTED_INDEPENDENT_REVIEW:V01"));
 }
});
test("les montants négatifs ou NaN sont rejetés",()=>{
 const d=copy();d.proofs[0].amount_mcad=-1;
 assert.ok(assessG016Preflight(d,audit).errors.includes("INVALID_PROOF:V01"));
 d.proofs[0].amount_mcad=NaN;
 assert.ok(assessG016Preflight(d,audit).errors.includes("INVALID_PROOF:V01"));
});
test("aucune modification des recettes officielles de référence",()=>{
 const d=copy();d.source_baseline_2026_2027.federal_transfers_mcad=0;
 assert.ok(assessG016Preflight(d,audit).errors.includes("OFFICIAL_BASELINE_CHANGED"));
});
test("une certification ou un taux improvisé n'est jamais autorisé",()=>{
 for(const key of ["rates_authorized","programme_certified","transition_authorized"]){
  const d=copy();d.decision[key]=true;
  assert.ok(assessG016Preflight(d,audit).errors.includes("PREMATURE_FISCAL_OR_LEGAL_APPROVAL"));
 }
 const d=copy();d.nova_tax_rate_percent=20;
 assert.ok(assessG016Preflight(d,audit).errors.includes("PREMATURE_FISCAL_OR_LEGAL_APPROVAL"));
});
test("un faux changement à 48 % est rejeté",()=>{
 const d=structuredClone(audit);d.scoring.earned=48;
 assert.ok(assessG016Preflight(manifest,d).errors.includes("PROGRAMME_SCORE_UNVERIFIED"));
});
test("même 15 revues déclarées ne valent pas approbation de réforme",()=>{
 const d=copy();
 d.proofs.forEach((p,i)=>Object.assign(p,{status:"REVUE_INDEPENDANTE",
  primary_source:"https://example.org/reference-"+i,
  year:2026,document_ref:"preuve-archivée-"+i,reviewed_independently:true}));
 const x=assessG016Preflight(d,audit);
 assert.equal(x.valid,true,x.errors.join(","));
 assert.equal(x.documented,15);
 assert.equal(x.stage,"EXTERNAL_APPROVAL_REQUIRED");
 assert.equal(x.simulation_authorized,false);
 assert.equal(x.new_tax_rate_authorized,false);
 assert.equal(x.government_budget_approved,false);
});
test("la page publique reproduit les chiffres de la grille, sans fausse certification",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/47 points attribués sur 100/);
 assert.match(html,/id="precontrole-g016"/);
 assert.match(html,/0 sur 15 preuves fiscales/);
 assert.match(html,/microsimulation non autorisée/i);
 assert.match(html,/47 % reste inchangé/i);
});
