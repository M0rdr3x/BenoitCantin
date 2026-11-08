import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016z,consolidateSyntheticZ,stressSyntheticZ} from "../assets/g016z-consolidated-funding-core.mjs";
const load=async name=>JSON.parse(await readFile(new URL("../data/"+name,import.meta.url),"utf8"));
const [d,V,W,X,Y]=await Promise.all([
 load("g016z-financement-consolide-et-protections-2026-2036.json"),
 load("cadre-financier-fiscal-g0-16v-aout-2026.json"),
 load("g016w-assiettes-fiscales-et-garanties-distributives-2023-2024.json"),
 load("g016x-concordance-fiscale-multiniveau-2026.json"),
 load("g016y-loi-cadre-et-conditions-arret-2026.json")
]);
const reject=(mut,expected)=>{const x=structuredClone(d);mut(x);const result=inspectG016z(x,V,W,X,Y);assert.equal(result.ok,false,result.errors.join("|"));assert.ok(result.errors.some(z=>z===expected||z.startsWith(expected)),result.errors.join("|"));};
const synthetic=(scenario="QUEBEC_CANADA")=>({
 mode:"SYNTHETIC_ONLY",unit:"MILLIONS_CAD",scenario,claims_real_government_model:false,
 nova_income_net_yield_mcad:110,nova_haven_incremental_net_yield_mcad:5,provincial_other_external_mcad:30,
 federal_transfer_to_province_mcad:20,municipal_own_external_mcad:15,additional_external_receipts_mcad:0,
 provincial_spending_including_municipal_transfer_mcad:140,municipal_spending_mcad:35,
 internal_transfer_paid_mcad:10,internal_transfer_received_mcad:10,
 service_additional_mcad:0,credits_and_social_guarantees_mcad:0,
 debt_pension_transition_mcad:0,national_functions_cost_mcad:0,federal_assigned_revenue_mcad:0
});
test("Registre G0.16z valide",()=>assert.equal(inspectG016z(d,V,W,X,Y).ok,true));
test("47 points de préparation maintenus",()=>assert.equal(d.score_after,47));
test("53 points manquants maintenus",()=>assert.equal(d.missing_score_points,53));
test("Dix exercices de référence",()=>assert.equal(d.official_reference_series.length,10));
test("Cinq exercices fondés sur prévisions gouvernementales",()=>assert.equal(d.official_reference_series.filter(x=>x.source_available).length,5));
test("Cinq exercices sans prévisions gouvernementales",()=>assert.equal(d.official_reference_series.filter(x=>!x.source_available).length,5));
test("Premier horizon 2026-2027",()=>assert.equal(d.official_reference_series[0].year,'2026-2027'));
test("Dernier horizon 2035-2036",()=>assert.equal(d.official_reference_series[9].year,'2035-2036'));
test("Revenus actuels gouvernement Québec 168389 M$",()=>assert.equal(d.baseline_current_provincial_finances.revenue_current_mcad,168389));
test("Impôts agrégés actuels Québec 107161 M$",()=>assert.equal(d.baseline_current_provincial_finances.tax_cats_current_mcad,107161));
test("Autres recettes 28182 M$ conservées seulement en hypothèse",()=>assert.equal(d.baseline_current_provincial_finances.assumed_remaining_other_revenue_mcad,28182));
test("Transferts fédéraux 33046 M$ hypothèse",()=>assert.equal(d.baseline_current_provincial_finances.assumed_current_federal_transfers_mcad,33046));
test("Dépenses publiques Québec prévues 171597 M$",()=>assert.equal(d.baseline_current_provincial_finances.spending_including_debt_mcad,171597));
test("Provision pour éventualités 2000 M$",()=>assert.equal(d.baseline_current_provincial_finances.contingency_mcad,2000));
test("Fonds des générations 2482 M$",()=>assert.equal(d.baseline_current_provincial_finances.generations_fund_mcad,2482));
test("Déficit prévu après provision -5208 M$",()=>assert.equal(d.baseline_current_provincial_finances.account_balance_current_with_reserve_mcad,-5208));
test("Seuil de remplacement conditionnel 112369 M$",()=>assert.equal(d.baseline_current_provincial_finances.conditional_two_levy_balance_target_mcad,112369));
test("Seuil avec Fonds des générations 114851 M$",()=>assert.equal(d.baseline_current_provincial_finances.conditional_two_levy_target_with_generations_mcad,114851));
test("Écart fiscal initial 5208 M$",()=>assert.equal(d.baseline_current_provincial_finances.conditional_current_tax_to_balance_gap_mcad,5208));
test("Référence municipale historique 2023 29,3 G$",()=>assert.equal(d.municipal_historical_reference.total_municipal_organization_revenues_gcad,29.3));
test("Foncier municipal 2023 14 G$",()=>assert.equal(d.municipal_historical_reference.property_taxes_gcad,14));
test("Transferts aux municipalités 2023 6,2 G$",()=>assert.equal(d.municipal_historical_reference.transfers_from_other_governments_gcad,6.2));
test("Aucun coût de remplacement foncier en 2026 inventé",()=>assert.equal(d.municipal_historical_reference.replacement_of_municipal_property_tax_costed_mcad,null));
test("Aucun changement automatique des impôts fédéraux",()=>assert.equal(d.scenario_years[0].federal_tax_unilaterally_repealed,false));
test("Transferts souverains non garantis",()=>assert.equal(d.scenario_years[1].federal_transfers_assumed_automatically,false));
test("Deux budgets décennaux distincts",()=>assert.ok(d.scenario_years.length===2&&d.scenario_years.every(x=>x.years.length===10)));
test("Aucun bilan public Nova créé arbitrairement",()=>assert.ok(d.scenario_years.every(x=>x.years.every(y=>y.net_real_public_balance_mcad===null))));
test("Aucune valeur de taxation Nova déclarée",()=>assert.ok(d.scenario_years.every(x=>x.years.every(y=>y.nova_income_net_yield_mcad===null))));
test("Rendement anti-paradis fiscaux non inventé",()=>assert.ok(d.scenario_years.every(x=>x.years.every(y=>y.nova_haven_incremental_net_yield_mcad===null))));
test("Aucun bilan souverain sans coût des fonctions nationales",()=>assert.ok(d.scenario_years[1].years.every(x=>x.additional_sovereign_functions_cost_mcad===null)));
test("Trois scénarios de sensibilité prévus et non calibrés",()=>assert.deepEqual(d.stress_test_plan.map(x=>x.id),['CENTRAL','DOWNSIDE','UPSIDE']));
test("Aucun scénario de sensibilité présenté comme réalisé",()=>assert.ok(d.stress_test_plan.every(x=>x.validated===false&&x.revenue_shock_pct===null)));
test("Quatorze portes de preuve bloquantes",()=>assert.ok(d.evidence_gates.length===14&&d.evidence_gates.every(x=>x.blocking===true)));
test("Dix risques ouverts",()=>assert.ok(d.risk_register.length===10&&d.risk_register.every(x=>x.status==='OPEN')));
test("Huit conditions d'arrêt toujours actives",()=>assert.equal(d.hard_stop_bridge.all_eight_stops_active,true));
test("Exemple de consolidation fictif avec solde +15",()=>assert.equal(consolidateSyntheticZ(synthetic()).balance_mcad,15));
test("Transfert fictif interne de 10 neutralisé",()=>assert.equal(consolidateSyntheticZ(synthetic()).internal_transfer_removed_mcad,10));
test("Recettes externes fictives comptées exactement",()=>assert.equal(consolidateSyntheticZ(synthetic()).total_external_receipts_mcad,180));
test("Dépenses fictives consolidées 165",()=>assert.equal(consolidateSyntheticZ(synthetic()).consolidated_spending_mcad,165));
test("Exercice fictif non certifié",()=>assert.equal(consolidateSyntheticZ(synthetic()).real_nova_policy_financed,false));
test("Scénario souverain fictif sans transferts comptabilisé",()=>assert.equal(consolidateSyntheticZ({...synthetic('QUEBEC_SOUVERAIN'),federal_transfer_to_province_mcad:0,national_functions_cost_mcad:20,federal_assigned_revenue_mcad:30}).balance_mcad,5));
test("Choc fictif recettes -10% donne une perte de 11",()=>assert.equal(stressSyntheticZ(synthetic(),{mode:'SYNTHETIC_ONLY',income_receipts_shock_pct:-10,total_spending_shock_pct:0,additional_debt_service_mcad:0}).balance_mcad,4));
test("Choc dépenses +5% et surcoût de dette 2",()=>assert.equal(stressSyntheticZ(synthetic(),{mode:'SYNTHETIC_ONLY',income_receipts_shock_pct:0,total_spending_shock_pct:5,additional_debt_service_mcad:2}).balance_mcad,6));
test("Choc combiné fictif solde négatif",()=>assert.ok(stressSyntheticZ(synthetic(),{mode:'SYNTHETIC_ONLY',income_receipts_shock_pct:-10,total_spending_shock_pct:5,additional_debt_service_mcad:2}).balance_mcad<0));
test("Aucune simulation certifiée automatiquement",()=>assert.equal(stressSyntheticZ(synthetic(),{mode:'SYNTHETIC_ONLY',income_receipts_shock_pct:-10,total_spending_shock_pct:5,additional_debt_service_mcad:2}).real_nova_policy_financed,false));
test("Retrait de l'hypothèse de transfert fédéral améliore la rigueur, pas recettes",()=>assert.equal(d.model_rules.no_unverified_sovereign_transfers,true));
test("Les transferts internes ne sont pas de nouvelles recettes",()=>assert.equal(d.model_rules.no_double_count_local_provincial_transfers,true));
test("Les crédits sociaux ne peuvent être supprimés sans financement",()=>assert.equal(d.model_rules.no_abolition_of_public_benefits_without_funding,true));
test("Pas de hausse artificielle d'audit pour les fichiers",()=>assert.equal(d.model_rules.no_completion_gain_for_new_files,true));
test("Ne pas augmenter score sans audit",()=>reject(x=>{x.score_after=49},"FALSE_PREPAREDNESS"));
test("Ne pas réduire artificiellement points manquants",()=>reject(x=>{x.missing_score_points=51},"FALSE_PREPAREDNESS"));
test("Ne pas certifier le financement sans test",()=>reject(x=>{x.decision.point_gain_earned=true},"FALSE_FINANCIAL_CERTIFICATION"));
test("Ne pas publier un solde Nova fictif",()=>reject(x=>{x.scenario_years[0].years[0].net_real_public_balance_mcad=1},"NOVA_TEN_YEAR_UNKNOWN"));
test("Ne pas inventer une recette fiscale",()=>reject(x=>{x.scenario_years[1].years[3].nova_income_net_yield_mcad=50000},"NOVA_TEN_YEAR_UNKNOWN"));
test("Ne pas prétendre à une réforme légale",()=>reject(x=>{x.scenario_years[0].certified=true},"NOVA_TEN_YEAR_UNKNOWN"));
test("Ne pas effacer recettes gouvernementales existantes",()=>reject(x=>{x.baseline_current_provincial_finances.revenue_current_mcad=168390},"PROVINCIAL_BRIDGE"));
test("Ne pas inventer financement municipal local",()=>reject(x=>{x.municipal_historical_reference.replacement_of_municipal_property_tax_costed_mcad=14000},"MUNICIPAL_NO_DOUBLE_COUNT"));
test("Ne pas transformer 2032 en prévision officielle",()=>reject(x=>{x.official_reference_series[5].source_available=true},"REFERENCE_YEAR_5"));
test("Ne pas inventer 2034-2035",()=>reject(x=>{x.official_reference_series[8].conditional_tax_need_to_balance_account_mcad=300000},"REFERENCE_YEAR_8"));
test("Ne pas inventer coût souverain national",()=>reject(x=>{x.scenario_years[1].years[2].additional_sovereign_functions_cost_mcad=8000},"NOVA_TEN_YEAR_UNKNOWN"));
test("Ne pas couvrir le déficit par les paradis fiscaux fictifs",()=>reject(x=>{x.scenario_years[0].years[0].nova_haven_incremental_net_yield_mcad=10000},"NOVA_TEN_YEAR_UNKNOWN"));
test("Ne pas annuler condition d'arrêt de service sans preuve",()=>reject(x=>{x.evidence_gates[3].passed=true},"EVIDENCE_GATES_NOT_CLEARED"));
test("Ne pas déclarer un risque financé",()=>reject(x=>{x.risk_register[0].net_cost_mcad=0},"OPEN_RISK_REGISTER"));
test("Ne pas falsifier l'audit du dossier législatif",()=>reject(x=>{x.hard_stop_bridge.all_eight_stops_active=false},"EIGHT_STOPS"));
test("Ne pas compter transferts municipaux deux fois",()=>reject(x=>{x.model_rules.no_double_count_local_provincial_transfers=false},"FALSE_COST_ASSUMPTIONS"));
test("Ne pas fabriquer choc pessimiste externe",()=>reject(x=>{x.stress_test_plan[1].revenue_shock_pct=-10},"STRESS_NOT_CALIBRATED"));
test("Ne pas supprimer fiscalité fédérale dans le Canada",()=>reject(x=>{x.scenario_years[0].federal_tax_unilaterally_repealed=true},"NOVA_TEN_YEAR_UNKNOWN"));
test("Ne pas présumer fédéral dans la souveraineté",()=>reject(x=>{x.scenario_years[1].federal_transfers_assumed_automatically=true},"NOVA_TEN_YEAR_UNKNOWN"));
test("Ne pas affirmer source antérieure absente",()=>reject(x=>{x.references[0].path='missing'},"REFERENCE_CHAIN"));
test("Ne pas certifier le programme adopté",()=>reject(x=>{x.decision.programme_adopted=true},"FALSE_FINANCIAL_CERTIFICATION"));
test("Une simulation réelle ne peut pas se déclarer fictive",()=>assert.throws(()=>consolidateSyntheticZ({...synthetic(),claims_real_government_model:true}),/SYNTHETIC_ONLY/));
test("Pas d'impôts fédéraux repris en province",()=>assert.throws(()=>consolidateSyntheticZ({...synthetic(),federal_assigned_revenue_mcad:20}),/FEDERAL_JURISDICTION_NOT_TRANSFERRED/));
test("Pas de dette nationale financée par province sans transition",()=>assert.throws(()=>consolidateSyntheticZ({...synthetic(),national_functions_cost_mcad:20}),/FEDERAL_JURISDICTION_NOT_TRANSFERRED/));
test("Rejeter le transfert interne non réconcilié",()=>assert.throws(()=>consolidateSyntheticZ({...synthetic(),internal_transfer_received_mcad:12}),/INTERNAL_TRANSFER_MISMATCH/));
test("Rejeter le transfert plus grand que les dépenses",()=>assert.throws(()=>consolidateSyntheticZ({...synthetic(),internal_transfer_paid_mcad:150,internal_transfer_received_mcad:150}),/IMPOSSIBLE_INTERNAL_TRANSFER/));
test("Rejeter la continuation souveraine de transfert non signé",()=>assert.throws(()=>consolidateSyntheticZ(synthetic('QUEBEC_SOUVERAIN')),/SOVEREIGN_TRANSFERS_NOT_PROVEN/));
test("Rejeter l'impôt négatif inventé",()=>assert.throws(()=>consolidateSyntheticZ({...synthetic(),nova_haven_incremental_net_yield_mcad:-1}),/INVALID_MONETARY_INPUTS/));
test("Rejeter un choc de revenus sous -100%",()=>assert.throws(()=>stressSyntheticZ(synthetic(),{mode:'SYNTHETIC_ONLY',income_receipts_shock_pct:-110,total_spending_shock_pct:0,additional_debt_service_mcad:0}),/INVALID_HYPOTHETICAL_STRESS/));
test("Rejeter un stress sans valeur de choc",()=>assert.throws(()=>stressSyntheticZ(synthetic(),{mode:'SYNTHETIC_ONLY',income_receipts_shock_pct:null,total_spending_shock_pct:0,additional_debt_service_mcad:0}),/INVALID_HYPOTHETICAL_STRESS/));
test("Rejeter un coût de dette négatif",()=>assert.throws(()=>stressSyntheticZ(synthetic(),{mode:'SYNTHETIC_ONLY',income_receipts_shock_pct:0,total_spending_shock_pct:0,additional_debt_service_mcad:-1}),/INVALID_HYPOTHETICAL_STRESS/));
