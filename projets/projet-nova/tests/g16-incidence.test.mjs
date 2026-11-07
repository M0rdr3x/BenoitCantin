import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG16Plan,compareSyntheticCases} from "../assets/g16-incidence-core.mjs";

const g16=JSON.parse(await readFile(new URL("../data/plan-microsimulation-g0-16.json",import.meta.url),"utf8"));
const g15=JSON.parse(await readFile(new URL("../data/matrice-preuves-g0-15-fiscalite.json",import.meta.url),"utf8"));
const clone=()=>structuredClone(g16);
const exercise=()=>({mode:"SYNTHETIC_EXERCISE",
 current:{gross_income_cad:100,taxes_cad:20,contributions_cad:5,benefits_cad:10,essential_expenses_cad:50},
 proposed:{gross_income_cad:100,taxes_cad:15,contributions_cad:5,benefits_cad:10,essential_expenses_cad:55}});

test("G0.16 conserve une grille non calibrée à 47/100",()=>{
 const x=inspectG16Plan(g16,g15);
 assert.equal(x.ok,true,x.errors.join(","));
 assert.equal(x.programme_percent,47);
 assert.equal(x.calibrated_scenarios,0);
 assert.equal(x.g016_passed,false);
});
test("deux scénarios séparés et dix déciles chacun",()=>{
 assert.deepEqual(g16.scenarios.map(x=>x.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
 assert.ok(g16.scenarios.every(s=>s.distribution.length===10));
});
test("aucune donnée de ménage n'est présentée comme constatée",()=>{
 const cells=g16.scenarios.flatMap(s=>s.distribution);
 assert.equal(cells.length,20);
 assert.ok(cells.every(c=>Object.values(c).filter(x=>x!==c.decile).every(x=>x===null)));
});
test("les 15 preuves G0.15 sont encore à documenter",()=>{
 assert.equal(g15.proofs.length,15);
 assert.ok(g15.proofs.every(p=>p.status==="A_DOCUMENTER"&&p.amount_mcad===null));
});
test("montant fictif dans un décile rejeté",()=>{
 const d=clone();d.scenarios[0].distribution[0].net_change_cad=3000;
 assert.ok(inspectG16Plan(d,g15).errors.some(x=>x.startsWith("UNVERIFIED_DECILE")));
});
test("décile dupliqué rejeté",()=>{
 const d=clone();d.scenarios[0].distribution[0].decile=2;
 assert.equal(inspectG16Plan(d,g15).ok,false);
});
test("scénarios fusionnés rejetés",()=>{
 const d=clone();d.scenarios[1].id="QUEBEC_CANADA";
 assert.ok(inspectG16Plan(d,g15).errors.includes("SCENARIOS_NOT_SEPARATE"));
});
test("transfert fédéral inventé en souveraineté rejeté",()=>{
 const d=clone();d.scenarios[1].federal_transfers_after_sovereignty_mcad=33046;
 assert.ok(inspectG16Plan(d,g15).errors.some(x=>x.includes("UNPROVEN_SCENARIO")));
});
test("approbation fictive ou taux annoncé rejeté",()=>{
 const d=clone();d.decision.ready_to_reform=true;d.unknowns.income_tax_rate_percent=18;
 const errors=inspectG16Plan(d,g15).errors;
 assert.ok(errors.includes("FALSE_AUTHORIZATION")&&errors.includes("INVENTED_RESULTS"));
});
test("preuve G0.15 non auditée ne devient pas validée",()=>{
 const p=structuredClone(g15);p.proofs[0].reviewed_independently=true;
 assert.ok(inspectG16Plan(g16,p).errors.includes("PREDECESSOR_NOT_VALIDATED"));
});
test("un calcul sans étiquette synthétique est bloqué",()=>{
 const x=exercise();delete x.mode;
 assert.deepEqual(compareSyntheticCases(x),{ok:false,code:"DEMO_ONLY"});
});
test("montants manquants, NaN et valeurs négatives sont rejetés",()=>{
 const a=exercise();a.proposed.taxes_cad=null;
 const b=exercise();b.current.taxes_cad=NaN;
 const c=exercise();c.current.essential_expenses_cad=-1;
 for(const x of [a,b,c])assert.equal(compareSyntheticCases(x).ok,false);
});
test("arithmétique synthétique nette : aucun gain n'est déduit de la seule baisse des impôts",()=>{
 const x=compareSyntheticCases(exercise());
 assert.equal(x.ok,true);
 assert.equal(x.before.after_essentials_cad,35);
 assert.equal(x.after.after_essentials_cad,35);
 assert.equal(x.change_after_essentials_cad,0);
 assert.equal(x.count_as_validated_nova_result,false);
});
test("le calcul pédagogique ne peut pas changer les fichiers G0.16",()=>{
 const before=JSON.stringify(g16);
 compareSyntheticCases(exercise());
 assert.equal(JSON.stringify(g16),before);
});
