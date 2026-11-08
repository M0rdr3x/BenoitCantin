import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {verifyG14} from "../assets/g14-fiscal-assiettes-core.mjs";
const reg=JSON.parse(await readFile(new URL("../data/registre-assiettes-fiscales-g0-14-2026-2027.json",import.meta.url),"utf8"));
const g13=JSON.parse(await readFile(new URL("../data/cadre-financier-g0-13-2026-2036.json",import.meta.url),"utf8"));
const clone=()=>structuredClone(reg);
test("9 catégories se réconcilient avec 168389 M$ et 135343 M$ autonomes",()=>{
 const x=verifyG14(reg,g13);assert.equal(x.ok,true,x.errors.join(","));
 assert.equal(x.amount_reconciled,168389);
 assert.equal(reg.baseline.own_source_revenue,135343);
});
test("le stress de 3 lignes signale une exposition de 41521 M$",()=>{
 const x=verifyG14(reg,g13);
 assert.equal(x.exposure_mcad,41521);
 assert.equal(x.mechanical_gap_to_zero_mcad,49211);
 assert.equal(reg.mechanical_sensitivity.mechanical_budgetary_balance_without_replacement,-49211);
});
test("le stress n'est pas un budget Nova",()=>{
 const x=verifyG14(reg,g13);
 assert.equal(x.proposal_funded,false);assert.equal(x.g0_passed,false);
 assert.equal(reg.mechanical_sensitivity.forecast_balance_nova,null);
 assert.equal(reg.programme_percent_after,47);
});
test("les recettes de paradis fiscaux restent inconnues",()=>{
 assert.equal(reg.tax_design_constraints.offshore_revenue_incremental_after_overlap,null);
 assert.equal(reg.constitutional_scenarios[0].net_anti_haven_revenue,null);
 assert.equal(reg.constitutional_scenarios[1].net_anti_haven_revenue,null);
});
test("un montant inventé dans la ligne de consommation est détecté",()=>{
 const d=clone();d.revenue_categories.find(x=>x.id==="TAXES_CONSOMMATION").amount_mcad=20000;
 assert.ok(verifyG14(d,g13).errors.includes("BASELINE_MAPPING"));
});
test("un nouveau rendement d'évasion pris comme certain est refusé",()=>{
 const d=clone();d.tax_design_constraints.offshore_revenue_incremental_after_overlap=10000;
 assert.ok(verifyG14(d,g13).errors.includes("UNVERIFIED_CLAIMS"));
});
test("une taxe municipale ne devient pas une recette provinciale",()=>{
 const d=clone();d.jurisdiction_separation.find(x=>x.id==="MUNICIPAL_TAXES").amount_mcad=900;
 assert.ok(verifyG14(d,g13).errors.includes("COMPETENCE"));
});
test("les transferts fédéraux ne sont pas garantis en souveraineté",()=>{
 const d=clone();d.constitutional_scenarios.find(x=>x.id==="QUEBEC_SOUVERAIN").baseline_federal_transfers_2026_2027=33046;
 assert.ok(verifyG14(d,g13).errors.includes("COMPETENCE"));
});
test("un changement silencieux des lignes supprimées est refusé",()=>{
 const d=clone();d.mechanical_sensitivity.removed_category_ids=["TAXES_CONSOMMATION","FONCIER_SCOLAIRE","REVENUS_DIVERS"];
 assert.ok(verifyG14(d,g13).errors.includes("EXPOSURE_SCOPE_ALTERED"));
});
test("des taux de prélèvements annoncés avant étude sont refusés",()=>{
 const d=clone();d.tax_design_constraints.income_tax_rate_percent=19;
 assert.ok(verifyG14(d,g13).errors.includes("UNVERIFIED_CLAIMS"));
});
test("une certification d'impôt offshore inventée est refusée",()=>{
 const d=clone();d.decision.anti_tax_haven_yield_certified=true;
 assert.ok(verifyG14(d,g13).errors.includes("PREMATURE_LEGAL_OR_FISCAL_CLAIMS"));
});
test("l'assiette des revenus ne se déduit pas des impôts de sociétés",()=>{
 const d=clone();d.reconciliation.income_tax_legal_base_defined=true;
 assert.ok(verifyG14(d,g13).errors.includes("MISCLASSIFIED_INCOME_BASE"));
});
test("les obligations RRQ et RQAP restent dans la liste hors comptabilité",()=>{
 const ids=reg.jurisdiction_separation.map(x=>x.id);
 assert.ok(ids.includes("RRQ")&&ids.includes("RQAP"));
 assert.ok(ids.includes("MUNICIPAL_TAXES")&&ids.includes("FEDERAL_TAXES"));
});
test("les deux contextes constitutionnels sont préservés",()=>{
 const ids=reg.constitutional_scenarios.map(x=>x.id).sort();
 assert.deepEqual(ids,["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
});
test("pas de passage automatique à 48 % ni de G0 franchie",()=>{
 const d=clone();d.programme_percent_after=48;
 assert.ok(verifyG14(d,g13).errors.includes("UNPROVEN_PROGRAMME_PROGRESS"));
 assert.equal(reg.decision.nova_budget_certified,false);
 assert.equal(reg.decision.g0_passed,false);
});
test("le maintien des services ne peut pas être déclaré démontré",()=>{
 const d=clone();d.mechanical_sensitivity.public_service_continuity_verified=true;
 assert.ok(verifyG14(d,g13).errors.includes("ILLUSTRATION_NOT_LABELED"));
});

test("le même montant ne permet pas de transformer les droits mixtes en impôt",()=>{
 const d=clone();
 d.revenue_categories.find(x=>x.id==="DROITS_PERMIS_REDEVANCES").fiscal_tax=true;
 const r=verifyG14(d,g13);
 assert.ok(r.errors.includes("UNSUPPORTED_REVENUE_CLASSIFICATION"),r.errors.join(","));
 assert.equal(reg.revenue_categories.find(x=>x.id==="DROITS_PERMIS_REDEVANCES").fiscal_tax,null);
});
test("des revenus divers non ventilés ne deviennent pas fiscalement libres",()=>{
 const d=clone();const row=d.revenue_categories.find(x=>x.id==="REVENUS_DIVERS");
 row.type="IMPOT_REVENU";
 row.potential_policy="CANDIDAT_REVENU_PERSONNES";
 assert.ok(verifyG14(d,g13).errors.includes("UNSUPPORTED_REVENUE_CLASSIFICATION"));
});
test("les dividendes des sociétés d'État ne sont pas un impôt nouveau",()=>{
 const d=clone();const row=d.revenue_categories.find(x=>x.id==="SOCIETES_ETAT");
 row.fiscal_tax=true;
 assert.ok(verifyG14(d,g13).errors.includes("UNSUPPORTED_REVENUE_CLASSIFICATION"));
});
test("les transferts fédéraux ne sont pas une taxe provinciale",()=>{
 const d=clone();const row=d.revenue_categories.find(x=>x.id==="TRANSFERTS_FEDERAUX");
 row.scope="PROVINCIAL";
 assert.ok(verifyG14(d,g13).errors.includes("UNSUPPORTED_REVENUE_CLASSIFICATION"));
});
test("la taxe scolaire reste juridiquement distinguée des recettes municipales",()=>{
 const d=clone();const row=d.revenue_categories.find(x=>x.id==="FONCIER_SCOLAIRE");
 row.scope="MUNICIPAL";
 assert.ok(verifyG14(d,g13).errors.includes("UNSUPPORTED_REVENUE_CLASSIFICATION"));
});
test("un changement de nature des cotisations santé sans preuve est rejeté",()=>{
 const d=clone();const row=d.revenue_categories.find(x=>x.id==="COTISATIONS_SANTE");
 row.type="IMPOT_REVENU";
 assert.ok(verifyG14(d,g13).errors.includes("UNSUPPORTED_REVENUE_CLASSIFICATION"));
});
test("même avec un total 168 389 M$ correct, le reclassement n'est pas validé",()=>{
 const d=clone();d.revenue_categories.find(x=>x.id==="TAXES_CONSOMMATION").fiscal_tax=false;
 const r=verifyG14(d,g13);
 assert.ok(!r.errors.includes("SOURCE_TOTALS"));
 assert.ok(!r.errors.includes("BASELINE_MAPPING"));
 assert.ok(r.errors.includes("UNSUPPORTED_REVENUE_CLASSIFICATION"));
 assert.equal(r.ok,false);
});
test("un registre malformé échoue proprement au lieu de contourner le contrôle",()=>{
 for(const prop of ["baseline","mechanical_sensitivity","tax_design_constraints",
   "decision","reconciliation","jurisdiction_separation","constitutional_scenarios"]){
  const d=clone();delete d[prop];
  const r=verifyG14(d,g13);
  assert.equal(r.ok,false,prop);
  assert.ok(r.errors.includes("SCHEMA"),prop);
 }
 const d=clone();d.revenue_categories[0]=null;
 assert.ok(verifyG14(d,g13).errors.includes("SCHEMA"));
});
