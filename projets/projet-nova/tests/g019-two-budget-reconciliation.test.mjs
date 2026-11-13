import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {analyserG019,EXERCICES_G019} from "../assets/g019-two-budget-reconciliation-core.mjs";
const root=new URL("../",import.meta.url);
async function get(path){return JSON.parse(await readFile(new URL(path,root),"utf8"));}
const original={
 audit:await get("data/audit-completude-programme-nova-2026-11-05.json"),
 assiettes:await get("data/registre-assiettes-fiscales-g0-14-2026-2027.json"),
 prevision:await get("data/cadre-financier-fiscal-g0-16v-aout-2026.json"),
 consolide:await get("data/g016z-financement-consolide-et-protections-2026-2036.json"),
 comptes:await get("data/comptes-publics-reels-g0-15-v02-v03-2025-2026.json"),
 municipal:await get("data/g017c-recettes-municipales-2024-et-couts-eau-2023.json"),
 cadre:await get("data/cadre-financier-g0-13-2026-2036.json")
};
const check=x=>analyserG019(x??original);
const change=()=>structuredClone(original);
test("reconciliation G0.19 des sept sources sans aucune valeur Nova inventee",()=>{
 const r=check();
 assert.equal(r.ok,true,r.errors.join("; "));
 assert.equal(r.audited_score,47);
 assert.equal(r.finance_dimension_points,3);
 assert.equal(r.pret_a_adopter,false);
 assert.equal(r.conclusion,"NO_GO_ETUDE_NON_ADOPTEE");
});
test("2026-2027: 168389 M recettes, 171597 M charges et 2000 M réserve gouvernementale",()=>{
 const r=check();
 assert.deepEqual(r.government_baseline_2026_27,{
  revenue_mcad:168389,expenditure_mcad:171597,receipts_in_current_tax_categories_mcad:107161,
  other_receipts_assumed_mcad:28182,federal_transfers_forecast_mcad:33046});
});
test("pont mecanique 2026-27 sans taux d'impot Nova ni promesse d'economies",()=>{
 const r=check();
 assert.deepEqual(r.frozen_mechanical_stresses_only,{
 three_categories_at_risk_mcad:41521,
 remaining_adjustment_including_existing_deficit_mcad:49211,
 required_conditional_levies_for_accounting_balance_mcad:112369,
 required_conditional_levies_including_generations_mcad:114851,
 without_federal_transfers_same_provincial_costs_mcad:145415});
 assert.equal(r.nova_tax_base_certified,false);
 assert.equal(r.nova_haven_incremental_revenue_certified,false);
});
test("10 exercices par scenario, 5 projections gouvernementales disponibles seulement",()=>{
 const r=check();
 assert.equal(EXERCICES_G019.length,10);
 assert.equal(r.official_forecast_years,5);
 assert.equal(r.total_planning_years_per_scenario,10);
 assert.equal(r.unsupported_nova_scenario_years,20);
 assert.equal(r.five_forecast_rows.length,10);
 for(let i=0;i<5;i++){
  assert.equal(r.five_forecast_rows[i].fiscal_reference_available,true);
  assert.equal(r.five_forecast_rows[i].real_nova_balance_mcad,null);
 }
 for(let i=5;i<10;i++){
  assert.equal(r.five_forecast_rows[i].fiscal_reference_available,false);
  assert.equal(r.five_forecast_rows[i].conditional_provincial_levies_mcad,null);
 }
});
test("Québec souverain: transferts fédéraux non automatiquement reconduits",()=>{
 assert.equal(original.prevision.scenarios[1].future_transfer_treatment,
 "DO_NOT_AUTOMATICALLY_PRESUME_FEDERAL_TRANSFERS");
 assert.equal(original.assiettes.constitutional_scenarios[1].baseline_federal_transfers_2026_2027,null);
 assert.equal(check().pret_a_adopter,false);
});
test("comptes 2025-2026 reels DISTINCTS de la prévision 2026-2027",()=>{
 const r=check();
 assert.equal(r.actual_2025_26_accounting_balance_mcad,-5502);
 assert.equal(original.comptes.annual[1].total_revenues,160428);
 assert.equal(original.comptes.annual[1].total_expenditures,165930);
});
test("ressources municipales 2024 et coût complet d'eau 2023 non additionnables",()=>{
 const r=check();
 assert.equal(r.municipal_2024_revenues_gcad,31.3);
 assert.equal(r.water_2023_full_cost_shortfall_not_cash_deficit_gcad,3.6);
 assert.equal(r.municipal_transfer_netting_completed,false);
});
test("refuser le gonflement d'une categorie de recettes",()=>{
 const x=change();x.assiettes.revenue_categories[0].amount_mcad+=9000;
 assert.ok(check(x).errors.includes("2026_BILAN_GOUVERNEMENTAL_INCOHERENT"));
});
test("refuser la suppression de la réserve et une balance fictive",()=>{
 const x=change();x.assiettes.baseline.contingency_reserve=0;
 assert.ok(check(x).errors.includes("2026_BILAN_GOUVERNEMENTAL_INCOHERENT"));
 const y=change();y.assiettes.baseline.accounting_balance=0;
 assert.ok(check(y).errors.includes("2026_BILAN_GOUVERNEMENTAL_INCOHERENT"));
});
test("refuser un changement de transferts sans rapprochement financier",()=>{
 const x=change();x.prevision.government_reference.fiscal_years_official[1].federal_transfers_mcad=0;
 assert.ok(check(x).errors.includes("REFERENCE_ANNUELLE_NON_RECONCILIEE:2027-2028"));
});
test("ne pas maquiller les cinq dernieres annees en projections officielles",()=>{
 const x=change();x.consolide.official_reference_series[5].provincial_revenue_mcad=199999;
 assert.ok(check(x).errors.includes("PROJECTION_2031_2036_INVENTEE:2031-2032"));
});
test("refuser un solde budgétaire Nova non audité dans les deux contextes",()=>{
 const x=change();x.consolide.scenario_years[0].years[0].net_real_public_balance_mcad=10;
 assert.ok(check(x).errors.includes("SCENARIO_NOVA_NON_ETAYE:QUEBEC_CANADA:2026-2027"));
 const y=change();y.prevision.scenarios[1].years[9].nova_annual_balance_mcad=42;
 assert.ok(check(y).errors.includes("SCENARIO_NOVA_NON_ETAYE:QUEBEC_SOUVERAIN:2035-2036"));
});
test("refuser un taux invente ou un revenu anti-paradis fiscaux certifié",()=>{
 const x=change();x.assiettes.tax_design_constraints.income_tax_rate_percent=28;
 assert.ok(check(x).errors.includes("DECLARATION_TAUX_OU_BUDGET_NON_PROUVEE"));
 const y=change();y.assiettes.tax_design_constraints.offshore_revenue_incremental_after_overlap=8000;
 assert.ok(check(y).errors.includes("DECLARATION_TAUX_OU_BUDGET_NON_PROUVEE"));
});
test("refuser la confusion année municipale et année provinciale",()=>{
 const x=change();x.municipal.municipal.year=2026;
 assert.ok(check(x).errors.includes("MUNICIPAL_EAU_DOUBLE_COMPTAGE"));
 const y=change();y.municipal.water.illustrative_gap_is_not_annual_cash_deficit=false;
 assert.ok(check(y).errors.includes("MUNICIPAL_EAU_DOUBLE_COMPTAGE"));
});
test("ne jamais convertir un contrôle CI réussi en homologation financière",()=>{
 const x=change();x.consolide.decision.ten_year_canada_balance_verified=true;
 assert.ok(check(x).errors.includes("DECLARATION_TAUX_OU_BUDGET_NON_PROUVEE"));
 const y=change();y.audit.scoring.earned=100;
 assert.ok(check(y).errors.includes("AUDIT_SOURCE_MISMATCH"));
});
test("refuser une source essentielle absente",()=>{
 assert.equal(analyserG019(null).ok,false);
 const x=change();delete x.municipal;
 assert.ok(analyserG019(x).errors.includes("SOURCES_ABSENTES"));
});
