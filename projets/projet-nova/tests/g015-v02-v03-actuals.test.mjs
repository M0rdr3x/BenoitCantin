import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG015V02V03Actuals,SOURCE_G015_V02_V03}
 from "../assets/g015-v02-v03-public-actuals-core.mjs";

const load=async p=>JSON.parse(await readFile(new URL("../data/"+p,import.meta.url),"utf8"));
const [d,g014,g015,source]=await Promise.all([
 load("comptes-publics-reels-g0-15-v02-v03-2025-2026.json"),
 load("registre-assiettes-fiscales-g0-14-2026-2027.json"),
 load("matrice-preuves-g0-15-fiscalite.json"),
 load("reperage-sources-officielles-g0-15-2026-11-07.json")
]);
const inspect=(x,a=g014,b=g015,c=source)=>inspectG015V02V03Actuals(x,a,b,c);
const tamper=(fn,expected)=>{
 const x=structuredClone(d);fn(x);const r=inspect(x);
 assert.equal(r.ok,false);
 assert.ok(r.errors.includes(expected),r.errors.join(","));
};

test("comptes publics 2025-2026 : 6708 M$ de droits et 14922 M$ de revenus divers",()=>{
 const r=inspect(d);
 assert.equal(r.ok,true,r.errors.join(","));
 assert.equal(r.rights_2025_2026_mcad,6708);
 assert.equal(r.miscellaneous_2025_2026_mcad,14922);
 assert.equal(r.programme_score,47);
 assert.equal(r.confirmed_nova_new_revenues_mcad,null);
});

test("revenus réels de deux exercices se concilient sans double compte",()=>{
 for(const row of d.annual){
  assert.equal(row.income_and_property_taxes+row.consumption_taxes+
   row.rights_permits_royalties+row.miscellaneous_revenues+
   row.government_enterprises,row.own_revenues);
  assert.equal(row.own_revenues+row.federal_transfers,row.total_revenues);
  assert.equal(row.total_revenues-row.total_expenditures,row.accounting_balance);
 }
 assert.equal(d.annual[1].total_revenues,160428);
 assert.equal(d.annual[0].total_revenues,156088);
});

test("comparaison 2024-2025 reclassée, variations cohérentes",()=>{
 assert.equal(d.annual[0].classification,"COMPTES_PUBLICS_REELS_RECLASSES_COMPARATIFS");
 assert.equal(d.changes_2025_2026_minus_2024_2025.rights_permits_royalties,517);
 assert.equal(d.changes_2025_2026_minus_2024_2025.miscellaneous_revenues,-1330);
});

test("un montant de droits inventé échoue malgré la présence de source",()=>{
 tamper(x=>x.annual[1].rights_permits_royalties=6800,"ACTUALS_RECONCILIATION_FAILED");
});
test("un revenu divers inventé échoue",()=>{
 tamper(x=>x.annual[0].miscellaneous_revenues=0,"ACTUALS_RECONCILIATION_FAILED");
});
test("un faux déficit équilibré ne peut devenir un résultat officiel",()=>{
 tamper(x=>x.annual[1].accounting_balance=0,"ACTUALS_RECONCILIATION_FAILED");
});
test("l'exercice 2026-2027 prévisionnel ne peut devenir un résultat réalisé",()=>{
 tamper(x=>x.cross_reference_g014.add_2025_2026_actuals_to_2026_2027_forecast=true,
   "FORECAST_ACTUALS_CONFUSED");
 tamper(x=>x.cross_reference_g014.forecast_total_revenues_mcad=160428,
   "FORECAST_ACTUALS_CONFUSED");
});
test("deux comptes de prévision ne prouvent ni recettes nouvelles ni réforme NOVA",()=>{
 tamper(x=>x.evidence.new_nova_revenue_mcad=6708,"PREMATURE_NOVA_CERTIFICATION");
 tamper(x=>x.decision.budget_nova_certified=true,"PREMATURE_NOVA_CERTIFICATION");
 tamper(x=>x.programme_score_after=48,"FALSE_STATUS_OR_SCORE");
});
test("un audit du gouvernement ne devient pas un audit fiscal indépendant de NOVA",()=>{
 assert.equal(d.source.government_accounts_vgq_unqualified_opinion,true);
 assert.equal(d.source.reviewed_independently_for_nova,false);
 tamper(x=>x.source.reviewed_independently_for_nova=true,"INVALID_PUBLIC_ACCOUNTS_SOURCE");
 tamper(x=>x.evidence.g015_v02_independently_validated=true,"PREMATURE_NOVA_CERTIFICATION");
 tamper(x=>x.evidence.g015_v03_independently_validated=true,"PREMATURE_NOVA_CERTIFICATION");
});
test("absence de ventilation fiscale et des éliminations internes bloquante",()=>{
 tamper(x=>x.evidence.v02_legal_source_allocation_complete=true,
   "PREMATURE_NOVA_CERTIFICATION");
 tamper(x=>x.evidence.v03_internal_transfer_elimination_complete=true,
   "PREMATURE_NOVA_CERTIFICATION");
});
test("source PDF, année et numéros de page non substituables",()=>{
 assert.equal(d.source.url,SOURCE_G015_V02_V03);
 assert.equal(d.source.pdf_page_index_zero_based_results,11);
 tamper(x=>x.source.url="http://example.org/comptes","INVALID_PUBLIC_ACCOUNTS_SOURCE");
 tamper(x=>x.source.pdf_page_index_zero_based_results=10,"INVALID_PUBLIC_ACCOUNTS_SOURCE");
});
test("V02 et V03 conservent des preuves non homologuées malgré le PDF",()=>{
 for(const id of ["V02","V03"]){
  const p=g015.proofs.find(x=>x.id===id);
  const candidate=source.entries.find(x=>x.id===id);
  assert.equal(p.primary_source,null);
  assert.equal(p.status,"A_DOCUMENTER");
  assert.ok(candidate.candidats.some(c=>c.url===SOURCE_G015_V02_V03));
 }
 const forged=structuredClone(g015);
 forged.proofs.find(x=>x.id==="V02").reviewed_independently=true;
 assert.ok(inspect(d,g014,forged).errors.includes("G015_V02_V03_STILL_UNVALIDATED"));
});
test("une série incomplète est rejetée proprement",()=>{
 const x=structuredClone(d);x.annual=[null];
 const r=inspect(x);assert.equal(r.ok,false);
 assert.ok(r.errors.includes("ACTUALS_RECONCILIATION_FAILED"));
});
test("la page publique distingue réalisés et prévisions",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 const start=html.indexOf('id="comptes-publics-g015-v02-v03"');
 const end=html.indexOf("</section>",start);
 assert.ok(start>=0&&end>start);
 const section=html.slice(start,end);
 assert.match(section,/6 708 M\$/);
 assert.match(section,/14 922 M\$/);
 assert.match(section,/2025-2026/);
 assert.match(section,/2026-2027/);
 assert.match(section,/47 % inchangé/);
 assert.ok(section.includes(SOURCE_G015_V02_V03));
});
