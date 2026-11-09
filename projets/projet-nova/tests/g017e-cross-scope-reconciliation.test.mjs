import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspecterConcordanceG017e,TEN_YEARS,EXPECTED_MUNICIPAL_IDS}
 from "../assets/g017e-cross-scope-reconciliation-core.mjs";
const load=async filename=>JSON.parse(await readFile(new URL("../data/"+filename,import.meta.url),"utf8"));
const [mun,forecast,budget,actual]=await Promise.all([
 load("g017c-recettes-municipales-2024-et-couts-eau-2023.json"),
 load("cadre-financier-fiscal-g0-16v-aout-2026.json"),
 load("cadre-financier-g0-13-2026-2036.json"),
 load("comptes-publics-reels-g0-15-v02-v03-2025-2026.json")
]);
const inspect=(c=mun,v=forecast,g=budget,a=actual)=>inspecterConcordanceG017e(c,v,g,a);
test("rapprochement : quatre sources, aucune certification Nova",()=>{
 const r=inspect();assert.equal(r.ok,true,r.errors.join(", "));
 assert.deepEqual(TEN_YEARS.slice(0,2),["2026-2027","2027-2028"]);
 assert.deepEqual(mun.municipal.components.map(x=>x.id),EXPECTED_MUNICIPAL_IDS);
 assert.equal(r.montant_net_taxes_nova_2026_mcad,null);
 assert.equal(r.rendement_anti_paradis_certifie_mcad,null);
 assert.equal(r.score_authorized_increment,0);
 assert.equal(r.validation_independante,false);
});
test("2024 : 31,3 G$ de recettes, 7,4 G$ de transferts, 23,9 G$ autres recettes",()=>{
 const r=inspect();assert.equal(r.municipales_2024_revenus_approximatifs_gcad,31.3);
 assert.equal(r.municipales_2024_transferts_gcad,7.4);
 assert.equal(r.municipales_2024_revenus_hors_transferts_approximatifs_gcad,23.9);
});
test("2024 : le foncier et les droits de mutation 16,3 G$ ne constituent pas le coût net 2026",()=>{
 const r=inspect();assert.equal(r.municipales_2024_foncier_et_mutation_exposes_si_abolis_gcad,16.3);
 assert.equal(r.foncier_et_mutation_2024_est_cout_net_2026,false);
 assert.equal(r.montant_2024_ajoutable_au_besoin_provincial_2026_mcad,null);
});
test("2023 : 3,6 G$ est un écart de coût complet et non un déficit de caisse",()=>{
 const r=inspect();assert.equal(r.eau_2023_ecart_couverture_cout_complet_gcad,3.6);
 assert.equal(r.eau_2023_est_deficit_tresorerie,false);
 assert.equal(r.eau_2023_est_additionnable_aux_recettes_2024,false);
});
test("2026–2031 : cinq seuils conditionnels recalculés sur les chiffres gouvernementaux",()=>{
 const p=inspect().budgets_provinciaux_officiels_previsions;
 assert.deepEqual(p.map(x=>x.provincial_levies_needed_conditionally_mcad),
  [112369,114162,114994,117225,121230]);
 assert.deepEqual(p.map(x=>x.provincial_levies_plus_generations_mcad),
  [114851,116663,117620,120015,124159]);
 assert.equal(inspect().annees_suivantes_sans_prevision_officielle,5);
 assert.ok(p.every(x=>x.scope==="PROVINCIAL_FORECAST_CONDITIONAL_NOT_NOVA"));
});
test("réalisations 2025–2026 : -5502 M$ sans fusion avec prévisions 2026–2027",()=>{
 assert.equal(inspect().comptabilite_reelle_2025_2026_resultat_mcad,-5502);
 assert.notEqual(inspect().budgets_provinciaux_officiels_previsions[0].provincial_levies_needed_conditionally_mcad,
 -5502);
});
test("une recette municipale gonflée est refusée",()=>{
 const c=structuredClone(mun);c.municipal.components[0].amount_gcad=16;
 assert.ok(inspect(c).errors.includes("AGREGATS_MUNICIPAUX_NON_HOMOLOGUES"));
});
test("suppression de l'interdiction des doubles comptes rejetée",()=>{
 const c=structuredClone(mun);
 c.controls.do_not_add_2024_municipal_to_2026_provincial_budget=false;
 assert.ok(inspect(c).errors.includes("REGLE_DE_PERIMETRE_MANQUANTE:do_not_add_2024_municipal_to_2026_provincial_budget"));
});
test("prévision provinciale manipulée ou déséquilibrée rejetée",()=>{
 const v=structuredClone(forecast);
 v.government_reference.fiscal_years_official[0].federal_transfers_mcad+=1;
 assert.ok(inspect(mun,v).errors.includes("CONCORDANCE_PROVINCIALE:2026-2027"));
});
test("futur hors source artificiellement rempli est rejeté",()=>{
 const b=structuredClone(budget);b.budget_reference[6].total_revenue=0;
 assert.ok(inspect(mun,forecast,b).errors.includes("INCONNU_SUBSTITUE_PAR_ZERO:2032-2033"));
});
test("coût eau fictivement abaissé ou transformé en déficit refusé",()=>{
 const c=structuredClone(mun);c.water.illustrative_gap_is_not_annual_cash_deficit=false;
 assert.ok(inspect(c).errors.includes("PERIMETRE_EAU_INVALIDE"));
});
test("une fausse réalisation est refusée",()=>{
 const a=structuredClone(actual);a.annual[1].total_revenues+=100;
 assert.ok(inspect(mun,forecast,budget,a).errors.includes("REALE_VS_PREVISION_CONFONDUS"));
});
test("entrées absentes rejetées sans exception",()=>{
 const r=inspect(null,null,null,null);
 assert.equal(r.ok,false);assert.equal(r.score_authorized_increment,0);
});
