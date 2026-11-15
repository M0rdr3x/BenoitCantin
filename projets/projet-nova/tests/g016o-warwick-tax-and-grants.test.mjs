import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016oWarwickTaxes,calculateSyntheticWarwickPart} from "../assets/g016o-warwick-tax-core.mjs";
const read=async f=>JSON.parse(await readFile(new URL("../data/"+f,import.meta.url),"utf8"));
const [d,m,n]=await Promise.all([
 read("taxes-warwick-2026-et-preuves-versements-g0-16o.json"),
 read("cas-municipal-reel-g0-16m-warwick-eau-2025-2026.json"),
 read("comparatif-cas-reels-primeau-g0-16n-2025.json")
]);
const copy=x=>structuredClone(x);
const check=x=>inspectG016oWarwickTaxes(x,m,n);
const reject=(edit,label)=>{
 const x=copy(d);edit(x);const result=check(x);
 assert.equal(result.ok,false,result.errors.join(","));
 assert.ok(result.errors.includes(label),result.errors.join(","));
};
const synthetic=x=>calculateSyntheticWarwickPart({
mode:"SYNTHETIC_PARTIAL_EXAMPLE",approved_example:true,
assessed_value_cad:x,property_class:"RESIDUAL_RESIDENTIAL",
urban_waste_collection:true,one_unit:true,water_connected:true,sewer_connected:true});
test("données Warwick réelles et degré global toujours 47",()=>{
 const r=check(d);assert.equal(r.ok,true,r.errors.join(","));
 assert.equal(r.programme_score,47);
});
test("règlement 415 adopté et en vigueur en janvier 2026",()=>{
 assert.equal(d.sources[0].council_adopted,"2026-01-12");
 assert.equal(d.sources[0].entered_into_force,"2026-01-14");
});
test("10 taux publiés et 4 compensations, non 10 taxes obligatoires",()=>{
 assert.equal(d.observed_2026_tax_rules.tax_rates_cad_per_100_assessment.length,10);
 assert.equal(d.observed_2026_tax_rules.fixed_compensations_cad_per_unit.length,4);
 assert.equal(d.observed_2026_tax_rules.tax_rates_cad_per_100_assessment.filter(x=>x.mandatory_for_illustrative_residence).length,6);
});
test("taux général résidentiel 0,575 dollar pour cent dollars d'évaluation",()=>{
 assert.equal(d.observed_2026_tax_rules.tax_rates_cad_per_100_assessment[0].rate_cad_per_100,0.575);
});
test("taux sanitaires particuliers 0,101 seulement dans le secteur desservi",()=>{
 const s=d.observed_2026_tax_rules.tax_rates_cad_per_100_assessment.find(x=>x.id==="SPECIAL_SANITATION");
 assert.equal(s.rate_cad_per_100,0.101);
 assert.equal(s.mandatory_for_illustrative_residence,false);
});
test("on ne suppose pas que l'ancien règlement 404 de l'usine figure au taux 2026",()=>{
 assert.equal(d.observed_2026_tax_rules.new_plant_404_2025_specific_2026_tax_rate_cad_per_100,null);
 assert.equal(d.observed_2026_tax_rules.lack_of_named_404_rate_does_not_prove_zero_liability,true);
});
test("eau 102 dollars et égouts 31,25 par logement sous conditions",()=>{
 const f=d.observed_2026_tax_rules.fixed_compensations_cad_per_unit;
 assert.equal(f.find(x=>x.id==="WATER_RESIDENTIAL").amount_cad,102);
 assert.equal(f.find(x=>x.id==="SEWER_RESIDENTIAL").amount_cad,31.25);
});
test("déchets résidentiels 283 urbain contre 267 rural",()=>{
 const f=d.observed_2026_tax_rules.fixed_compensations_cad_per_unit;
 assert.equal(f.find(x=>x.id==="WASTE_URBAN").amount_cad,283);
 assert.equal(f.find(x=>x.id==="WASTE_RURAL").amount_cad,267);
});
test("exemple fictif 300000 dollars : six taux totalisent 0,6374 par 100",()=>{
 const r=synthetic(300000);
 assert.equal(r.property_tax_rate_sum_cad_per_100,0.6374);
 assert.equal(r.property_tax_subtotal_cad,1912.2);
});
test("exemple fictif : compensations 416,25 et sous-total 2328,45",()=>{
 const r=synthetic(300000);
 assert.equal(r.selected_fixed_services_subtotal_cad,416.25);
 assert.equal(r.partial_example_subtotal_cad,2328.45);
 assert.equal(r.actual_total_tax_bill_cad,null);
});
test("le sous-total n'inclut pas toute la fiscalité ou un gain Nova",()=>{
 const r=synthetic(300000);
 assert.equal(r.includes_all_special_tax_rates,false);
 assert.equal(r.real_tax_saving_nova_cad,null);
});
test("un rôle d'évaluation réel reste non identifié",()=>{
 assert.equal(d.synthetic_household_example.real_person_or_property,false);
 assert.equal(d.synthetic_household_example.source_for_2026_assessed_value,"SYNTHETIC_EXAMPLE_NO_ASSESSMENT_ROLL");
});
test("règle actuelle PRIMEAU : demandes partielles jusqu'à 90 pour cent",()=>{
 assert.equal(d.primeau_current_guide_rules.partial_claim_maximum_share_pct,90);
 assert.equal(d.primeau_current_guide_rules.partial_claim_limit_is_not_confirmed_paid_pct,true);
});
test("règle actuelle PRIMEAU : réclamations et factures exigées",()=>{
 assert.equal(d.primeau_current_guide_rules.final_claim_requires_cost_records_and_paid_invoices,true);
 assert.equal(d.primeau_current_guide_rules.initial_payment_only_if_agreement_so_provides,true);
});
test("retenue finale 10 pour cent n'est pas systématique à tous dossiers",()=>{
 assert.equal(d.primeau_current_guide_rules.ten_percent_holdback_applies_to_every_project,false);
});
test("convention historique Warwick requiert l'examen de son régime applicable",()=>{
 assert.equal(d.primeau_current_guide_rules.applicability_to_existing_2025_awards_requires_convention_review,true);
});
test("aucun versement individuel non sourcé n'est déclaré connu",()=>{
 assert.equal(d.decision.g016o_individual_grant_cash_verified,false);
 assert.ok(d.sample_cash_evidence.every(x=>x.status==="NOT_VERIFIED"));
});
test("deux budgets décennaux restent inconnus, pas des projections historiques",()=>{
 assert.deepEqual(d.ten_year_unfunded_scenarios.map(x=>x.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
 assert.ok(d.ten_year_unfunded_scenarios.every(x=>x.years.length===10));
 assert.ok(d.ten_year_unfunded_scenarios.every(x=>x.years.every(y=>y.net_budget_cad===null)));
});
test("taxe municipale par évaluation n'est pas impôt par revenu",()=>{
 assert.equal(d.fiscal_interpretation.tax_per_100_assessed_not_tax_per_100_income,true);
});
test("une source Warwick falsifiée est refusée",()=>{
 reject(x=>x.sources[0].url="https://example.com","ACTUAL_SOURCE_SCOPE");
});
test("taux résidentiel changé sans réglementation est refusé",()=>{
 reject(x=>x.observed_2026_tax_rules.tax_rates_cad_per_100_assessment[0].rate_cad_per_100=0.95,"TAX_RATES_WRONG_OR_UNJUSTIFIED");
});
test("taux dette du camion pompier changé est refusé",()=>{
 reject(x=>x.observed_2026_tax_rules.tax_rates_cad_per_100_assessment[2].rate_cad_per_100=0.8,"TAX_RATES_WRONG_OR_UNJUSTIFIED");
});
test("une taxe sectorielle devient à tort applicable partout : rejet",()=>{
 reject(x=>x.observed_2026_tax_rules.tax_rates_cad_per_100_assessment[6].mandatory_for_illustrative_residence=true,"TAX_RATES_WRONG_OR_UNJUSTIFIED");
});
test("un paiement réel sans justificatif est refusé",()=>{
 reject(x=>x.observed_2026_tax_rules.actual_bill_paid_for_a_specific_home_cad=2328.45,"ACTUAL_HOUSEHOLD_BILL_NOT_PROVEN");
});
test("une taxe de la nouvelle usine ne peut être inventée",()=>{
 reject(x=>x.observed_2026_tax_rules.new_plant_404_2025_specific_2026_tax_rate_cad_per_100=0.1,"ACTUAL_HOUSEHOLD_BILL_NOT_PROVEN");
});
test("retirer la prudence sur les autres règlements invalide le fichier",()=>{
 reject(x=>x.observed_2026_tax_rules.other_municipal_by_laws_may_create_additional_charges=false,"ACTUAL_HOUSEHOLD_BILL_NOT_PROVEN");
});
test("exemple fictif modifié pour afficher une réduction de facture Nova est refusé",()=>{
 reject(x=>x.synthetic_household_example.nova_tax_saving_predicted_cad=100,"SYNTHETIC_EXAMPLE_MISREPRESENTED");
});
test("un total fictif déclaré facture complète est refusé",()=>{
 reject(x=>x.synthetic_household_example.actual_total_tax_bill_cad=2328.45,"SYNTHETIC_EXAMPLE_MISREPRESENTED");
});
test("les règles de versement ne deviennent pas promesse de 90 pour cent payé",()=>{
 reject(x=>x.primeau_current_guide_rules.partial_claim_limit_is_not_confirmed_paid_pct=false,"PRIMEAU_GUIDE_NOT_PAYMENT");
});
test("la convention antérieure ne peut être considérée automatiquement remplacée",()=>{
 reject(x=>x.primeau_current_guide_rules.applicability_to_existing_2025_awards_requires_convention_review=false,"PRIMEAU_GUIDE_NOT_PAYMENT");
});
test("la taxe devient à tort impôt sur le revenu : rejet",()=>{
 reject(x=>x.fiscal_interpretation.tax_per_100_assessed_not_tax_per_100_income=false,"FISCAL_DISTINCTIONS");
});
test("la preuve de décaissement ne peut être marquée trouvée",()=>{
 reject(x=>x.sample_cash_evidence[0].status="VERIFIED","CASH_AUDIT_STILL_MISSING");
});
test("un solde souverain ne peut être inventé sans budget",()=>{
 reject(x=>x.ten_year_unfunded_scenarios[1].years[0].net_budget_cad=1200,"FINANCING_SCENARIO_NOT_PROVEN");
});
test("score 48 artificiel refusé",()=>{
 reject(x=>x.programme_score_after=48,"FALSE_PROGRAMME_STATUS");
});
test("on ne peut homologuer la viabilité fiscale sans audit",()=>{
 reject(x=>x.decision.g016o_fiscal_sustainability_audited=true,"UNWARRANTED_POLICY_APPROVAL");
});
test("exemple sans marqueur synthétique refusé",()=>{
 assert.throws(()=>calculateSyntheticWarwickPart({assessed_value_cad:300000}),/SYNTHETIC_ONLY/);
});
test("exemple synthétique retourne des valeurs non négatives",()=>{
 const r=synthetic(0);
 assert.equal(r.property_tax_subtotal_cad,0);
 assert.equal(r.partial_example_subtotal_cad,416.25);
});
test("une valeur non entière comme le rôle officiel doit être rejetée",()=>{
 assert.throws(()=>synthetic(100000.7),/SYNTHETIC_ONLY/);
});
test("les sources G0.16m restent une aide accordée sans preuves de paiement",()=>{
 const modified=copy(m);modified.cases[0].award.cash_paid_verified_cad=1000;
 const r=inspectG016oWarwickTaxes(d,modified,n);
 assert.ok(r.errors.includes("UPSTREAM_CASES_NOT_CASH_VERIFIED"));
});

test("la page publique G0.16o indique taux réels et hypothèses du calcul",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/id="taxes-warwick-g016o"/);
 assert.match(html,/0,575 \$/);
 assert.match(html,/2 328,45 \$/);
 assert.match(html,/exemple fictif et incomplet/);
 assert.match(html,/47 % inchangé/);
});
test("le site ne fait pas passer les aides et taxes conditionnelles pour des recettes réelles",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/Ce n'est pas une facture complète ni une économie fiscale promise/);
 assert.match(html,/pas une preuve de paiement/);
 assert.match(html,/Aucun compte de taxes réel, versement PRIMEAU individualisé/);
});
