import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016w,compareHypotheticalHousehold,compareHypotheticalPublicFinance} from "../assets/g016w-fiscal-base-and-protection-core.mjs";
const read=async filename=>JSON.parse(await readFile(new URL("../data/"+filename,import.meta.url),"utf8"));
const [d,v]=await Promise.all([read("g016w-assiettes-fiscales-et-garanties-distributives-2023-2024.json"),read("cadre-financier-fiscal-g0-16v-aout-2026.json")]);
const reject=(fn,label)=>{const x=structuredClone(d);fn(x);const r=inspectG016w(x,v);assert.equal(r.ok,false);assert.ok(r.errors.includes(label),r.errors.join("|"));};
const profile = (scenario="QUEBEC_CANADA")=>({
 mode:"SYNTHETIC_ONLY",scenario,gross_income_cad:50000,is_real_person:false,benefits_double_counted:false,completeness:"FULL_ASSUMPTIONS_EXPLICIT",federal_reform_legally_authorized:false,
 current:{income_tax_quebec:5000,income_tax_federal:6000,consumption_tax_borne:1800,municipal_property_tax_borne:1000,social_contributions:2600,service_fees:500,refundable_credits:1000,cash_benefits:800,other_levies:0},
 proposed:{income_tax_quebec:4500,income_tax_federal:6000,consumption_tax_borne:500,municipal_property_tax_borne:200,social_contributions:2600,service_fees:500,refundable_credits:1000,cash_benefits:800,other_levies:0}
});
const finance = (scenario="QUEBEC_CANADA")=>({
mode:"SYNTHETIC_ONLY",scenario,provincial_services_and_debt_mcad:173597,provincial_other_receipts_mcad:28182,federal_transfers_maintained_mcad:33046,
novaincome_tax_net_mcad:112369,tax_haven_net_mcad:0,local_services_additional_net_cost_mcad:0,credit_protections_net_cost_mcad:0,national_functions_net_cost_mcad:0,transition_cost_mcad:0,federal_taxes_assumed_reassigned_mcad:0
});
test("G0.16w contrôle de source valide",()=>assert.equal(inspectG016w(d,v).ok,true));
test("Comparateur synthétique bien préparé sans certification",()=>assert.equal(d.decision.valid_synthetic_effect_calculator_ready,true));
test("Score réel reste 47",()=>assert.equal(d.score_after,47));
test("53 points manquants",()=>assert.equal(inspectG016w(d,v).missing,53));
test("Revenu déclaré des particuliers québécois 2023 : 427915 M$",()=>assert.equal(d.individual_quebec_provincial_2023.total_declared_income_mcad,427915));
test("Revenu net provincial 2023 : 387023 M$",()=>assert.equal(d.individual_quebec_provincial_2023.net_income_mcad,387023));
test("Revenu imposable provincial 2023 : 372261 M$",()=>assert.equal(d.individual_quebec_provincial_2023.taxable_income_mcad,372261));
test("Écart d'arrondi de 1 million revenu net / imposable",()=>assert.equal(d.individual_quebec_provincial_2023.net_income_mcad-d.individual_quebec_provincial_2023.deductions_to_taxable_income_mcad-d.individual_quebec_provincial_2023.taxable_income_mcad,1));
test("Impôt Québec avant crédits 2023",()=>assert.equal(d.individual_quebec_provincial_2023.tax_on_taxable_income_before_nonref_mcad,62148));
test("Impôt Québec à payer 2023 : 40790 M$",()=>assert.equal(d.individual_quebec_provincial_2023.tax_payable_mcad,40790));
test("Crédits remboursables 2023 : 9305 M$",()=>assert.equal(d.individual_quebec_provincial_2023.refundable_tax_credits_mcad,9305));
test("Impôt net après crédit 2023 : 31485 M$",()=>assert.equal(d.individual_quebec_provincial_2023.net_tax_after_refundable_mcad,31485));
test("Total déclarants provinciaux 2023",()=>assert.equal(d.individual_quebec_provincial_2023.total_filers,7220140));
test("6 groupes de revenu",()=>assert.equal(d.individual_2023_distribution.groups.length,6));
test("Total des revenus par groupes",()=>assert.equal(d.individual_2023_distribution.groups.reduce((s,x)=>s+x.declared_total_revenue_mcad,0),427915));
test("Total des impôts à payer des groupes",()=>assert.equal(d.individual_2023_distribution.groups.reduce((s,x)=>s+x.income_tax_payable_mcad,0),40790));
test("Total des crédits de groupes arrondi à 9304",()=>assert.equal(d.individual_2023_distribution.selected_group_refundable_credits_sum_mcad,9304));
test("Crédits remboursables plus élevés que impôt à payer pour revenus sous 10k",()=>assert.ok(d.individual_2023_distribution.groups[0].net_income_tax_after_refundable_mcad<0));
test("Crédits remboursables plus élevés que impôt à payer pour revenus 10-20k",()=>assert.ok(d.individual_2023_distribution.groups[1].net_income_tax_after_refundable_mcad<0));
test("Crédits remboursables plus élevés que impôt à payer pour revenus 20-30k",()=>assert.ok(d.individual_2023_distribution.groups[2].net_income_tax_after_refundable_mcad<0));
test("Net après crédits des six groupes",()=>assert.equal(d.individual_2023_distribution.groups.reduce((s,x)=>s+x.net_income_tax_after_refundable_mcad,0),31485));
test("Pas de taux individuel issu de moyennes arbitraires",()=>assert.equal(d.individual_2023_distribution.no_homogeneous_tax_rate_from_aggregate,true));
test("ARC T1 Québec 2024 : 7 106 960",()=>assert.equal(d.individual_cra_federal_2024.filers,7106960));
test("ARC T1 Québec 2024 : taxable 376946.404 M$",()=>assert.equal(d.individual_cra_federal_2024.taxable_income_mcad,376946.404));
test("ARC T1 Québec 2024 : net fédéral 43214.314 M$",()=>assert.equal(d.individual_cra_federal_2024.federal_net_income_tax_mcad,43214.314));
test("Zéro impôt provincial T1 ≠ Québec provincial réellement zéro",()=>assert.equal(d.individual_cra_federal_2024.actual_provincial_income_tax_cad,null));
test("ARC T1 et RQ 2023 non homogènes",()=>assert.equal(d.individual_cra_federal_2024.cannot_compare_filers_directly_to_provincial_statistics,true));
test("ARC T2 Québec 2024 : revenu imposable fédéral 204985.142 M$",()=>assert.equal(d.corporations_cra_federal_2024.taxable_income_mcad,204985.142));
test("ARC T2 Québec 2023 révisé 131063.725 M$",()=>assert.equal(d.corporations_cra_federal_2024.prior_2023_revised_mcad,131063.725));
test("Assiette T2 fédérale ne remplace pas assiette provinciale des sociétés",()=>assert.equal(d.corporations_cra_federal_2024.not_revenu_quebec_provincial_corporate_tax_base,true));
test("Capture visuelle PDF T2 2024 effectuée",()=>assert.equal(d.sources[5].screenshot_result,"SUCCESS"));
test("Capture visuelle PDF MAMH effectuée",()=>assert.deepEqual(d.sources[7].pdf_pages_checked_visually,[5]));
test("Capture visuelle T1 non prétendue réussie",()=>assert.equal(d.sources[3].screenshot_result,"CACHE_MISS"));
test("Municipal organismes 2023 : 29,3 G$ de revenus",()=>assert.equal(d.municipal_2023.total_revenues_reported_gcad,29.3));
test("Municipal foncier 2023 : 14,0 G$",()=>assert.equal(d.municipal_2023.property_tax_gcad,14));
test("Transferts municipaux 2023 ne sont pas nouvelles recettes provinciales",()=>assert.equal(d.municipal_2023.must_not_count_6_2_transfers_twice,true));
test("Données MAMH arrondies 29.4 vs 29.3 G$",()=>assert.equal(d.municipal_2023.rounding_difference_with_published_total_gcad,0.1));
test("Québec Canada ne peut abolir seul les impôts fédéraux",()=>assert.equal(d.constitutional_gate.within_canada_province_cannot_unilaterally_repeal_federal_tax,true));
test("Régimes contributifs à documenter",()=>assert.equal(d.constitutional_gate.tax_vs_user_fee_vs_social_insurance_distinction_unresolved,true));
test("Deux scénarios pour dix années",()=>assert.ok(d.ten_year_scenarios.every(x=>x.years.length===10)));
test("Aucun taux Nova déjà vérifié",()=>assert.equal(d.fiscal_gaps.coherent_government_rate_pct,null));
test("Aucune recette anti-paradis fiscaux fantasmée",()=>assert.equal(d.fiscal_gaps.net_enforceable_tax_haven_levy_mcad,null));
test("Aucun financement municipal fiscalement démontré",()=>assert.equal(d.fiscal_gaps.municipal_tax_replacement_fully_costed_mcad,null));
test("Cinq profils de ménage ne sont pas des estimations déjà effectuées",()=>assert.ok(d.distribution_protections.sample_household_profiles.every(x=>x.status==="NOT_MODELED")));
test("Huit pièces de validation manquent",()=>assert.equal(d.unresolved_validation_work.length,8));
test("Exemple ménage fictif calculé seulement à titre de test",()=>{const x=compareHypotheticalHousehold(profile());assert.equal(x.classification,"SYNTHETIC_CASE_NOT_FORECAST");assert.equal(x.change_cad,2600);assert.equal(x.benefit_proven,false);});
test("Une diminution fictive de crédits peut générer une perte",()=>{const p=profile();p.proposed.refundable_credits=0;p.proposed.consumption_tax_borne=1800;p.proposed.municipal_property_tax_borne=1000;p.proposed.income_tax_quebec=5200;assert.ok(compareHypotheticalHousehold(p).change_cad<0);});
test("Ménage réel ou incomplet rejeté",()=>{const p=profile();p.is_real_person=true;assert.throws(()=>compareHypotheticalHousehold(p),/HYPOTHETICAL_ONLY_INCOMPLETE/);});
test("Droit fédéral maintenu en Québec Canada",()=>{const p=profile();p.proposed.income_tax_federal=0;assert.throws(()=>compareHypotheticalHousehold(p),/FEDERAL_TAX_NOT_AUTOMATICALLY_ABOLISHED/);});
test("Crédits double comptés rejetés",()=>{const p=profile();p.benefits_double_counted=true;assert.throws(()=>compareHypotheticalHousehold(p),/HYPOTHETICAL_ONLY_INCOMPLETE/);});
test("Simulation de bilan synthétique équilibré",()=>{const x=compareHypotheticalPublicFinance(finance());assert.equal(x.balance_mcad,0);assert.equal(x.financial_plan_certified,false);});
test("Le transfert des recettes fédérales impossible dans la province sans régime",()=>{const x=finance();x.federal_taxes_assumed_reassigned_mcad=100;assert.throws(()=>compareHypotheticalPublicFinance(x),/NO_UNILATERAL_FEDERAL_POWERS/);});
test("Le souverain ne reprend pas les transferts fédéraux sans accord",()=>{const x=finance("QUEBEC_SOUVERAIN");assert.throws(()=>compareHypotheticalPublicFinance(x),/NO_UNVERIFIED_SOVEREIGN_TRANSFERS/);});
test("Fausse hausse du score refusée",()=>reject(x=>x.score_after=48,"FALSE_SCORE"));
test("Montant imposable Québec 2023 inventé refusé",()=>reject(x=>x.individual_quebec_provincial_2023.taxable_income_mcad=500000,"QUEBEC_TAX_2023"));
test("Montant imposable sociétés 2024 inventé refusé",()=>reject(x=>x.corporations_cra_federal_2024.taxable_income_mcad=500000,"CRA_T2_MEANING"));
test("Numéro d'année T1 2023 au lieu de 2024 refusé",()=>reject(x=>x.individual_cra_federal_2024.tax_year=2023,"CRA_T1_MEANING"));
test("Faux argent de taxes foncières ajouté au Québec refusé",()=>reject(x=>x.municipal_2023.must_not_add_whole_29_3_billion_to_province_budget=false,"MUNICIPAL_NOT_DOUBLECOUNTED"));
test("Rendement artificiel paradis fiscaux refusé",()=>reject(x=>x.fiscal_gaps.net_enforceable_tax_haven_levy_mcad=10000,"UNFUNDED_MACRO"));
test("Bilan de souveraineté inventé refusé",()=>reject(x=>x.ten_year_scenarios[1].years[0].full_consolidated_balance_mcad=1,"TWO_DECADE_MODELS"));
test("Protection personnes vulnérables ne peut être supprimée",()=>reject(x=>x.distribution_protections.do_not_abolish_refundable_credits_without_poverty_impact_test=false,"DISTRIBUTION_UNPROVEN"));
test("Validation légale fictive refusée",()=>reject(x=>x.constitutional_gate.no_legality_approved=false,"LEGAL_GATE"));
test("La réussite des contrôles n'est pas certification officielle",()=>reject(x=>x.decision.nova_tax_rate_certified=true,"FALSE_CERTIFICATION"));
