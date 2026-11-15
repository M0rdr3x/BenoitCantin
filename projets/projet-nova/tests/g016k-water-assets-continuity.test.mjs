import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016kWaterContinuity} from "../assets/g016k-water-assets-core.mjs";
const load=async name=>JSON.parse(await readFile(new URL("../data/"+name,import.meta.url),"utf8"));
const [d,g016j,g016h]=await Promise.all([
 load("continuite-actifs-eau-g0-16k-2025.json"),
 load("ventilation-charges-municipales-g0-16j-2024.json"),
 load("finances-municipales-g0-16h-2024.json")
]);
const clone=x=>structuredClone(x);
const inspect=x=>inspectG016kWaterContinuity(x,g016j,g016h);
const reject=(change,code)=>{
 const v=clone(d);change(v);const result=inspect(v);
 assert.equal(result.ok,false);
 assert.ok(result.errors.includes(code),result.errors.join(","));
};
test("référence CERIU et MAMH cohérente et programme 47",()=>{
 const r=inspect(d);
 assert.equal(r.ok,true,r.errors.join(","));
 assert.equal(r.programme_score,47);
 assert.equal(r.certified_10_year_budgets,0);
});
test("patrimoine 2025 total : 197,6 G$ et non budget Nova",()=>{
 const a=d.assets_2025;
 assert.equal(a.total_replacement_gcad,197.6);
 assert.equal(a.replacement_value_is_not_2026_budget,true);
 assert.equal(a.poor_assets_full_replacement_not_always_required,true);
});
test("159,7 G$ de conduites et 37,9 G$ d'ouvrages forment 197,6 G$",()=>{
 const a=d.assets_2025;
 assert.equal(Math.round((a.linear_subtotal_gcad+a.facility_subtotal_gcad)*10),1976);
 assert.equal(a.asset_types.reduce((v,x)=>v+Math.round(x.replacement_gcad*10),0),1976);
});
test("101105 km de conduites et 10659 ouvrages",()=>{
 const a=d.assets_2025;
 assert.equal(a.asset_types.filter(x=>x.kind==="LINEAR").reduce((n,x)=>n+x.count,0),101105);
 assert.equal(a.asset_types.filter(x=>x.kind==="FACILITY").reduce((n,x)=>n+x.count,0),10659);
});
test("conditions A/B, C, D/E 67/23/10 totalisent 100",()=>{
 const a=d.assets_2025;
 assert.equal(a.very_good_or_good_share_pct+a.acceptable_share_pct+a.poor_very_poor_share_pct,100);
});
test("20,6 G$ d'actifs D/E ne sont pas des travaux obligatoires de 20,6 G$",()=>{
 assert.equal(d.assets_2025.poor_very_poor_replacement_gcad,20.6);
 assert.equal(d.accounting_barriers.bad_condition_stock_not_due_replacement_cost,true);
});
test("44,9 G$ en C ne sont pas des dépenses immédiatement dues",()=>{
 assert.equal(d.assets_2025.acceptable_replacement_gcad,44.9);
 assert.equal(d.accounting_barriers.category_C_not_automatically_due,true);
});
test("les sources couvrent 938 municipalités, mais toutes n'ont pas renouvelé leurs données",()=>{
 const a=d.assets_2025;
 assert.equal(a.reporting_municipalities_since_2014,938);
 assert.equal(a.updated_2025_municipalities,666);
 assert.equal(a.represented_population_share_pct,99);
});
test("les valeurs évaluées selon l'âge ou le jugement demandent vérification",()=>{
 assert.equal(d.assets_2025.approx_percent_values_assessed_age_or_judgment,75);
 assert.equal(d.assets_2025.bad_assets_age_or_judgment_share_pct,43);
 assert.equal(d.assets_2025.acceptable_assets_age_or_judgment_share_pct,87);
});
test("les travaux de chaussée à la largeur de tranchée sont déjà inclus",()=>{
 assert.equal(d.assets_2025.includes_road_reinstatement_on_trench_width,true);
 assert.equal(d.accounting_barriers.road_trench_restoration_not_added_to_separate_total,true);
});
test("dépenses de fonctionnement MAMH 2024 distinctes du stock CERIU 2025",()=>{
 assert.equal(d.municipal_water_operating_2024.expense_cad,2519426792);
 assert.equal(d.municipal_water_operating_2024.municipalities_included,1056);
 assert.equal(d.municipal_water_operating_2024.same_scope_as_ceriu_sample,false);
 assert.equal(d.municipal_water_operating_2024.expense_plus_asset_value_meaningful,false);
});
test("la première étape PGA-Eau est l'engagement, pas l'adoption du plan final",()=>{
 assert.equal(d.government_plans.invited_commitment_deadline,"2026-12-31");
 assert.equal(d.government_plans.engagement_is_final_pga_approval,false);
 assert.equal(d.government_plans.municipal_plans_fully_submitted_verified,null);
});
test("20 années de simulation restent sans financement ni solde",()=>{
 assert.equal(d.continuity_scenarios.length,2);
 assert.ok(d.continuity_scenarios.every(x=>x.annual.length===10));
 assert.ok(d.continuity_scenarios.every(s=>s.annual.every(x=>
  x.net_balance_cad===null&&x.asset_renewal_capex_cad===null)));
});
test("on ne peut certifier un financement fiscal Nova sur ces seuls comptes",()=>{
 assert.equal(d.decisions.tax_reduction_financed,false);
 assert.equal(d.decisions.renewal_investments_funded,false);
 assert.equal(d.decisions.program_budget_complete,false);
});
test("modifier 197,6 G$ sans révision de source est rejeté",()=>{
 reject(x=>x.assets_2025.total_replacement_gcad=220.0,"ASSET_INVENTORY_UNCORROBORATED");
});
test("modifier les 10 % d'actifs D/E est rejeté",()=>{
 reject(x=>x.assets_2025.poor_very_poor_share_pct=21,"ASSET_INVENTORY_UNCORROBORATED");
});
test("une conduite supplémentaire sans source est rejetée",()=>{
 reject(x=>x.assets_2025.asset_types[0].count=100000,"ASSET_INVENTORY_UNCORROBORATED");
});
test("inventer un audit Nova est rejeté",()=>{
 reject(x=>x.assets_2025.external_nova_audit_complete=true,"ASSET_STOCK_NOT_FUTURE_CASH");
});
test("inventer un coût de réhabilitation dans les comptes 2024 est rejeté",()=>{
 reject(x=>x.municipal_water_operating_2024.derived_repair_backlog_cad=20600000000,"ANNUAL_EXPENSE_STOCK_CONFUSION");
});
test("déclarer les deux échantillons identiques est rejeté",()=>{
 reject(x=>x.municipal_water_operating_2024.same_scope_as_ceriu_sample=true,"ANNUAL_EXPENSE_STOCK_CONFUSION");
});
test("confondre 31 décembre 2026 avec la date d'adoption complète est rejeté",()=>{
 reject(x=>x.government_plans.engagement_is_final_pga_approval=true,"PGA_DEADLINE_MISSTATED");
});
test("changer la date d'engagement sans preuve est rejeté",()=>{
 reject(x=>x.government_plans.invited_commitment_deadline="2026-01-01","PGA_DEADLINE_MISSTATED");
});
test("une baisse de taxes non financée est rejetée",()=>{
 reject(x=>x.decisions.tax_reduction_financed=true,"APPROVAL_PREMATURE");
});
test("la continuité d'emploi ne peut être certifiée à partir des tuyaux",()=>{
 reject(x=>x.decisions.employee_rights_certified=true,"APPROVAL_PREMATURE");
});
test("les actifs du Québec souverain ne sont pas automatiquement financés",()=>{
 reject(x=>x.continuity_scenarios[1].annual[0].asset_renewal_capex_cad=20600000000,"DECADAL_BUDGET_INVENTED");
});
test("le financement fédéral n'est pas présumé dans Québec au Canada",()=>{
 reject(x=>x.continuity_scenarios[0].annual[0].grants_net_cad=100000,"DECADAL_BUDGET_INVENTED");
});
test("un exercice en moins rend le modèle décennal invalide",()=>{
 reject(x=>x.continuity_scenarios[0].annual.pop(),"DECADAL_BUDGET_INVENTED");
});
test("les besoins de preuve ne peuvent être déclarés tous satisfaits",()=>{
 reject(x=>x.unmet_evidence[0].status="COMPLETE","PROOFS_UNSUPPORTED");
});
test("un risque de coût futur n'est pas un financement approuvé",()=>{
 reject(x=>x.risk_register[0].remediation_cost_cad=50000000,"ASSET_RISKS_NOT_FINANCED");
});
test("un cumul routier de tranchée non vérifié est rejeté",()=>{
 reject(x=>x.accounting_barriers.road_trench_restoration_not_added_to_separate_total=false,"ACCOUNTING_DOUBLE_COUNT_RISK");
});
test("un score politique de 48 ne résulte pas d'un registre de patrimoine",()=>{
 reject(x=>x.programme_score_after=48,"FALSE_SCORE_OR_STATUS");
});
test("changer la source primaire du CERIU est rejeté",()=>{
 reject(x=>x.sources[0].url="https://example.com/a.pdf","PROVENANCE_NOT_REVIEWED");
});
test("rompre les données MAMH historiques bloque la comparaison",()=>{
 const z=clone(g016j);z.non_overlapping_observed_subsets[0].y2024=0;
 const r=inspectG016kWaterContinuity(d,z,g016h);
 assert.ok(r.errors.includes("ANNUAL_EXPENSE_STOCK_CONFUSION"));
});
test("une source fiscale MAMH amont non cohérente bloque le contrôle",()=>{
 const z=clone(g016h);z.annual[0].total_expenses_cad=0;
 const r=inspectG016kWaterContinuity(d,g016j,z);
 assert.ok(r.errors.includes("ANNUAL_EXPENSE_STOCK_CONFUSION"));
});

