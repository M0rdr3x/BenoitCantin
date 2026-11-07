import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016iLocalTaxStress,calculateFrozenStress} from "../assets/g016i-local-tax-stress-core.mjs";
const load=async file=>JSON.parse(await readFile(new URL("../data/"+file,import.meta.url),"utf8"));
const [d,g016h,g016g,g014,g015]=await Promise.all([
 load("risque-transition-taxes-locales-g0-16i-2024.json"),
 load("finances-municipales-g0-16h-2024.json"),
 load("continuite-territoriale-g0-16g-education-municipalites-dette.json"),
 load("registre-assiettes-fiscales-g0-14-2026-2027.json"),
 load("matrice-preuves-g0-15-fiscalite.json")
]);
const check=x=>inspectG016iLocalTaxStress(x,g016h,g016g,g014,g015);
const copy=x=>structuredClone(x);
const fails=(modify,name)=>{
 const x=copy(d);modify(x);
 const r=check(x);
 assert.equal(r.ok,false,name);
 assert.ok(r.errors.includes(name),r.errors.join(","));
};
test("4 sensibilités documentées et programme toujours à 47 sur 100",()=>{
 const x=check(d);
 assert.equal(x.ok,true,x.errors.join(","));
 assert.equal(x.programme_score,47);
 assert.equal(x.legal_approvals,0);
});
test("référence 2024 reprise exactement de G0.16h",()=>{
 assert.equal(d.fixed_2024_baseline.total_revenues_cad,32109026468);
 assert.equal(d.fixed_2024_baseline.total_expenses_cad,28366959822);
 assert.equal(d.fixed_2024_baseline.operating_surplus_cad,3742066646);
});
test("absence de retrait = résultat comptable 2024 sans le déclarer disponible",()=>{
 const b=d.static_stress[0];
 assert.equal(b.removed_revenue_cad,0);
 assert.equal(b.arithmetic_operating_balance_cad,3742066646);
 assert.equal(b.actual_nova_prediction,false);
});
test("sans taxe générale foncière et charges gelées, solde mécanique -9472519746",()=>{
 const b=d.static_stress[1];
 assert.equal(b.removed_revenue_cad,13214586392);
 assert.equal(b.arithmetic_operating_balance_cad,-9472519746);
});
test("sans toutes taxes foncières et charges gelées, solde mécanique -11228100656",()=>{
 const b=d.static_stress[2];
 assert.equal(b.removed_revenue_cad,14970167302);
 assert.equal(b.arithmetic_operating_balance_cad,-11228100656);
});
test("sans toutes taxes locales et charges gelées, solde mécanique -13446067400",()=>{
 const b=d.static_stress[3];
 assert.equal(b.removed_revenue_cad,17188134046);
 assert.equal(b.arithmetic_operating_balance_cad,-13446067400);
 assert.equal(b.replacement_to_hold_reference_balance_cad,17188134046);
});
test("toutes les catégories sont imbriquées, jamais additionnées",()=>{
 assert.equal(d.methodology.category_stresses_overlap_never_add_together,true);
 assert.ok(d.static_stress[1].removed_revenue_cad<d.static_stress[2].removed_revenue_cad);
 assert.ok(d.static_stress[2].removed_revenue_cad<d.static_stress[3].removed_revenue_cad);
});
test("aucun scénario 2024 ne prétend à un financement de remplacement",()=>{
 assert.ok(d.static_stress.every(x=>x.verified_replacement_cad===null&&!x.continuity_financed&&!x.legally_approved));
});
test("la provenance municipale comporte 1056 comptes sans exhaustivité",()=>{
 assert.equal(d.provenance.included_local_municipalities,1056);
 assert.equal(d.provenance.missing_municipalities,true);
 assert.equal(d.geographic_coverage.municipal_row_level_data_imported,false);
});
test("jeu 2025 du catalogue est un rôle d'évaluation foncière et non des recettes fiscales 2025",()=>{
 assert.equal(d.provenance.catalogue_financial_dataset_year,2024);
 assert.equal(d.provenance.catalogue_updated_on,"2026-11-05");
 assert.equal(d.provenance.catalogue_2025_values_are_property_assessment_not_2025_financial_revenues,true);
});
test("2026-2036 : deux statuts, dix années chacun, budgets toujours inconnus",()=>{
 assert.deepEqual(d.two_constitutional_budgets.map(x=>x.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
 assert.ok(d.two_constitutional_budgets.every(x=>x.annual.length===10));
 assert.ok(d.two_constitutional_budgets.every(x=>x.annual.every(y=>y.municipal_net_balance_cad===null)));
});
test("7 familles de services et droits non financées artificiellement",()=>{
 assert.equal(d.essential_services.length,7);
 assert.ok(d.essential_services.every(x=>x.protected_in_principle===true&&
   x.annual_continuity_cost_cad===null&&x.income_replacement_identified_cad===null));
});
test("l'ajout d'un montant de remplacement fictif est refusé",()=>{
 fails(x=>x.static_stress[3].verified_replacement_cad=1000000000,"STATIC_STRESS_INCORRECT");
});
test("faire passer le déficit 2024 pour un budget Nova est refusé",()=>{
 fails(x=>x.static_stress[3].actual_nova_prediction=true,"STATIC_STRESS_INCORRECT");
});
test("un solde négatif falsifié est refusé",()=>{
 fails(x=>x.static_stress[3].arithmetic_operating_balance_cad=0,"STATIC_STRESS_INCORRECT");
});
test("une recette fiscale locale faussement actualisée est refusée",()=>{
 fails(x=>x.fixed_2024_baseline.taxes_cad=19000000000,"HISTORICAL_BASELINE_MISMATCH");
});
test("substitution de 2025 comme millésime financier interdit",()=>{
 fails(x=>x.provenance.catalogue_financial_dataset_year=2025,"PROVENANCE_AND_YEARS");
});
test("source 1056 municipalités ne peut prétendre en couvrir davantage",()=>{
 fails(x=>x.provenance.included_local_municipalities=1100,"PROVENANCE_AND_YEARS");
});
test("taxes cumulées artificiellement créent un registre invalide",()=>{
 fails(x=>x.static_stress.push(copy(x.static_stress[3])),"STATIC_STRESS_INCORRECT");
});
test("les catégories ne peuvent s'additionner comme disjointes",()=>{
 fails(x=>x.methodology.category_stresses_overlap_never_add_together=false,"MISLEADING_POLICY_PROJECTIONS");
});
test("un excédent comptable n'est pas une réserve de liquidités libre",()=>{
 fails(x=>x.methodology["2024_balance_is_accounting_not_free_cash"]=false,"MISLEADING_POLICY_PROJECTIONS");
});
test("aucune recette provenant de paradis fiscaux ne peut être inventée",()=>{
 fails(x=>x.methodology.anti_haven_net_revenue_modeled=true,"MISLEADING_POLICY_PROJECTIONS");
});
test("un coût d'eau inventé sans étude est refusé",()=>{
 fails(x=>x.essential_services[0].annual_continuity_cost_cad=2500000000,"SERVICE_FINANCING_UNVERIFIED");
});
test("une revue juridique de droit du travail imaginaire est refusée",()=>{
 fails(x=>x.essential_services[5].worker_rights_audit=true,"SERVICE_FINANCING_UNVERIFIED");
});
test("la matrice régionale ne peut être marquée complète sans municipalités",()=>{
 fails(x=>x.geographic_coverage.regional_service_costs_comparable=true,"LOCAL_DATA_COVERAGE_UNVERIFIED");
});
test("les transferts internes ne peuvent être considérés réconciliés",()=>{
 fails(x=>x.geographic_coverage.intergovernmental_transfers_eliminated_for_consolidated_budget=true,"LOCAL_DATA_COVERAGE_UNVERIFIED");
});
test("une simulation Canada chiffrée sans preuve est rejetée",()=>{
 fails(x=>x.two_constitutional_budgets[0].annual[0].municipal_net_balance_cad=3742066646,"FALSE_DECADAL_SCENARIO");
});
test("une transmission automatique de transferts fédéraux au Québec souverain est rejetée",()=>{
 fails(x=>x.two_constitutional_budgets[1].federal_transfers_assumed_retained=true,"FALSE_DECADAL_SCENARIO");
});
test("vingt années ne deviennent pas toutes des copies du 2024",()=>{
 fails(x=>x.two_constitutional_budgets[0].annual[0].municipal_revenue_current_cad=32109026468,"FALSE_DECADAL_SCENARIO");
});
test("année manquante dans le budget hypothétique est refusée",()=>{
 fails(x=>x.two_constitutional_budgets[1].annual.pop(),"FALSE_DECADAL_SCENARIO");
});
test("15 dépendances G0.15 demeurent non franchies",()=>{
 assert.equal(d.evidence_dependencies.length,15);
 fails(x=>x.evidence_dependencies.pop(),"G015_NOT_VALIDATED");
});
test("une politique à deux taxes ne peut être approuvée sans budget",()=>{
 fails(x=>x.decisions.two_taxes_achievable_certified=true,"FALSE_APPROVAL");
});
test("l'état politique 47/100 n'augmente pas sur un seul calcul",()=>{
 fails(x=>x.programme_score_after=48,"FALSE_PROGRAMME_STATUS");
});
test("on ne peut attribuer 2024 à un autre périmètre G0.16h",()=>{
 const h=copy(g016h);h.source.municipalities_included=1200;
 const r=inspectG016iLocalTaxStress(d,h,g016g,g014,g015);
 assert.ok(r.errors.includes("HISTORICAL_BASELINE_MISMATCH"));
});
test("un financement du Québec devenu non sourcé ne valide pas la taxe scolaire",()=>{
 const g=copy(g014);g.revenue_categories.find(x=>x.id==="FONCIER_SCOLAIRE").amount_mcad=17188;
 const r=inspectG016iLocalTaxStress(d,g016h,g016g,g,g015);
 assert.ok(r.errors.includes("PREDECESSOR_CHAIN_BROKEN"));
});
test("une commande de stress sur une taxe inconnue échoue fermement",()=>{
 assert.throws(()=>calculateFrozenStress(d.fixed_2024_baseline,"FEDERAL_TAX"),/INVALID_REFERENCE_OR_MODE/);
});
test("un montant négatif ou incohérent de référence échoue",()=>{
 const b=copy(d.fixed_2024_baseline);b.taxes_cad=-1;
 assert.throws(()=>calculateFrozenStress(b,"ALL_MUNICIPAL_TAXES"),/INVALID_REFERENCE_OR_MODE/);
});
