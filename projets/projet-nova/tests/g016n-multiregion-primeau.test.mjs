import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {validateG016nMultiRegion} from "../assets/g016n-multiregion-primeau-core.mjs";
const load=async path=>JSON.parse(await readFile(new URL("../data/"+path,import.meta.url),"utf8"));
const [d,previous]=await Promise.all([
 load("comparatif-cas-reels-primeau-g0-16n-2025.json"),
 load("cas-municipal-reel-g0-16m-warwick-eau-2025-2026.json")
]);
const copy=x=>structuredClone(x);
const check=x=>validateG016nMultiRegion(x,previous);
const mustFail=(alter,expected)=>{
 const x=copy(d);alter(x);const r=check(x);
 assert.equal(r.ok,false);
 assert.ok(r.errors.includes(expected),r.errors.join(","));
};
test("sept projets publics de sept régions passent la comparaison interne",()=>{
 const r=check(d);assert.equal(r.ok,true,r.errors.join(","));
 assert.equal(r.projects_in_non_random_sample,7);
 assert.equal(r.regions,7);assert.equal(r.programme_score,47);
});
test("source primaire MAMH 2025-082 et pages PDF 3 et 4",()=>{
 assert.equal(d.sources[0].id,"MAMH_2025_082");
 assert.deepEqual(d.sources[0].visual_pdf_pages_zero_based,[3,4]);
 assert.equal(d.scope.list_date,"2025-10-08");
});
test("les sept montants sont des aides accordées non des versements",()=>{
 assert.ok(d.projects.every(x=>x.actual_disbursement_cad===null));
 assert.equal(d.derived_summary.confirmed_paid_sum_cad,null);
});
test("les sept coûts sont des plafonds admissibles et non des coûts globaux",()=>{
 assert.ok(d.projects.every(x=>x.actual_total_project_cost_cad===null));
 assert.equal(d.scope.maximum_eligible_cost_not_total_project_cost,true);
});
test("somme des sept aides PRIMEAU : 156721180 dollars",()=>{
 assert.equal(d.projects.reduce((n,p)=>n+p.awarded_financial_aid_cad,0),156721180);
 assert.equal(d.derived_summary.sum_awarded_cad,156721180);
});
test("somme des coûts admissibles maximum : 188322869 dollars",()=>{
 assert.equal(d.projects.reduce((n,p)=>n+p.max_admissible_cost_cad,0),188322869);
});
test("différence admissible-aide n'est pas un coût municipal final",()=>{
 assert.equal(d.derived_summary.sum_max_eligible_minus_awarded_cad,31601689);
 assert.equal(d.derived_summary.award_less_than_eligible_not_municipal_total_cost_gap,true);
});
test("Warwick n'est pas réimporté comme un huitième projet",()=>{
 assert.equal(d.projects.filter(x=>x.id==="WARWICK").length,1);
 assert.ok(d.projects[0].prior_case_link?.includes("g0-16m"));
});
test("Gatineau : station d'eau 75942667 admissibles, 56957000 accordés",()=>{
 const p=d.projects.find(x=>x.id==="GATINEAU");
 assert.equal(p.max_admissible_cost_cad,75942667);
 assert.equal(p.awarded_financial_aid_cad,56957000);
});
test("Laval : bassin Cartier 31004168 admissibles, 23253126 accordés",()=>{
 const p=d.projects.find(x=>x.id==="LAVAL");
 assert.equal(p.max_admissible_cost_cad,31004168);
 assert.equal(p.awarded_financial_aid_cad,23253126);
});
test("Port-Daniel-Gascons : admissibles 44528918, aide 42302472",()=>{
 const p=d.projects.find(x=>x.id==="PORT_DANIEL_GASCONS");
 assert.equal(p.max_admissible_cost_cad,44528918);
 assert.equal(p.awarded_financial_aid_cad,42302472);
});
test("Anticosti : aide égale au plafond admissible ne garantit pas coût total nul",()=>{
 const p=d.projects.find(x=>x.id==="ILE_DANTICOSTI");
 assert.equal(p.max_admissible_cost_cad,8354735);
 assert.equal(p.awarded_financial_aid_cad,8354735);
 assert.equal(p.actual_total_project_cost_cad,null);
});
test("Val-d'Or et La Doré sont deux dossiers distincts",()=>{
 const v=d.projects.find(x=>x.id==="VAL_DOR");
 const l=d.projects.find(x=>x.id==="LA_DORE");
 assert.equal(v.awarded_financial_aid_cad,10318289);
 assert.equal(l.awarded_financial_aid_cad,866657);
});
test("les dates de début et de fin sont annoncées en 2025 pas certifiées",()=>{
 assert.equal(d.scope.planned_construction_dates_not_actual_completion,true);
 assert.ok(d.projects.every(x=>x.completion_date_independently_verified===null));
});
test("échantillon raisonné, ni tirage aléatoire ni estimation de tout le Québec",()=>{
 assert.equal(d.derived_summary.sum_is_sample_only_not_quebec_total,true);
 assert.match(d.scope.selection,/NOT_RANDOM/);
});
test("Port-Daniel : 42302472 PRIMEAU + 14293528 emprunt = 56596000",()=>{
 const p=d.port_daniel_municipal_bylaw;
 assert.equal(p.promise_applied_to_financing_cad+p.borrowing_authorized_cad,56596000);
 assert.equal(p.planned_total_project_spending_cad,56596000);
});
test("Port-Daniel : emprunt autorisé sur quarante ans pas une dette tirée",()=>{
 const p=d.port_daniel_municipal_bylaw;
 assert.equal(p.borrowing_term_years,40);
 assert.equal(p.actual_borrowing_drawdown_cad,null);
});
test("Port-Daniel : taxation générale et secteurs desservis repérés, montant annuel inconnu",()=>{
 const p=d.port_daniel_municipal_bylaw;
 assert.equal(p.special_general_property_tax_share_borrowing_pct,14);
 assert.equal(p.special_served_sector_tax_and_compensation_reported,true);
 assert.equal(p.annual_special_tax_amount_cad,null);
});
test("Port-Daniel : texte PDF vérifié, capture visuelle indisponible",()=>{
 const p=d.port_daniel_municipal_bylaw;
 assert.equal(p.pdf_screenshot_observed,false);
 assert.equal(p.pdf_screenshot_cache_miss,true);
});
test("les deux modèles de dix ans restent non chiffrés et non homologués",()=>{
 assert.deepEqual(d.fiscal_continuity.two_constitutional_scenarios.map(x=>x.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
 assert.ok(d.fiscal_continuity.two_constitutional_scenarios.every(x=>x.annual.length===10));
 assert.ok(d.fiscal_continuity.two_constitutional_scenarios.every(x=>x.annual.every(y=>y.balance_cad===null)));
});
test("une population municipale entièrement couverte ne doit pas être inventée",()=>{
 mustFail(x=>x.decision.all_quebec_municipal_project_population_covered=true,"UNWARRANTED_REFORM_APPROVAL");
});
test("des paiements publics non documentés ne doivent pas être inventés",()=>{
 mustFail(x=>x.projects[1].actual_disbursement_cad=56957000,"MAMH_ROW_MISMATCH");
});
test("une aide Gatineau changée sans preuve est refusée",()=>{
 mustFail(x=>x.projects[1].awarded_financial_aid_cad=50000000,"MAMH_ROW_MISMATCH");
});
test("un plafond admissible Laval falsifié est refusé",()=>{
 mustFail(x=>x.projects[2].max_admissible_cost_cad=25000000,"MAMH_ROW_MISMATCH");
});
test("la date fin annoncée de Port-Daniel ne peut être déclarée définitive",()=>{
 mustFail(x=>x.projects[3].completion_date_independently_verified="2025-10-31","MAMH_ROW_MISMATCH");
});
test("une hausse artificielle à 48 sur l'existence d'un tableau est refusée",()=>{
 mustFail(x=>x.programme_score_after=48,"SCORE_NOT_PROVEN");
});
test("modifier une région parmi les sept échoue",()=>{
 mustFail(x=>x.projects[6].region="Côte-Nord","MAMH_ROW_MISMATCH");
});
test("doublonner Warwick dans la liste échoue",()=>{
 mustFail(x=>x.projects.push(copy(x.projects[0])),"MAMH_ROW_MISMATCH");
});
test("faire croire à un échantillon représentatif est refusé",()=>{
 mustFail(x=>x.scope.selection="RANDOM_NATIONAL_SAMPLE","SAMPLE_NOT_REPRESENTATIVE");
});
test("une source du ministère manquante échoue",()=>{
 mustFail(x=>x.sources[0].url="https://example.com","PROVENANCE_UNSUPPORTED");
});
test("inventer la photo du règlement de Port-Daniel est refusé",()=>{
 mustFail(x=>x.port_daniel_municipal_bylaw.pdf_screenshot_observed=true,"MUNICIPAL_BYLAW_OR_DEBT_CONFUSION");
});
test("inventer une dette réelle de Port-Daniel est refusé",()=>{
 mustFail(x=>x.port_daniel_municipal_bylaw.actual_borrowing_drawdown_cad=14293528,"MUNICIPAL_BYLAW_OR_DEBT_CONFUSION");
});
test("une fausse taxe annuelle Port-Daniel est refusée",()=>{
 mustFail(x=>x.port_daniel_municipal_bylaw.annual_special_tax_amount_cad=10000,"MUNICIPAL_BYLAW_OR_DEBT_CONFUSION");
});
test("un faux refinancement Port-Daniel est refusé",()=>{
 mustFail(x=>x.port_daniel_municipal_bylaw.promise_applied_to_financing_cad=30000000,"MUNICIPAL_BYLAW_OR_DEBT_CONFUSION");
});
test("la somme du portefeuille ne devient pas l'argent disponible pour Nova",()=>{
 mustFail(x=>x.derived_summary.budget_savings_nova_cad=156721180,"DERIVED_SUMMARY_INCORRECT");
});
test("un financement fédéral souverain inventé est refusé",()=>{
 mustFail(x=>x.fiscal_continuity.two_constitutional_scenarios[1].annual[0].grants_paid_cad=14668901,"BUDGET_AND_WORKERS_UNFUNDED");
});
test("suppression fiscale sans vérification est refusée",()=>{
 mustFail(x=>x.decision.two_tax_financing_proven=true,"UNWARRANTED_REFORM_APPROVAL");
});
test("les six questions restent expressément ouvertes",()=>{
 assert.equal(d.unresolved_questions.length,6);
 mustFail(x=>x.unresolved_questions[0].status="DONE","PROOFS_NOT_REVIEWED");
});
test("l'étude Warwick ne peut être remplacée par un autre montant",()=>{
 const prior=copy(previous);prior.cases[0].award.amount_cad=0;
 const z=validateG016nMultiRegion(d,prior);
 assert.ok(z.errors.includes("G016M_PREDECESSOR_MISMATCH"));
});