test("147,9 G$ d'actifs sont évalués sur des critères théoriques ou subjectifs",()=>{
 const a=d.assets_2025;
 assert.equal(a.value_assessed_age_or_judgment_gcad,147.9);
 assert.equal(a.poor_assets_age_or_judgment_gcad,8.8);
 assert.equal(a.acceptable_assets_age_or_judgment_gcad,39.1);
 assert.equal(a.poor_assets_in_cities_above_100k_gcad,14.8);
 assert.equal(a.poor_assets_in_cities_above_100k_share_approx_pct,72);
});
test("le ratio de données estimées et la concentration urbaine ne peuvent être inventés",()=>{
 reject(x=>x.assets_2025.value_assessed_age_or_judgment_gcad=100.0,"ASSET_INVENTORY_UNCORROBORATED");
 reject(x=>x.assets_2025.poor_assets_in_cities_above_100k_gcad=20.0,"ASSET_INVENTORY_UNCORROBORATED");
});

test("la page publique décrit G0.16k sans transformer les actifs en budget",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/id="actifs-eau-g016k"/);
 assert.match(html,/197,6 G\$/);
 assert.match(html,/20,6 G\$/);
 assert.match(html,/75 %/);
 assert.match(html,/d'ici le 31 décembre 2026/);
 assert.match(html,/Aucun impôt n'est déclaré supprimable/);
 assert.match(html,/47 % inchangé/);
});
