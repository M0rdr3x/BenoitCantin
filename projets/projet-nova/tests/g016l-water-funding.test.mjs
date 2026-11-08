import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016lFundingSources,calculateSyntheticFundingExercise}
 from "../assets/g016l-water-funding-core.mjs";

const read=async file=>JSON.parse(await readFile(new URL("../data/"+file,import.meta.url),"utf8"));
const [d,k]=await Promise.all([
 read("financement-eau-g0-16l-pga-primeau-tecq-2026.json"),
 read("continuite-actifs-eau-g0-16k-2025.json")
]);
const inspect=x=>inspectG016lFundingSources(x,k);
const clone=x=>structuredClone(x);
const reject=(alter,code)=>{
 const row=clone(d);alter(row);
 const r=inspect(row);
 assert.equal(r.ok,false);
 assert.ok(r.errors.includes(code),r.errors.join(","));
};
const fake=(cost,commitments)=>calculateSyntheticFundingExercise({
 mode:"SYNTHETIC_EXERCISE",synthetic_label:true,total_cost_cad:cost,commitments
});
const g=(programme,stage,amount_cad,synthetic_reference)=>({
 programme,stage,amount_cad,synthetic_reference
});

test("les règles gouvernementales et l'état 47 passent le contrôle",()=>{
 const r=inspect(d);assert.equal(r.ok,true,r.errors.join(","));
 assert.equal(r.programme_score,47);assert.equal(r.verified_municipal_awards,0);
});
test("trois sources officielles PGA PRIMEAU TECQ enregistrées",()=>{
 assert.deepEqual(d.sources.map(x=>x.id),["PGA_EAU","PRIMEAU","TECQ"]);
});
test("PGA : engagement décembre 2026, pas plan complet",()=>{
 const x=d.official_milestones.find(x=>x.id==="PGA_COMMIT");
 assert.equal(x.date,"2026-12-31");
 assert.equal(x.constitutes_final_plan,false);
 assert.equal(x.automatically_mandatory_for_every_city,false);
});
test("PGA : suivi annuel à partir de 2028",()=>{
 assert.equal(d.official_milestones.find(x=>x.id==="PGA_FOLLOW_UP").date,"2028-01-01");
});
test("PRIMEAU 2026 est clôturé le 30 octobre",()=>{
 const x=d.official_milestones.find(x=>x.id==="PRIMEAU_CALL_2026");
 assert.equal(x.as_of_status,"PAST_WINDOW");
 assert.equal(x.open_date,"2026-08-31");
 assert.equal(x.date,"2026-10-30");
});
test("PRIMEAU volet 2 fermé aux nouvelles demandes",()=>{
 assert.match(d.official_milestones.find(x=>x.id==="PRIMEAU_CALL_2026").fact,/volet 2 fermé/);
});
test("PRIMEAU : présélection et promesses sont des limites distinctes",()=>{
 assert.equal(d.official_milestones.find(x=>x.id==="PRIMEAU_PRESELECT_LIMIT").date,"2028-03-31");
 assert.equal(d.official_milestones.find(x=>x.id==="PRIMEAU_GRANT_LIMIT").date,"2031-03-31");
});
test("TECQ : fenêtre annuelle 1er octobre à 15 février",()=>{
 const x=d.official_milestones.find(x=>x.id==="TECQ_UPDATE_WINDOW");
 assert.equal(x.open_date,"2026-10-01");
 assert.equal(x.date,"2027-02-15");
 assert.equal(x.as_of_status,"OPEN_WINDOW");
});
test("TECQ : travaux terminés 2028, comptes finaux au juin 2029",()=>{
 assert.equal(d.official_milestones.find(x=>x.id==="TECQ_WORK_ELIGIBILITY_END").date,"2028-12-31");
 assert.equal(d.official_milestones.find(x=>x.id==="TECQ_FINAL_ACCOUNTING").date,"2029-06-30");
});
test("2,4 G$ PRIMEAU n'est pas une subvention obtenue pour Nova",()=>{
 assert.equal(d.programme_funding[0].announced_envelope_cad,2400000000);
 assert.equal(d.programme_funding[0].grant_to_nova_cad,null);
});
test("TECQ représente une enveloppe de plus de 3,3 G$, non une attribution",()=>{
 assert.equal(d.programme_funding[1].announced_envelope_floor_cad,3300000000);
 assert.equal(d.programme_funding[1].amount_relation,"MORE_THAN");
 assert.equal(d.programme_funding[1].municipality_specific_awards_verified_cad,null);
});
test("aucun projet municipal fictif n'est présenté comme vérifié",()=>{
 assert.equal(d.project_register.length,0);
 assert.equal(d.regional_readiness.municipality_level_project_costs_imported,0);
});
test("les scénarios Canada et souverain comportent chacun dix exercices inconnus",()=>{
 assert.deepEqual(d.constitutional_models.map(x=>x.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
 assert.ok(d.constitutional_models.every(s=>s.budget_years.length===10));
 assert.ok(d.constitutional_models.every(s=>s.budget_years.every(y=>y.net_gap_cad===null)));
});
test("stock CERIU 2025 et dépenses 2024 ne deviennent pas un déficit Nova",()=>{
 assert.equal(d.underlying_evidence.stock_2025_replacement_gcad,197.6);
 assert.equal(d.underlying_evidence.historical_water_and_sewer_cost_2024_cad,2519426792);
 assert.equal(d.underlying_evidence.underfunding_for_nova_cad,null);
});
test("une date de PGA avancée sans preuve est rejetée",()=>{
 reject(x=>x.official_milestones[0].date="2026-10-01","IMPORTANT_DATES_FALSIFIED");
});
test("l'étape PGA d'engagement ne peut être assimilée à l'adoption définitive",()=>{
 reject(x=>x.official_milestones[0].constitutes_final_plan=true,"IMPORTANT_DATES_FALSIFIED");
});
test("un appel PRIMEAU rouvert artificiellement est rejeté",()=>{
 reject(x=>x.official_milestones[3].as_of_status="OPEN_WINDOW","IMPORTANT_DATES_FALSIFIED");
});
test("le volet TECQ ne peut être déclaré fermé sans preuve",()=>{
 reject(x=>x.official_milestones[6].as_of_status="PAST_WINDOW","IMPORTANT_DATES_FALSIFIED");
});
test("une enveloppe de 2,4 G$ ne devient pas une aide reçue",()=>{
 reject(x=>x.programme_funding[0].grant_to_nova_cad=2400000000,"ENVELOPE_MISREPRESENTED_AS_AWARD");
});
test("le montant de l'enveloppe TECQ ne doit pas devenir exactement 3,3 G$",()=>{
 reject(x=>x.programme_funding[1].amount_relation="EQUAL_ANNOUNCED_ENVELOPE","ENVELOPE_MISREPRESENTED_AS_AWARD");
});
test("un nombre de projets fictifs est bloqué",()=>{
 reject(x=>x.project_register.push({municipality:"faux"}),"PROJECT_DATA_CANNOT_BE_FABRICATED");
});
test("une promesse d'aide ne signifie pas un versement effectif",()=>{
 reject(x=>x.decision_rules.promise_is_not_cash_disbursement=false,"KEY_FUNDING_DISTINCTIONS_LOST");
});
test("un versement présumé au Québec souverain est bloqué",()=>{
 reject(x=>x.decision_rules.federal_tecq_not_automatic_sovereign_funding=false,"KEY_FUNDING_DISTINCTIONS_LOST");
});
test("le coût du patrimoine de 197,6 G$ n'est pas un devis local",()=>{
 reject(x=>x.decision_rules.no_project_cost_from_197_6b_stock=false,"KEY_FUNDING_DISTINCTIONS_LOST");
});
test("le nombre de subventions locales ne peut être inventé",()=>{
 reject(x=>x.regional_readiness.municipality_level_approved_awards_verified=1,"UNSUBSTANTIATED_MUNICIPAL_READINESS");
});
test("le budget 2028 souverain ne peut être chiffré sans preuves",()=>{
 reject(x=>x.constitutional_models[1].budget_years[2].verified_tecq_awards_cad=200000000,"TEN_YEAR_BUDGET_UNSUBSTANTIATED");
});
test("un exercice supprimé invalide la projection",()=>{
 reject(x=>x.constitutional_models[0].budget_years.pop(),"TEN_YEAR_BUDGET_UNSUBSTANTIATED");
});
test("l'audit juridique ou financier ne peut être préapprouvé",()=>{
 reject(x=>x.decisions.external_audit_signed=true,"PREMATURE_CONCLUSION");
});
test("la complétude ne peut augmenter à 48 par création d'une matrice",()=>{
 reject(x=>x.programme_score_after=48,"PROGRAMME_STATUS_UNVERIFIED");
});
test("les six portes documentaires ne peuvent être marquées franchies",()=>{
 reject(x=>x.unmet_conditions[0].status="DONE","MISSING_DOCUMENTARY_PROOFS");
});
test("le contrôle d'amont refuse un stock CERIU modifié",()=>{
 const broken=clone(k);broken.assets_2025.total_replacement_gcad=200;
 const r=inspectG016lFundingSources(d,broken);
 assert.equal(r.ok,false);assert.ok(r.errors.includes("SOURCE_ASSETS_AND_COSTS_MIXED"));
});
test("exercice synthétique : zéro subvention, reste à financer l'intégralité",()=>{
 const x=fake(10000,[]);
 assert.equal(x.synthetic_promises_cad,0);
 assert.equal(x.gap_after_promises_cad,10000);
 assert.equal(x.project_legally_funded,false);
});
test("exercice synthétique : promesse 3000, versement 2000",()=>{
 const x=fake(10000,[g("TECQ","PROMISE_DOCUMENTED",3000,"A1"),
   g("PRIMEAU","PAYMENT_DOCUMENTED",2000,"A2")]);
 assert.equal(x.synthetic_promises_cad,5000);
 assert.equal(x.synthetic_paid_cad,2000);
 assert.equal(x.promised_but_not_paid_cad,3000);
 assert.equal(x.gap_after_promises_cad,5000);
 assert.equal(x.gap_after_cash_payments_cad,8000);
});
test("l'exercice sans drapeau synthétique est refusé",()=>{
 assert.throws(()=>calculateSyntheticFundingExercise({mode:"REAL",synthetic_label:true,total_cost_cad:100,commitments:[]}),/SYNTHETIC_ONLY/);
});
test("l'argent fictif annoncé mais non promis ne peut être compté",()=>{
 assert.throws(()=>fake(100,[g("TECQ","ANNOUNCED_PROGRAMME",100,"A1")]),/INVALID_SYNTHETIC_COMMITMENT/);
});
test("un dépassement du coût total ne peut devenir financement disponible",()=>{
 assert.throws(()=>fake(100,[g("TECQ","PROMISE_DOCUMENTED",101,"A1")]),/OVERFUNDED/);
});
test("deux aides sous la même référence sont rejetées",()=>{
 assert.throws(()=>fake(100,[g("TECQ","PROMISE_DOCUMENTED",20,"A1"),
  g("PRIMEAU","PAYMENT_DOCUMENTED",30,"A1")]),/INVALID_SYNTHETIC_COMMITMENT/);
});
test("la simulation bloque les montants négatifs et les décimales",()=>{
 assert.throws(()=>fake(100,[g("TECQ","PROMISE_DOCUMENTED",-1,"A")]),/INVALID_SYNTHETIC_COMMITMENT/);
 assert.throws(()=>fake(100,[g("TECQ","PROMISE_DOCUMENTED",1.2,"A")]),/INVALID_SYNTHETIC_COMMITMENT/);
});
