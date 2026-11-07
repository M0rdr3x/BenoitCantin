import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016bBenchmarks,EXPECTED_DECILE_UPPER_BOUNDS_CAD} from "../assets/g016b-public-benchmarks-core.mjs";

const base=new URL("../data/reperes-publics-g0-16b-2023.json",import.meta.url);
const source=JSON.parse(await readFile(base,"utf8"));
const g015=JSON.parse(await readFile(new URL("../data/matrice-preuves-g0-15-fiscalite.json",import.meta.url),"utf8"));
const g016=JSON.parse(await readFile(new URL("../data/plan-microsimulation-g0-16.json",import.meta.url),"utf8"));
const clone=()=>structuredClone(source);
const check=d=>inspectG016bBenchmarks(d,g015,g016);

test("deux références historiques et 47 % sans certification",()=>{
 const r=check(source);assert.equal(r.ok,true,r.errors.join(","));
 assert.equal(r.documentary_benchmarks,2);
 assert.equal(r.candidate_catalogues,2);
 assert.equal(r.can_calibrate,false);
 assert.equal(r.programme_percent,47);
 assert.equal(r.records_for_policy_simulation,0);
});
test("ISQ : neuf limites publiées en dollars ajustés, dixième non chiffrée",()=>{
 const d=source.datasets.household_decile_thresholds;
 assert.equal(d.reference_year,2023);
 assert.deepEqual(d.deciles.map(x=>x.upper_bound_cad),EXPECTED_DECILE_UPPER_BOUNDS_CAD);
 assert.equal(d.deciles[9].published_marker,"x");
 assert.equal(d.fit_for_tax_calibration,false);
});
test("revenu après impôt ajusté ≠ revenu imposable ni résultat Nova",()=>{
 const d=source.datasets.household_decile_thresholds;
 assert.equal(d.variable,"REVENU_APRES_IMPOT_AJUSTE_TAILLE_MENAGE");
 assert.equal(d.unit,"CAD_COURANTS_2023_PAR_EQUIVALENT_MENAGE");
 assert.equal(source.measurement_limits.not_2026_tax_base,true);
});
test("StatCan : moyenne Québec 2023 sans fausse ventilation par décile",()=>{
 const e=source.datasets.household_spending_provincial;
 assert.equal(e.average_spending_cad,65344);
 assert.deepEqual(e.shares_pct,{housing:27.1,transport:16.9,food:17.3});
 assert.equal(e.by_income_decile,false);
 assert.equal(source.measurement_limits.do_not_join_income_and_spending_by_decile,true);
});
test("une limite ISQ inventée rend le dossier invalide",()=>{
 const d=clone();d.datasets.household_decile_thresholds.deciles[0].upper_bound_cad=99999;
 assert.ok(check(d).errors.includes("ISQ_DECILE:1"));
});
test("la case non publiée du dernier décile reste null",()=>{
 const d=clone();d.datasets.household_decile_thresholds.deciles[9].upper_bound_cad=150000;
 assert.ok(check(d).errors.includes("ISQ_DECILE:10"));
});
test("une colonne injectée dans le tableau est refusée",()=>{
 const d=clone();d.datasets.household_decile_thresholds.deciles[0].gain_nova=2000;
 assert.ok(check(d).errors.includes("ISQ_DECILE:1"));
});
test("source remplacée ou millésime actuel fictif refusé",()=>{
 const d=clone();d.datasets.household_decile_thresholds.source_url="https://example.org/data";
 assert.ok(check(d).errors.includes("ISQ_METADATA"));
 const x=clone();x.datasets.household_decile_thresholds.reference_year=2026;
 assert.ok(check(x).errors.includes("ISQ_METADATA"));
});
test("variation de pourcentage de dépenses non sourcée refusée",()=>{
 const d=clone();d.datasets.household_spending_provincial.shares_pct.housing=32.1;
 assert.ok(check(d).errors.includes("STATCAN_EXPENDITURES"));
});
test("interdiction de traiter moyenne provinciale comme moyenne de chaque décile",()=>{
 const d=clone();d.datasets.household_spending_provincial.by_income_decile=true;
 assert.ok(check(d).errors.includes("STATCAN_EXPENDITURES"));
});
test("catalogue fiscal n'est pas un classeur téléchargé",()=>{
 const d=clone();d.candidates[0].content_imported=true;
 assert.ok(check(d).errors.includes("CANDIDATE_CATALOGUES"));
});
test("pas d'impôt, de gain, de programme 48 % ou de budget fictifs",()=>{
 for(const mutate of [
  d=>{d.programme_percent=48},
  d=>{d.scenarios[0].proposed_tax_rate_pct=20},
  d=>{d.scenarios[1].annual_fiscal_balance_mcad=1000},
  d=>{d.decision.new_nova_savings_estimated=true},
  d=>{d.decision.g016b_calibration_complete=true}
 ]){
  const d=clone();mutate(d);assert.equal(check(d).ok,false);
 }
});
test("les préconditions G0.15 restent indépendantes",()=>{
 const v=structuredClone(g015);v.proofs.pop();
 assert.ok(inspectG016bBenchmarks(source,v,g016).errors.includes("PREDECESSOR_G015_MISMATCH"));
});
test("la matrice G0.16 ne peut se remplir avec les seuls tableaux descriptifs",()=>{
 const v=structuredClone(g016);v.scenarios[0].distribution[0].net_change_cad=400;
 assert.ok(inspectG016bBenchmarks(source,g015,v).errors.includes("PREDECESSOR_G016_MISMATCH"));
});
test("les sources ne contiennent aucun dossier personnel",()=>{
 assert.equal(source.individual_data_collected,false);
 assert.equal(source.source_spreadsheets_imported,false);
 assert.equal(source.approved_for_microsimulation,false);
});
