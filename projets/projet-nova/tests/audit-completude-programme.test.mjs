import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {
  inspectProgramCompleteness,listPriorities,REQUIRED_DOMAINS,REQUIRED_SECTORS
} from "../assets/audit-completude-programme-core.mjs";

const doc=JSON.parse(await readFile(
  new URL("../data/audit-completude-programme-nova-2026-11-05.json",import.meta.url),"utf8"));
const copy=()=>structuredClone(doc);

test("la grille donne bien 47/100 avec 10 dimensions pondérées",()=>{
 const result=inspectProgramCompleteness(doc);
 assert.equal(result.ok,true,result.errors.join(","));
 assert.equal(result.percent,47);
 assert.equal(result.maximum,100);
 assert.equal(result.dimensions_in_scope,10);
 assert.equal(REQUIRED_DOMAINS.length,10);
});
test("les 14 chantiers sont identifiés sans fausse fiche complète",()=>{
 const result=inspectProgramCompleteness(doc);
 assert.equal(result.sectors_in_scope,14);
 assert.equal(REQUIRED_SECTORS.length,14);
 assert.ok(doc.sector_register.every(x=>x.completed_measure_sheets_confirmed===0&&
   x.full_costed_budget_confirmed===null));
});
test("la grille ne certifie pas la préparation à gouverner",()=>{
 const result=inspectProgramCompleteness(doc);
 assert.equal(result.ready_to_govern,false);
 assert.equal(result.fiscal_model_independently_certified,false);
 assert.equal(doc.decisions.not_officially_adopted,true);
 assert.equal(doc.decisions.pilot_authorized,false);
});
test("une nouvelle pondération sans équilibre à 100 est rejetée",()=>{
 const d=copy();d.dimensions[0].weight=9;
 assert.equal(inspectProgramCompleteness(d).ok,false);
});
test("le score ne peut être gonflé artificiellement sans correction des points",()=>{
 const d=copy();d.scoring.percentage=90;
 assert.ok(inspectProgramCompleteness(d).errors.includes("SCORE_ARITHMETIC_INCORRECT"));
});
test("un domaine en double empêche de conclure",()=>{
 const d=copy();d.dimensions[0].id="FINANCES";
 assert.equal(inspectProgramCompleteness(d).ok,false);
});
test("le budget n'est pas marqué comme certifié sans preuve",()=>{
 const d=copy();d.decisions.sector_budgets_certified=true;
 assert.ok(inspectProgramCompleteness(d).errors.includes("FALSE_READINESS_OR_ADOPTION_CLAIM"));
});
test("une fiche sectorielle imaginaire est rejetée",()=>{
 const d=copy();d.sector_register[0].completed_measure_sheets_confirmed=1;
 assert.equal(inspectProgramCompleteness(d).ok,false);
});
test("une preuve juridique non documentée ne devient pas un oui",()=>{
 const d=copy();d.sector_register[1].legal_review_confirmed=true;
 assert.ok(inspectProgramCompleteness(d).errors.some(x=>x.includes("SECTOR_HAS_UNSUPPORTED_CLAIMS")));
});
test("les travaux P0 sont prioritaires sur les P1",()=>{
 const x=listPriorities(doc);
 const firstP1=x.findIndex(a=>a.priority==="P1");
 assert.ok(firstP1>0);
 assert.ok(x.slice(0,firstP1).every(a=>a.priority==="P0"));
});
test("la référence de santé G0.11 n'est pas une preuve de budget équilibré",()=>{
 const finance=doc.dimensions.find(d=>d.id==="FINANCES");
 const health=doc.dimensions.find(d=>d.id==="SERVICES");
 assert.ok(finance.points<finance.weight);
 assert.ok(health.points<health.weight);
 assert.equal(doc.decisions.ready_to_govern,false);
});
test("l'estimation de rédaction n'est pas présentée comme un résultat audité",()=>{
 assert.equal(doc.scoring.documentation_maturity_estimate_percent,75);
 assert.equal(doc.scoring.documentation_maturity_is_independently_measured,false);
});
