import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {verifyG016gTerritorialContinuity} from "../assets/g016g-territorial-continuity-core.mjs";

const read=async file=>JSON.parse(await readFile(new URL("../data/"+file,import.meta.url),"utf8"));
const [data,g014,g015,g016e,g016f]=await Promise.all([
 read("continuite-territoriale-g0-16g-education-municipalites-dette.json"),
 read("registre-assiettes-fiscales-g0-14-2026-2027.json"),
 read("matrice-preuves-g0-15-fiscalite.json"),
 read("pont-financier-g0-16e-2021-2026.json"),
 read("continuite-regimes-g0-16f-2024-2026.json")
]);
const copy=()=>structuredClone(data);
const inspect=d=>verifyG016gTerritorialContinuity(d,g014,g015,g016e,g016f);
const mustFail=(change,code)=>{
 const d=copy();change(d);
 const r=inspect(d);
 assert.equal(r.ok,false);
 assert.ok(r.errors.includes(code),r.errors.join(","));
};
test("base école municipalité employés dette: valide sans certification fictive",()=>{
 const result=inspect(data);
 assert.equal(result.ok,true,result.errors.join(","));
 assert.equal(result.programme_score,47);
 assert.equal(result.legal_reviews_completed,0);
 assert.equal(result.certified_scenarios,0);
});
test("la taxe scolaire 1301 M$ n'est pas une taxe foncière municipale",()=>{
 const f=data.source_facts.school_property_tax;
 assert.equal(f.amount_mcad,1301);
 assert.equal(f.same_as_municipal_property_tax,false);
 assert.equal(data.source_facts.municipalities.aggregate_property_tax_revenue_mcad,null);
});
test("70 % de l'UMQ est un constat d'association et pas une statistique officielle auditee",()=>{
 const f=data.source_facts.municipalities;
 assert.equal(f.umq_claim_property_share_pct,70);
 assert.equal(f.umq_claim_is_independent_audited_nova_data,false);
 assert.equal(data.origins.find(x=>x.id==="MUNICIPAL_UMQ").source_type,"STAKEHOLDER_ASSOCIATION");
});
test("dette : 10516 M$ de service ne mesurent pas le stock",()=>{
 const f=data.source_facts.debt;
 assert.equal(f.government_service_2026_2027_mcad,10516);
 assert.equal(f.debt_stock_actual_mcad,null);
 assert.equal(f.net_debt_not_same_as_annual_service,true);
});
test("deux scénarios distincts, aucune valeur financière Nova inventée",()=>{
 assert.deepEqual(data.scenarios.map(x=>x.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
 assert.ok(data.scenarios.every(x=>x.independent_audit===false&&x.debt_service_mcad===null));
});
test("neuf lignes de continuité sont non chiffrées et non homologuées",()=>{
 assert.equal(data.critical_continuity.length,9);
 assert.ok(data.critical_continuity.every(x=>x.baseline_cost_mcad===null&&x.replacement_mcad===null&&!x.legal_signoff&&!x.staff_signoff));
});
test("une majorité des revenus d'une municipalité ne remplace pas les données détaillées",()=>{
 const d=copy();d.source_facts.municipalities.aggregate_property_tax_revenue_mcad=20000;
 assert.ok(inspect(d).errors.includes("MUNICIPAL_TAX_INCOMPLETE"));
});
test("taxe scolaire gonflée à partir d'une projection de mars",()=>{
 mustFail(d=>d.source_facts.school_property_tax.amount_mcad=1311,"SCHOOL_TAX_NOT_SCHOOL_COST");
});
test("taxe scolaire faussement identifiée à une taxe municipale",()=>{
 mustFail(d=>d.source_facts.school_property_tax.same_as_municipal_property_tax=true,"SCHOOL_TAX_NOT_SCHOOL_COST");
});
test("taxe scolaire prétendument supprimée par le programme",()=>{
 mustFail(d=>d.source_facts.school_property_tax.proposed_abolition_approved=true,"SCHOOL_TAX_NOT_SCHOOL_COST");
});
test("suppression scolaire prétendument financée",()=>{
 mustFail(d=>d.source_facts.school_property_tax.replacement_proven_mcad=1301,"SCHOOL_TAX_NOT_SCHOOL_COST");
});
test("source UMQ faussement requalifiée comme loi",()=>{
 mustFail(d=>d.origins.find(x=>x.id==="MUNICIPAL_UMQ").source_type="PRIMARY_LAW","SOURCE_CLASSIFICATION");
});
test("source de référence disparue",()=>{
 mustFail(d=>d.origins.pop(),"SOURCE_PROVENANCE");
});
test("source tenue pour revue indépendante sans rapport",()=>{
 mustFail(d=>d.origins[0].reviewed_independently_for_nova=true,"SOURCE_PROVENANCE");
});
test("municipalités faussement indemnisées",()=>{
 mustFail(d=>d.source_facts.municipalities.funding_transition_estimate_mcad=20000,"MUNICIPAL_TAX_INCOMPLETE");
});
test("l'école ne peut être déclarée financée sans rapprocher les crédits",()=>{
 mustFail(d=>d.source_facts.education.student_service_continuity_certified=true,"EDUCATION_COST_UNKNOWN");
});
test("droits des organismes scolaires particuliers restent à revoir",()=>{
 mustFail(d=>d.source_facts.education.special_status_school_funding_separately_reviewed=true,"EDUCATION_COST_UNKNOWN");
});
test("dette de souveraineté ne peut pas être imputée sans négociation",()=>{
 mustFail(d=>d.source_facts.debt.sovereign_debt_share_allocation_mcad=40000,"DEBT_STOCK_VS_SERVICE");
});
test("service de la dette ne peut être présumé financé par Nova",()=>{
 mustFail(d=>d.source_facts.debt.debt_service_financing_nova_mcad=10516,"DEBT_STOCK_VS_SERVICE");
});
test("définition du ratio de dette reste distincte du service annuel",()=>{
 mustFail(d=>d.source_facts.debt.net_debt_not_same_as_annual_service=false,"DEBT_STOCK_VS_SERVICE");
});
test("réduction de la main d'oeuvre non garantie est refusée",()=>{
 mustFail(d=>d.source_facts.workers.protect_current_workforce_in_transition=false,"WORKER_RIGHTS_UNVERIFIED");
});
test("effectifs inventés bloqués",()=>{
 mustFail(d=>d.source_facts.workers.public_workforce_baseline_full_time_equivalents=120000,"WORKER_RIGHTS_UNVERIFIED");
});
test("régimes de retraite considérés audités sans preuve bloqués",()=>{
 mustFail(d=>d.source_facts.workers.collective_agreements_reviewed=true,"WORKER_RIGHTS_UNVERIFIED");
});
test("la Constitution n'a pas validé une réforme Nova",()=>{
 mustFail(d=>d.legal_competences[0].independent_legal_review=true,"LEGAL_COMPETENCES_NOT_CERTIFIED");
});
test("suppression d'une obligation municipale est refusée",()=>{
 mustFail(d=>d.critical_continuity.splice(3,1),"SERVICE_CONTINUITY_UNFUNDED");
});
test("promesse d'eau municipale financée bloquée",()=>{
 mustFail(d=>d.critical_continuity.find(x=>x.id==="M01").replacement_mcad=1000,"SERVICE_CONTINUITY_UNFUNDED");
});
test("droits des salariés certifiés sans preuve bloqués",()=>{
 mustFail(d=>d.critical_continuity.find(x=>x.id==="W01").staff_signoff=true,"SERVICE_CONTINUITY_UNFUNDED");
});
test("les transferts fédéraux ou une dette héritée ne sont pas présumés en souveraineté",()=>{
 mustFail(d=>d.scenarios[1].federal_funding_or_inherited_debt_assumed=true,"FICTIONAL_CONSTITUTIONAL_BUDGET");
});
test("un budget annuel fictif dans le Québec canadien est refusé",()=>{
 mustFail(d=>d.scenarios[0].school_budget_continuity_mcad=30000,"FICTIONAL_CONSTITUTIONAL_BUDGET");
});
test("dédoublement de taxe scolaire et taxe municipale interdit",()=>{
 mustFail(d=>d.cross_checks.no_double_count_school_municipal=false,"ACCOUNTING_DOUBLE_COUNT_RISK");
});
test("70 % de l'UMQ n'est pas une statistique fédérale certifiée",()=>{
 mustFail(d=>d.cross_checks.claims_70pct_umq_as_verified_federal_statistic=true,"ACCOUNTING_DOUBLE_COUNT_RISK");
});
test("V10, V14 et V15 sont requises, aucune preuve indépendamment franchie",()=>{
 assert.deepEqual(data.required_proofs,["V10","V14","V15"]);
 mustFail(d=>d.required_proofs.pop(),"G015_EVIDENCE_UNPASSED");
});
test("responsable et devis fictifs ne clôturent pas un dossier",()=>{
 mustFail(d=>d.unresolved_issues[0].independent_review=true,"ISSUES_PREMATURELY_CLOSED");
});
test("un pourcentage Nova à 48 est refusé",()=>{
 mustFail(d=>d.programme_score_after=48,"FALSE_PROGRAMME_STATUS");
});
test("une économie RH fantaisiste est refusée",()=>{
 mustFail(d=>d.decision.staffing_savings_verified=true,"PREMATURE_APPROVAL");
});
test("un Québec indépendant sans bilan certifié n'est pas prêt",()=>{
 mustFail(d=>d.decision.sovereign_budget_certified=true,"PREMATURE_APPROVAL");
});
test("la base source G0.14 ne peut être remplacée discrètement",()=>{
 const x=structuredClone(g014);
 x.revenue_categories.find(q=>q.id==="FONCIER_SCOLAIRE").amount_mcad=1;
 const r=verifyG016gTerritorialContinuity(data,x,g015,g016e,g016f);
 assert.equal(r.ok,false);
 assert.ok(r.errors.includes("SCHOOL_TAX_NOT_SCHOOL_COST"));
});
test("la source G0.15 non auditée ne peut être marquée complète",()=>{
 const x=structuredClone(g015);
 x.proofs.find(q=>q.id==="V10").status="DOCUMENTEE";
 const r=verifyG016gTerritorialContinuity(data,g014,x,g016e,g016f);
 assert.equal(r.ok,false);
 assert.ok(r.errors.includes("G015_EVIDENCE_UNPASSED"));
});
test("un solde Nova inventé dans G0.16e bloque la chaîne de preuves",()=>{
 const x=structuredClone(g016e);
 x.scenarios[0].annual[0].net_balance_mcad=7000;
 const r=verifyG016gTerritorialContinuity(data,g014,g015,x,g016f);
 assert.equal(r.ok,false);
 assert.ok(r.errors.includes("PREDECESSOR_GATES_UNPASSED"));
});
test("une étape G0.16f réputée complète n'augmente pas le score",()=>{
 const x=structuredClone(g016f);x.programme_percent_after=48;
 const r=verifyG016gTerritorialContinuity(data,g014,g015,g016e,x);
 assert.equal(r.ok,false);
 assert.ok(r.errors.includes("PREDECESSOR_GATES_UNPASSED"));
});

test("la ressource officielle agrégée 2024 MAMH est identifiable sans prétendre l'avoir extraite",()=>{
 const m=data.source_facts.municipalities;
 assert.equal(m.aggregate_2024_resource_page,
  "https://www.donneesquebec.ca/recherche/dataset/profil-financier-des-municipalites-locales/resource/5dec077d-4ef9-4e22-99e9-0c4f3a6dd52d");
 assert.equal(m.aggregate_2024_csv_status,"SOURCE_CATALOGUE_IDENTIFIEE_NON_IMPORTEE");
 assert.equal(m.aggregate_property_tax_revenue_mcad,null);
});
test("l'import du CSV municipal ne peut pas être marqué réalisé sans total validé",()=>{
 mustFail(d=>d.source_facts.municipalities.aggregate_2024_csv_status="IMPORTE_ET_AUDITE","MUNICIPAL_TAX_INCOMPLETE");
});
