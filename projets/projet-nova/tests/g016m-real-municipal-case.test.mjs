import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016mWarwickPilot} from "../assets/g016m-real-municipal-case-core.mjs";

const read=async file=>JSON.parse(await readFile(new URL("../data/"+file,import.meta.url),"utf8"));
const [d,g016l]=await Promise.all([
  read("cas-municipal-reel-g0-16m-warwick-eau-2025-2026.json"),
  read("financement-eau-g0-16l-pga-primeau-tecq-2026.json")
]);
const inspect=x=>inspectG016mWarwickPilot(x,g016l);
const copy=x=>structuredClone(x);
const reject=(change,error)=>{
 const x=copy(d);change(x);const r=inspect(x);
 assert.equal(r.ok,false,r.errors.join(","));
 assert.ok(r.errors.includes(error),r.errors.join(","));
};
test("cas Warwick réel et score 47 sans politique Nova approuvée",()=>{
 const r=inspect(d);assert.equal(r.ok,true,r.errors.join(","));
 assert.equal(r.programme_score,47);assert.equal(r.real_source_backed_projects,1);
});
test("subvention PRIMEAU de Warwick officiellement accordée, pas versée prouvée",()=>{
 const a=d.cases[0].award;assert.equal(a.amount_cad,14668901);
 assert.equal(a.cash_paid_verified_cad,null);
 assert.equal(a.status,"AWARDED_NOT_PAYMENT_VERIFIED");
});
test("coût maximal admissible distinct du coût total",()=>{
 const a=d.cases[0].award;
 assert.equal(a.max_eligible_cost_cad,15440948);
 assert.equal(Math.round(100*a.amount_cad/a.max_eligible_cost_cad),95);
 assert.equal(d.guards.eligible_grant_cost_not_lifetime_full_cost,true);
});
test("engagement gouvernemental ventilé sur deux années 2025-2027",()=>{
 const s=d.cases[0].award.government_commitments;
 assert.equal(s[0].committed_cad+s[1].committed_cad,14668901);
 assert.equal(d.guards.commitment_schedule_not_bank_payment,true);
});
test("PTI Warwick 2026 : 20 074 664 dollars, trois sources exactes",()=>{
 const p=d.cases[0].city_2026_capital_plan;
 assert.equal(p.project_cost_line_cad,20074664);
 assert.equal(p.same_primeau_award_cad+p.water_fund_budgeted_cad+
   p.borrowing_budgeted_cad,20074664);
});
test("emprunt du PTI 2026 n'est pas dette réellement tirée",()=>{
 const p=d.cases[0].city_2026_capital_plan;
 assert.equal(p.borrowing_budgeted_cad,5068940);
 assert.equal(p.actual_paid_or_borrowed_verified_cad,null);
});
test("règlement 404-2025 : 27 988 101 dollars de dépenses et d'emprunt autorisés",()=>{
 const b=d.cases[0].city_2025_bylaw;
 assert.equal(b.authorised_total_spending_cad,27988101);
 assert.equal(b.gross_borrowing_authorization_cad,27988101);
 assert.equal(b.outstanding_debt_verified_cad,null);
});
test("trois postes du règlement 2025 se rapprochent sans double compte",()=>{
 const b=d.cases[0].city_2025_bylaw;
 assert.equal(b.building_scope_cad+b.pretreatment_equipment_scope_cad+
    b.hardness_equipment_scope_cad,27988101);
});
test("la taxe spéciale dans le règlement doit être prise en compte dans l'impact citoyen",()=>{
 const b=d.cases[0].city_2025_bylaw;
 assert.equal(b.special_tax_on_water_served_properties_in_bylaw,true);
 assert.equal(d.guards.special_local_tax_may_have_household_effect,true);
});
test("la ligne PTI 2026 et le règlement 2025 ne sont jamais additionnés",()=>{
 assert.equal(d.guards.do_not_sum_pti_and_bylaw,true);
 assert.equal(d.cases[0].city_2025_bylaw.identical_scope_to_2026_pti,false);
});
test("état de chantier juin 2026 non assimilé au coût final vérifié",()=>{
 const p=d.cases[0].progress;
 assert.equal(p.municipal_update_date,"2026-06-25");
 assert.equal(p.reported_budget_used_percent,50);
 assert.equal(p.independent_final_cost_verified,false);
});
test("six preuves locales restent ouvertes",()=>{
 assert.equal(d.cases[0].missing_proofs.length,6);
 assert.ok(d.cases[0].missing_proofs.every(x=>x.status==="OPEN"));
});
test("sept liens primaires de provenance, seul MAMH PRIMEAU revu visuellement en PDF",()=>{
 assert.equal(d.sources.length,7);
 assert.equal(d.sources.filter(x=>x.pdf_visual_verified).length,1);
 assert.ok(d.sources.every(x=>x.url.startsWith("https://")));
});
test("étude de cas du bénéficiaire Warwick, jamais subvention à Projet Nova",()=>{
 assert.equal(d.cases[0].award.beneficiary,"VILLE_DE_WARWICK_NOT_NOVA");
 assert.equal(d.guards.no_grant_to_nova,true);
});
test("deux cadres constitutionnels sur dix ans restent sans budget",()=>{
 assert.deepEqual(d.constitutional_budget.map(x=>x.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
 assert.ok(d.constitutional_budget.every(x=>x.years.length===10));
 assert.ok(d.constitutional_budget.every(x=>x.years.every(y=>y.net_balance_cad===null)));
});
test("aucun montant total dépensé, épargné ou encaissé Nova inventé",()=>{
 assert.equal(d.summary.grant_cash_disbursements_verified_cad,null);
 assert.equal(d.summary.actual_debt_cad,null);
 assert.equal(d.summary.net_cost_of_nova_reform_cad,null);
});
test("aide gonflée sans publication rejetée",()=>{
 reject(x=>x.cases[0].award.amount_cad=20000000,"GRANT_COMMITMENT_NOT_PAYMENT");
});
test("montant admissible transformé en coût final rejeté",()=>{
 reject(x=>x.cases[0].award.max_eligible_cost_cad=20074664,"GRANT_COMMITMENT_NOT_PAYMENT");
});
test("montant engagé fiscal altéré rejeté",()=>{
 reject(x=>x.cases[0].award.government_commitments[0].committed_cad=10000000,"GRANT_COMMITMENT_NOT_PAYMENT");
});
test("un versement inventé à Warwick est refusé",()=>{
 reject(x=>x.cases[0].award.cash_paid_verified_cad=14668901,"GRANT_COMMITMENT_NOT_PAYMENT");
});
test("la subvention déclarée payée sans facture est refusée",()=>{
 reject(x=>x.cases[0].award.status="PAYMENT_DOCUMENTED","GRANT_COMMITMENT_NOT_PAYMENT");
});
test("le PTI 2026 faussement réduit bloque le rapprochement",()=>{
 reject(x=>x.cases[0].city_2026_capital_plan.project_cost_line_cad=19000000,"CITY_2026_PLAN_NOT_RECONCILED");
});
test("le Fonds eau potable changé dans le PTI est refusé",()=>{
 reject(x=>x.cases[0].city_2026_capital_plan.water_fund_budgeted_cad=0,"CITY_2026_PLAN_NOT_RECONCILED");
});
test("l'emprunt du PTI ne devient pas une dette tirée",()=>{
 reject(x=>x.cases[0].city_2026_capital_plan.actual_paid_or_borrowed_verified_cad=5068940,"CITY_2026_PLAN_NOT_RECONCILED");
});
test("l'autorisation de 27 988 101 dollars ne devient pas emprunt effectivement tiré",()=>{
 reject(x=>x.cases[0].city_2025_bylaw.outstanding_debt_verified_cad=27988101,"BYLAW_BORROWING_VERSUS_ACTUAL_DEBT");
});
test("une taxe spéciale omise fausse les risques distributifs",()=>{
 reject(x=>x.cases[0].city_2025_bylaw.special_tax_on_water_served_properties_in_bylaw=false,"BYLAW_BORROWING_VERSUS_ACTUAL_DEBT");
});
test("la confusion périmètre 2025/2026 est bloquée",()=>{
 reject(x=>x.guards.do_not_sum_pti_and_bylaw=false,"SCOPES_AND_FISCAL_PROTECTION");
});
test("une seule étude de cas ne devient pas une statistique du Québec",()=>{
 reject(x=>x.summary.real_cases_documented=1056,"FALSELY_AGGREGATED_PROJECT_MONEY");
});
test("un coût net Nova inventé est rejeté",()=>{
 reject(x=>x.summary.net_cost_of_nova_reform_cad=5000000,"FALSELY_AGGREGATED_PROJECT_MONEY");
});
test("l'ajout d'un faux bénéficiaire est refusé",()=>{
 reject(x=>x.cases.push(copy(x.cases[0])),"SINGLE_REAL_CASE_REQUIRED");
});
test("une loi fiscale dite adoptée est refusée",()=>{
 reject(x=>x.decision.new_fiscal_policy_approved=true,"PREMATURE_GOVERNMENT_READINESS");
});
test("le score ne passe pas à 48 sur la seule base de Warwick",()=>{
 reject(x=>x.score_after=48,"PROGRAMME_MATURITY_NOT_PROVEN");
});
test("la ligne PRIMEAU source ne peut disparaître",()=>{
 reject(x=>x.sources.splice(1,1),"SOURCE_TRACEABILITY");
});
test("le budget du Québec souverain ne reprend pas automatiquement l'aide",()=>{
 reject(x=>x.constitutional_budget[1].years[0].award_paid_cad=14668901,"DECADAL_BUDGET_UNAUDITED");
});
test("une preuve locale n'est pas considérée clos par magie",()=>{
 reject(x=>x.cases[0].missing_proofs[0].status="RESOLVED","PROOFS_FALSELY_CLOSED");
});
test("la date de mise en fonction juin 2027 est une prévision, pas une certification",()=>{
 reject(x=>x.cases[0].progress.finished_as_of_november_verified=true,"NON_FINAL_CONSTRUCTION_STATUS");
});
test("le dossier antérieur G0.16l reste non certifié",()=>{
 const old=copy(g016l);old.decisions.g016l_financing_certified=true;
 const r=inspectG016mWarwickPilot(d,old);
 assert.equal(r.ok,false);
 assert.ok(r.errors.includes("INHERITED_G0_16L_NOT_CERTIFIED"));
});

test("la page d’avancement G0.16m présente le cas réel sans financement fictif",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/id="cas-warwick-g016m"/);
 assert.match(html,/14 668 901 \$/);
 assert.match(html,/20 074 664 \$/);
 assert.match(html,/27,988 M\$/);
 assert.match(html,/47 % inchangé/);
});
test("la page d’avancement maintient les avertissements sur les emprunts et versements",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/projet municipal existant, et non un projet ou une subvention attribuée à Nova/);
 assert.match(html,/Une autorisation d'emprunt n'est pas une dette déjà tirée/);
 assert.match(html,/un engagement gouvernemental n'est pas un paiement reçu/);
 assert.match(html,/aucune attestation de versements/);
});
