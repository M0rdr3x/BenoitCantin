import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016jServiceExpenses} from "../assets/g016j-municipal-services-core.mjs";

const load=async file=>JSON.parse(await readFile(new URL("../data/"+file,import.meta.url),"utf8"));
const [d,h,i]=await Promise.all([
 load("ventilation-charges-municipales-g0-16j-2024.json"),
 load("finances-municipales-g0-16h-2024.json"),
 load("risque-transition-taxes-locales-g0-16i-2024.json")
]);
const clone=x=>structuredClone(x);
const check=x=>inspectG016jServiceExpenses(x,h,i);
const shouldFail=(modify,expected)=>{
 const x=clone(d);modify(x);const result=check(x);
 assert.equal(result.ok,false);
 assert.ok(result.errors.includes(expected),result.errors.join(","));
};
const summed=(rows,key)=>rows.reduce((n,x)=>n+x[key],0);

test("la référence documentaire est cohérente, sans réforme homologuée",()=>{
 const v=check(d);
 assert.equal(v.ok,true,v.errors.join(","));
 assert.equal(v.programme_score,47);
 assert.equal(v.audited_nova_replacement,false);
});
test("total 2024 : 28366959822 des 10 fonctions",()=>{
 assert.equal(d.functions.length,10);
 assert.equal(summed(d.functions,"y2024"),28366959822);
 assert.equal(d.reference_total.y2024,28366959822);
});
test("total 2023 : 26469048805 des 10 fonctions",()=>{
 assert.equal(summed(d.functions,"y2023"),26469048805);
 assert.equal(d.reference_total.y2023,26469048805);
});
test("source PDF paginée et détail indiqué non audité",()=>{
 assert.deepEqual(d.primary_pdf.pages.map(x=>x.pdf_page_zero_based),[7,51,52]);
 assert.equal(d.primary_pdf.pages[1].section_detailed_not_audited,true);
 assert.equal(d.primary_pdf.pages[2].section_detailed_not_audited,true);
});
test("la couverture de 1056 municipalités n'est pas exhaustive",()=>{
 assert.equal(d.primary_pdf.municipalities_count,1056);
 assert.equal(d.primary_pdf.non_exhaustive,true);
 assert.equal(d.maturity.covers_all_municipalities,false);
});
test("34 lignes détaillées reconstituent quatre fonctions sans autre charge",()=>{
 assert.equal(d.details.length,34);
 for(const key of ["SECURITE","TRANSPORT","MILIEU","SANTE_BIEN_ETRE"]){
   const rows=d.details.filter(x=>x.group===key);
   const parent=d.functions.find(x=>x.id===key);
   assert.equal(summed(rows,"y2024"),parent.y2024);
   assert.equal(summed(rows,"y2023"),parent.y2023);
 }
});
test("eau et égouts : quatre dépenses historiques, 2024 et 2023",()=>{
 const row=d.non_overlapping_observed_subsets.find(x=>x.id==="EAU_EGOUTS");
 assert.equal(row.members.length,4);
 assert.equal(row.y2024,2519426792);
 assert.equal(row.y2023,2363825596);
 assert.equal(row.extra_sum_on_function_expenses,false);
});
test("voirie et déneigement : montants sans doublon avec transport",()=>{
 const row=d.non_overlapping_observed_subsets.find(x=>x.id==="VOIRIE_DENEIGEMENT");
 assert.equal(row.y2024,3711874237);
 assert.equal(row.y2023,3639527054);
 assert.equal(d.baseline_links.double_count_transport_and_road,false);
});
test("sécurité incendie : premiers répondants et autres",()=>{
 const row=d.non_overlapping_observed_subsets.find(x=>x.id==="INCENDIE");
 assert.equal(row.y2024,1533111877);
 assert.equal(row.members.length,2);
});
test("police, incendie et sécurité civile dans un seul total 2024",()=>{
 const costs=d.details.filter(x=>x.group==="SECURITE");
 assert.equal(summed(costs,"y2024"),4510158652);
});
test("les frais de financement sont déjà inclus dans les charges",()=>{
 assert.equal(d.functions.find(x=>x.id==="FINANCEMENT").y2024,1332060734);
 assert.equal(d.baseline_links.finance_charges_already_in_total,true);
});
test("aucune dépense historique n'est assimilée à une dépense évitable",()=>{
 assert.equal(d.maturity.costs_not_automatically_avoidable_if_tax_removed,true);
 assert.equal(d.maturity.costs_assignable_to_abolished_taxes,false);
});
test("la continuité des services et des retraites reste à chiffrer",()=>{
 assert.equal(d.service_continuity.length,8);
 assert.ok(d.service_continuity.every(x=>x.service_continuity_cost_per_year_cad===null&&
 x.replacement_funding_verified_cad===null));
});
test("deux budgets sur dix exercices restent non certifiés",()=>{
 assert.deepEqual(d.separate_scenarios.map(x=>x.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
 assert.ok(d.separate_scenarios.every(x=>x.annual.length===10));
 assert.ok(d.separate_scenarios.every(x=>x.annual.every(y=>y.net_balance_cad===null)));
});
test("l'exercice 2026–2027 ne réutilise pas arbitrairement le chiffre de 2024",()=>{
 assert.equal(d.separate_scenarios[0].annual[0].municipal_service_cost_cad,null);
 assert.equal(d.separate_scenarios[1].annual[0].municipal_service_cost_cad,null);
});
test("un nouveau rapport prétendument audité est bloqué",()=>{
 shouldFail(x=>x.primary_pdf.external_independent_reviewer_for_nova=true,"SOURCE_SCOPE_OR_AUDIT");
});
test("un nombre de municipalités gonflé est bloqué",()=>{
 shouldFail(x=>x.primary_pdf.municipalities_count=1100,"SOURCE_SCOPE_OR_AUDIT");
});
test("un texte de provenance remplacé est bloqué",()=>{
 shouldFail(x=>x.primary_pdf.pages[2].pdf_page_zero_based=53,"SOURCE_SCOPE_OR_AUDIT");
});
test("une dépense administrative réduite fictivement est bloquée",()=>{
 shouldFail(x=>x.functions[0].y2024=2000000000,"FUNCTION_EXPENSE_RECONCILIATION");
});
test("une économie artificielle de déneigement est bloquée",()=>{
 shouldFail(x=>x.details.find(y=>y.id==="DENEIGEMENT").y2024=0,"DETAIL_EXPENSE_PROVENANCE");
});
test("un poste d'eau artificiellement gonflé est bloqué",()=>{
 shouldFail(x=>x.details.find(y=>y.id==="EAU_DISTRIBUTION").y2024=1000000000,"DETAIL_EXPENSE_PROVENANCE");
});
test("un poste municipal manquant est bloqué",()=>{
 shouldFail(x=>x.details.pop(),"DETAIL_EXPENSE_PROVENANCE");
});
test("un sous-total eau altéré est bloqué",()=>{
 shouldFail(x=>x.non_overlapping_observed_subsets[0].y2024=0,"PARTIAL_SERVICE_SUBTOTAL");
});
test("le double comptage voirie-transport est bloqué",()=>{
 shouldFail(x=>x.baseline_links.double_count_transport_and_road=true,"REFERENCE_ACCOUNTING_RULES");
});
test("les frais de financement ne s'ajoutent pas au total",()=>{
 shouldFail(x=>x.baseline_links.finance_charges_already_in_total=false,"REFERENCE_ACCOUNTING_RULES");
});
test("marquer toutes les municipalités couvertes sans preuve est interdit",()=>{
 shouldFail(x=>x.maturity.covers_all_municipalities=true,"FICTITIOUS_SERVICE_CERTIFICATION");
});
test("une projection 2025 inventée est refusée",()=>{
 shouldFail(x=>x.maturity.annual_2025_financial_values_verified=true,"FICTITIOUS_SERVICE_CERTIFICATION");
});
test("les coûts en 2026 ne sont pas automatiquement financés",()=>{
 shouldFail(x=>x.maturity.expenditure_needs_2026_2036_financed=true,"FICTITIOUS_SERVICE_CERTIFICATION");
});
test("un budget d'eau futur imposé sans données est refusé",()=>{
 shouldFail(x=>x.service_continuity[0].service_continuity_cost_per_year_cad=2519426792,"SERVICE_CONTINUITY_NOT_FUNDED");
});
test("une source de remplacement fictive du service de voirie est refusée",()=>{
 shouldFail(x=>x.service_continuity[1].replacement_funding_verified_cad=3711874237,"SERVICE_CONTINUITY_NOT_FUNDED");
});
test("un revenu souverain imaginaire est refusé",()=>{
 shouldFail(x=>x.separate_scenarios[1].annual[0].local_tax_replacement_revenue_cad=17188134046,"PREMATURE_DECADAL_BUDGET");
});
test("un exercice décennal supprimé est refusé",()=>{
 shouldFail(x=>x.separate_scenarios[0].annual.pop(),"PREMATURE_DECADAL_BUDGET");
});
test("une approbation juridique de réforme fictive est refusée",()=>{
 shouldFail(x=>x.decision.tax_removal_authorized=true,"POLICY_PREMATURE");
});
test("la hausse à 48 points ne résulte pas de dépenses historiques",()=>{
 shouldFail(x=>x.score_after=48,"FALSE_PROGRAMME_STATUS");
});
test("une catégorie fiscale inconnue ne devient pas un service chiffré",()=>{
 shouldFail(x=>x.conditions_for_next_gate[0].complete=true,"CONDITIONS_FALSE_APPROVAL");
});
test("chiffres G0.16h falsifiés brisent la chaîne",()=>{
 const source=clone(h);source.annual[0].total_expenses_cad=20000000000;
 const res=inspectG016jServiceExpenses(d,source,i);
 assert.equal(res.ok,false);
 assert.ok(res.errors.includes("PREDECESSOR_BASE_MISMATCH"));
});
test("bilan de référence G0.16i falsifié brise la chaîne",()=>{
 const source=clone(i);source.fixed_2024_baseline.total_expenses_cad=0;
 const res=inspectG016jServiceExpenses(d,h,source);
 assert.equal(res.ok,false);
 assert.ok(res.errors.includes("PREDECESSOR_BASE_MISMATCH"));
});

test("la page d’avancement G0.16j distingue chiffres et financement non démontré",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/id="depenses-services-g016j"/);
 assert.match(html,/28,367 G\$/);
 assert.match(html,/2,519 G\$/);
 assert.match(html,/3,712 G\$/);
 assert.match(html,/1 056 municipalités locales/);
 assert.match(html,/« Non audité »/);
 assert.match(html,/Viabilité financière Nova non démontrée/);
 assert.match(html,/47 % inchangé/);
});
