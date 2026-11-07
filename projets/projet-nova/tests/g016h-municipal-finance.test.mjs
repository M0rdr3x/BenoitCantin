import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016hMunicipalData} from "../assets/g016h-municipal-finance-core.mjs";
const load=async path=>JSON.parse(await readFile(new URL("../data/"+path,import.meta.url),"utf8"));
const [d,g016g,g014]=await Promise.all([
 load("finances-municipales-g0-16h-2024.json"),
 load("continuite-territoriale-g0-16g-education-municipalites-dette.json"),
 load("registre-assiettes-fiscales-g0-14-2026-2027.json")
]);
const inspect=x=>inspectG016hMunicipalData(x,g016g,g014);
const copy=x=>structuredClone(x);
const mutate=(fn,reason)=>{const x=copy(d);fn(x);const r=inspect(x);assert.equal(r.ok,false);assert.ok(r.errors.includes(reason),r.errors.join(","));};
test("première sommation municipale MAMH publiée et préparation 47",()=>{
 const r=inspect(d);assert.equal(r.ok,true,r.errors.join(","));assert.equal(r.programme_score,47);
 assert.equal(r.local_municipalities_reported,1056);assert.equal(r.verified_municipal_tax_policies,0);
});
test("2024 : 14970167302 + 2199032000 + 18934744 = 17188134046 $ de taxes",()=>{
 const x=d.annual[0];
 assert.equal(x.property_base_taxes_cad+x.other_base_taxes_cad+x.business_taxes_cad,x.taxes_cad);
 assert.equal(x.taxes_cad,17188134046);
});
test("2023 : la ventilation se rapproche dans le même rapport",()=>{
 const x=d.annual[1];
 assert.equal(x.property_base_taxes_cad+x.other_base_taxes_cad+x.business_taxes_cad,x.taxes_cad);
 assert.equal(x.taxes_cad,16081032867);
});
test("les recettes et charges 2024 donnent le surplus publié",()=>{
 const x=d.annual[0];
 assert.equal(x.total_revenues_cad-x.total_expenses_cad,x.operating_surplus_cad);
 assert.equal(x.operating_surplus_cad,3742066646);
});
test("les recettes et charges 2023 se réconcilient",()=>{
 const x=d.annual[1];
 assert.equal(x.total_revenues_cad-x.total_expenses_cad,x.operating_surplus_cad);
});
test("les pourcentages publiés par Nova sont dérivés, non fournis par le MAMH",()=>{
 assert.equal(d.observed_reconciliation.taxes_share_of_total_revenues_pct,53.53);
 assert.equal(d.observed_reconciliation.property_tax_share_of_all_municipal_taxes_pct,87.10);
 assert.equal(d.observed_reconciliation.property_tax_share_of_total_revenues_pct,46.62);
 assert.equal(d.observed_reconciliation.tax_yoy_growth_pct,6.88);
 assert.equal(d.observed_reconciliation.rounded_percent_derived_not_source_published,true);
});
test("toutes les taxes municipales ne sont pas foncières",()=>{
 assert.ok(d.annual[0].taxes_cad>d.annual[0].property_base_taxes_cad);
 assert.ok(d.annual[0].property_base_taxes_cad>d.annual[0].property_general_tax_cad);
});
test("la taxe scolaire provinciale de 2026 reste exclue des recettes municipales de 2024",()=>{
 assert.equal(d.cross_status.g014_school_property_tax_2026_2027_mcad,1301);
 assert.equal(d.cross_status.school_property_tax_separate_from_municipal_property_taxes,true);
});
test("le ratio UMQ de 70 pour cent n'a pas la même définition",()=>{
 assert.equal(d.observed_reconciliation.scope_not_equivalent_umq_70_pct,true);
 assert.equal(d.annual[0].taxes_cad,d.observed_reconciliation.taxes_cad);
});
test("aucune recette de remplacement Nova ne peut être certifiée à partir de 2024",()=>{
 assert.ok(d.scenarios.every(x=>x.revenue_replacement_2026_2027_mcad===null));
 assert.equal(d.decision.municipal_taxes_abolition_approved,false);
});
test("sommation non exhaustive, pas de prétention à couvrir toutes les municipalités",()=>{
 assert.equal(d.source.municipalities_included,1056);
 assert.equal(d.source.municipalities_absent_from_aggregate,true);
 assert.equal(d.cross_status.all_municipal_finance_data_exhaustive,false);
});
test("analyse détaillée explicitement non auditée",()=>{
 assert.equal(d.source.detail_tax_analysis_is_marked_non_audited,true);
 assert.equal(d.source.reviewed_independently_for_nova,false);
});
test("taxes foncières 2024 modifiées sans source rejetées",()=>{
 mutate(x=>x.annual[0].property_base_taxes_cad=14970167303,"PDF_LEDGER_NOT_RECONCILED");
});
test("impôt général 2024 modifié sans preuve rejeté",()=>{
 mutate(x=>x.annual[0].property_general_tax_cad=100000,"PDF_LEDGER_NOT_RECONCILED");
});
test("taxes sur d'autres bases inventées rejetées",()=>{
 mutate(x=>x.annual[0].other_base_taxes_cad=0,"PDF_LEDGER_NOT_RECONCILED");
});
test("faux revenu total 2024 rejeté",()=>{
 mutate(x=>x.annual[0].total_revenues_cad=100000000000,"PDF_LEDGER_NOT_RECONCILED");
});
test("faux surplus public 2024 rejeté",()=>{
 mutate(x=>x.annual[0].operating_surplus_cad=0,"PDF_LEDGER_NOT_RECONCILED");
});
test("fausse série 2023 rejetée",()=>{
 mutate(x=>x.annual[1].taxes_cad=20000000000,"PDF_LEDGER_NOT_RECONCILED");
});
test("les transferts sont déjà compris dans les recettes, pas à additionner",()=>{
 assert.ok(d.annual.every(x=>x.government_transfers_cad<x.total_revenues_cad));
 mutate(x=>x.annual[0].total_revenues_cad+=x.annual[0].government_transfers_cad,"PDF_LEDGER_NOT_RECONCILED");
});
test("faux pourcentage foncier officiel rejeté",()=>{
 mutate(x=>x.observed_reconciliation.property_tax_share_of_total_revenues_pct=70,"DERIVED_PCT_UNVERIFIED");
});
test("le rapport ne doit pas être déclaré audité indépendamment pour Nova",()=>{
 mutate(x=>x.source.reviewed_independently_for_nova=true,"SCOPE_SOURCE_INCORRECT");
});
test("la couverture de 1056 municipalités ne peut devenir exhaustive",()=>{
 mutate(x=>x.source.municipalities_absent_from_aggregate=false,"SCOPE_SOURCE_INCORRECT");
});
test("confusion des pages PDF audit et détail rejetée",()=>{
 mutate(x=>x.source.pdf_page_index_tax_breakdown=7,"SCOPE_SOURCE_INCORRECT");
});
test("un CSV de ratios n'est pas une copie certifiée des montants PDF",()=>{
 assert.equal(d.cross_status.prior_csv_contains_indicators_not_amounts,true);
 mutate(x=>x.cross_status.prior_csv_imported_and_validated=true,"FALSE_REFORM_PROOF");
});
test("l'abolition de la taxation municipale ne suit pas du montant observé",()=>{
 mutate(x=>x.decision.municipal_taxes_abolition_approved=true,"GATE_INVENTED");
});
test("les montants d'une réforme future ne peuvent pas être saisis sans preuve",()=>{
 mutate(x=>x.scenarios[0].revenue_replacement_2026_2027_mcad=14970,"SCENARIO_UNFOUNDED");
});
test("la souveraineté n'hérite pas d'un budget municipal garanti",()=>{
 mutate(x=>x.scenarios[1].municipal_services_continuity_mcad=32109,"SCENARIO_UNFOUNDED");
});
test("la grille du programme ne monte pas artificiellement à 48",()=>{
 mutate(x=>x.programme_score_after=48,"STATUS_PREMATURE");
});
test("le gouvernement Nova ne peut être dit complet au stade G0.16h",()=>{
 mutate(x=>x.decision.programme_complete=true,"GATE_INVENTED");
});
test("la source G0.16g n'est pas réputée complète du seul fait de PDF municipal",()=>{
 const x=copy(g016g);x.programme_score_after=48;
 const r=inspectG016hMunicipalData(d,x,g014);
 assert.equal(r.ok,false);assert.ok(r.errors.includes("PREDECESSOR_CONTEXT"));
});
test("la taxe scolaire provinciale G0.14 n'est pas remplacée par la taxe municipale",()=>{
 const x=copy(g014);x.revenue_categories.find(x=>x.id==="FONCIER_SCOLAIRE").amount_mcad=17188;
 const r=inspectG016hMunicipalData(d,g016g,x);
 assert.equal(r.ok,false);assert.ok(r.errors.includes("PREDECESSOR_CONTEXT"));
});
