import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {verifyFiscalReadiness,summarizeFiscalStatus} from "../assets/g13-fiscal-readiness-core.mjs";
const source=JSON.parse(await readFile(
 new URL("../data/cadre-financier-g0-13-2026-2036.json",import.meta.url),"utf8"));
const clone=()=>structuredClone(source);
test("cinq années gouvernementales et cinq années sans source",()=>{
 const r=verifyFiscalReadiness(source);
 assert.equal(r.ok,true,r.errors.join(","));
 assert.equal(r.official_years,5);
 assert.equal(r.unavailable_years,5);
});
test("dix ans distincts pour Québec Canada et Québec souverain",()=>{
 assert.equal(source.budget_reference.length,10);
 assert.equal(source.scenarios.length,2);
 assert.ok(source.scenarios.every(s=>s.annual.length===10));
});
test("2026-2027 : revenus 168389, dépenses 171597 et provision 2000 donnent -5208",()=>{
 const y=source.budget_reference[0];
 assert.equal(y.total_revenue,168389);
 assert.equal(y.total_expenditures,171597);
 assert.equal(y.contingency_reserve,2000);
 assert.equal(y.accounting_balance_before_gap,-5208);
 assert.equal(y.budgetary_balance_after_assumed_gap,-7690);
});
test("les recettes autonomes 2026-2027 et transferts se réconcilient",()=>{
 const x=source.five_year_income_components_2026_2027;
 assert.equal(x.own_revenue_total,135343);
 assert.equal(x.federal_transfers,33046);
 assert.equal(x.personal_income_tax,50942);
 assert.equal(x.own_revenue_total+x.federal_transfers,168389);
});
test("2028-2031: l'écart futur à résorber est conditionnel et non économie réalisée",()=>{
 for(const y of source.budget_reference.slice(2,5)){
   assert.equal(y.budget_balance_conditional_on_future_gap,true);
   assert.ok(y.gap_to_be_bridged>0);
 }
});
test("les années 2031-2036 restent inconnues",()=>{
 assert.ok(source.budget_reference.slice(5).every(y=>y.total_revenue===null&&
  y.total_expenditures===null&&y.budgetary_balance_after_assumed_gap===null));
});
test("le budget Nova n'est calculé pour aucun des deux scénarios",()=>{
 assert.ok(source.scenarios.every(s=>s.annual.every(y=>y.net_budgetary_balance===null)));
 assert.equal(summarizeFiscalStatus(source).nova_proposed_balance,null);
});
test("un million inventé de recettes d'évasion est rejeté",()=>{
 const d=clone();d.tax_policy.anti_tax_haven_collectible_yield=1000;
 assert.equal(verifyFiscalReadiness(d).ok,false);
});
test("un revenu de transfert fictif est détecté",()=>{
 const d=clone();d.budget_reference[0].federal_transfers+=1500;
 assert.ok(verifyFiscalReadiness(d).errors.includes("OFFICIAL_ARITHMETIC:0"));
});
test("le déficit prévu ne devient pas faussement un surplus",()=>{
 const d=clone();d.budget_reference[0].accounting_balance_before_gap=5208;
 assert.equal(verifyFiscalReadiness(d).ok,false);
});
test("une année 2034-2035 inventée est refusée",()=>{
 const d=clone();d.budget_reference[8].total_revenue=200000;
 assert.ok(verifyFiscalReadiness(d).errors.includes("UNSOURCED_YEARS_NOT_NULL:8"));
});
test("les deux scénarios ne peuvent être fusionnés",()=>{
 const d=clone();d.scenarios[1].id="QUEBEC_CANADA";
 assert.equal(verifyFiscalReadiness(d).ok,false);
});
test("aucune recette ou dépense souveraine ne peut être validée sans étude",()=>{
 const d=clone();d.scenarios[1].annual[0].debt_and_asset_allocation=0;
 assert.ok(verifyFiscalReadiness(d).errors.some(x=>x.startsWith("UNPROVEN_SOVEREIGN_ASSUMPTIONS")));
});
test("aucune recette d'impôt générale Nova n'est supposée",()=>{
 const d=clone();d.scenarios[0].annual[0].nova_income_tax_revenue=100000;
 assert.equal(verifyFiscalReadiness(d).ok,false);
});
test("la progression du programme n'augmente pas par simple création de fichiers",()=>{
 const r=verifyFiscalReadiness(source);
 assert.equal(r.progress_percent,47);
 assert.equal(source.blocking_gates.programme_progress_percent_after,47);
 assert.equal(r.fiscal_plan_certified,false);
});
test("une approbation financière artificielle est bloquée",()=>{
 const d=clone();d.blocking_gates.fiscal_plan_certified=true;
 assert.ok(verifyFiscalReadiness(d).errors.includes("FALSE_COMPLETION_OR_AUTHORIZATION"));
});
