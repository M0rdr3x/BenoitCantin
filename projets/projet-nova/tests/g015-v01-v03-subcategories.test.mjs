import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG015V01V03Subcategories,OFFICIAL_REVENUE_NOTE_URL}
 from "../assets/g015-v01-v03-subcategories-core.mjs";
const load=async file=>JSON.parse(await readFile(new URL("../data/"+file,import.meta.url),"utf8"));
const [d,g014,g015,discovery,actuals]=await Promise.all([
 load("ventilation-revenus-g0-15-v01-v02-v03-2025-2026.json"),
 load("registre-assiettes-fiscales-g0-14-2026-2027.json"),
 load("matrice-preuves-g0-15-fiscalite.json"),
 load("reperage-sources-officielles-g0-15-2026-11-07.json"),
 load("comptes-publics-reels-g0-15-v02-v03-2025-2026.json")
]);
const check=(x,a=g014,b=g015,c=discovery,z=actuals)=>
 inspectG015V01V03Subcategories(x,a,b,c,z);
const mutate=(fn,error)=>{
 const x=structuredClone(d);fn(x);
 const v=check(x);
 assert.equal(v.ok,false,error);
 assert.ok(v.errors.includes(error),v.errors.join(","));
};
test("V01–V03 : les 20 sous-catégories réelles se rapprochent des comptes officiels",()=>{
 const result=check(d);
 assert.equal(result.ok,true,result.errors.join(","));
 assert.deepEqual(result.groups_observed_2025_2026_mcad,[29639,6708,14922]);
 assert.equal(result.number_subcategories,20);
 assert.equal(result.programme_score,47);
 assert.equal(result.additional_nova_revenue_mcad,null);
});
test("V01 : les cinq taxes réalisées totalisent 29 639 M$ contre 28 377 M$",()=>{
 const v=d.groups[0];assert.equal(v.id,"V01");
 assert.equal(v.categories.reduce((a,r)=>a+r.year_2025_2026_mcad,0),29639);
 assert.equal(v.categories.reduce((a,r)=>a+r.year_2024_2025_mcad,0),28377);
});
test("V02 : quatre types de droits totalisent 6 708 M$ contre 6 191 M$",()=>{
 const v=d.groups[1];assert.equal(v.id,"V02");
 assert.equal(v.categories.reduce((a,r)=>a+r.year_2025_2026_mcad,0),6708);
 assert.equal(v.categories.find(r=>r.id==="GHG").year_2025_2026_mcad,1123);
});
test("V03 : 11 rubriques totalisent 14 922 M$ contre 16 252 M$",()=>{
 const v=d.groups[2];assert.equal(v.id,"V03");
 assert.equal(v.categories.reduce((a,r)=>a+r.year_2025_2026_mcad,0),14922);
 assert.equal(v.categories.reduce((a,r)=>a+r.year_2024_2025_mcad,0),16252);
 assert.equal(v.categories.slice(0,6).reduce((a,r)=>a+r.year_2025_2026_mcad,0),9132);
});
test("le crédit d'impôt solidarité 1 996 M$ est déjà soustrait de la vente",()=>{
 assert.equal(d.groups[0].categories[0].year_2025_2026_mcad,25930);
 assert.equal(d.solidarity_credit.year_2025_2026_mcad,1996);
 assert.equal(d.solidarity_credit.already_deducted_in_sales,true);
 assert.equal(d.solidarity_credit.add_again_as_new_expense,false);
});
test("modifier un chiffre fiscal V01 entraîne un échec sans extrapolation",()=>{
 mutate(x=>x.groups[0].categories[0].year_2025_2026_mcad=26000,
   "SUBCATEGORY_RECONCILIATION_V01");
 mutate(x=>x.groups[0].year_2025_2026_total_mcad=30000,
   "SUBCATEGORY_RECONCILIATION_V01");
});
test("les droits d'émission et droits de ressources ne sont pas automatiquement des taxes",()=>{
 mutate(x=>x.groups[1].categories[2].treatment="FISCAL_SALES_NET_OF_CREDIT",
  "SUBCATEGORY_RECONCILIATION_V02");
 mutate(x=>x.groups[1].categories[1].year_2024_2025_mcad=2000,
  "SUBCATEGORY_RECONCILIATION_V02");
});
test("les primes médicaments et les services rendus ne sont pas assimilés à l'impôt",()=>{
 mutate(x=>x.groups[2].categories[1].treatment="FISCAL_EXCISE",
   "SUBCATEGORY_RECONCILIATION_V03");
 mutate(x=>x.groups[2].categories[1].year_2025_2026_mcad=0,
   "SUBCATEGORY_RECONCILIATION_V03");
 mutate(x=>x.groups[2].services_rendered_subtotal_2025_2026_mcad=9000,
   "V03_SERVICE_SUBTOTAL");
});
test("le crédit solidarité ne doit pas être ajouté une seconde fois",()=>{
 mutate(x=>x.solidarity_credit.add_again_as_new_expense=true,
   "SOLIDARITY_CREDIT_DOUBLE_COUNT");
 mutate(x=>x.solidarity_credit.year_2025_2026_mcad=0,
   "SOLIDARITY_CREDIT_DOUBLE_COUNT");
});
test("le résultat 2025-2026 et les prévisions 2026-2027 restent séparés",()=>{
 mutate(x=>x.crosswalk.never_add_forecast_to_actuals=false,"ACTUAL_FORECAST_CROSSCHECK");
 mutate(x=>x.crosswalk.g014_forecast_v01_mcad=29639,"ACTUAL_FORECAST_CROSSCHECK");
});
test("la source publique auditée ne certifie pas les mesures fiscales NOVA",()=>{
 mutate(x=>x.source.nova_reform_independently_audited=true,"PROVENANCE_FALSE");
 mutate(x=>x.evidence.policy_rates_authorized=true,"NOVA_UNPROVEN_APPROVAL");
 mutate(x=>x.evidence.financed_new_nova_revenue_mcad=29639,"NOVA_UNPROVEN_APPROVAL");
 mutate(x=>x.programme_score_after=48,"FALSE_READINESS");
});
test("V01, V02 et V03 restent A_DOCUMENTER et non certifiées",()=>{
 for(const id of ["V01","V02","V03"]){
  const proof=g015.proofs.find(p=>p.id===id);
  assert.equal(proof.status,"A_DOCUMENTER");
  assert.equal(proof.primary_source,null);
  assert.ok(discovery.entries.find(p=>p.id===id).candidats.some(s=>s.url===OFFICIAL_REVENUE_NOTE_URL));
 }
 const g=structuredClone(g015);
 g.proofs.find(p=>p.id==="V01").reviewed_independently=true;
 assert.ok(check(d,g014,g).errors.includes("G015_NOT_VALIDATED"));
});
test("chiffres 2025-2026 indépendamment contrôlés contre le registre V02/V03",()=>{
 const a=structuredClone(actuals);
 a.annual.find(r=>r.year==="2025-2026").rights_permits_royalties=9999;
 assert.ok(check(d,g014,g015,discovery,a).errors.includes("ACTUAL_FORECAST_CROSSCHECK"));
});
test("une source ou un ordre de sous-catégorie falsifié est rejeté",()=>{
 mutate(x=>x.source.pdf_page_index_zero_based=11,"PROVENANCE_FALSE");
 mutate(x=>x.groups[0].categories.reverse(),"SUBCATEGORY_RECONCILIATION_V01");
});
test("un document sans champs obligatoires est rejeté proprement",()=>{
 for(const k of ["source","groups","evidence","solidarity_credit","crosswalk","decisions"]){
  const x=structuredClone(d);delete x[k];
  assert.ok(check(x).errors.includes("SCHEMA"),k);
 }
});
test("la page publique montre les trois ventilations et le score inchangé",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 const start=html.indexOf('id="ventilation-revenus-g015-v01-v03"');
 const end=html.indexOf("</section>",start);
 assert.ok(start>=0&&end>start);
 const section=html.slice(start,end);
 for(const phrase of ["29 639 M$","6 708 M$","14 922 M$","1 996 M$",
     "2025-2026","2026-2027","47 % inchangé"]){
  assert.ok(section.includes(phrase),phrase);
 }
 assert.ok(section.includes(OFFICIAL_REVENUE_NOTE_URL));
});
