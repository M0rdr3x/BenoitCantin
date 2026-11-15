#!/usr/bin/env node
"use strict";
// Tests unitaires de la fonction EFFECTIVEMENT exécutée dans l'Edge Supabase.
// Aucun réseau, aucun jeton ni aucun bulletin; toutes les données sont fictives.
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const file=path.join(__dirname,"../supabase/functions/nova-civic-poll/index.ts");
const edge=fs.readFileSync(file,"utf8");
const match=edge.match(/function verifyPublishedCounts\([\s\S]*?\n}\n+(?=\/\/ Une catégorie)/);
assert.ok(match,"La fonction de validation réelle est introuvable");
const js=match[0]
  .replace(/function verifyPublishedCounts\([\s\S]*?\)\s*:\s*Map<string,number\[\]>\s*\{/,
    "function verifyPublishedCounts(questions,counts,ballotCount){")
  .replace(/new Map<string,number\[\]>/g,"new Map")
  .replace(/new Set<string>/g,"new Set")
  .replace(/countsById\.get\(id\)!\[ix\]/g,"countsById.get(id)[ix]");
assert.ok(!js.includes("Map<string")&&!js.includes("Set<string")&&!js.includes("get(id)!"),"TypeScript non supprimé du test");
const verify=vm.runInNewContext(js+"\nverifyPublishedCounts",{}, {timeout:2000});
assert.equal(typeof verify,"function");
const questions=Array.from({length:8},(_,i)=>({question_id:"q"+String(i+1).padStart(2,"0")}));
const counts=n=>questions.map(q=>({question_id:q.question_id,option_value:9,total:n}));
const keys=()=>Array.from(verify(questions,[],0).values()).map(row=>row.reduce((a,b)=>a+b,0));
assert.deepEqual(keys(),Array(8).fill(0));
for(const n of [10,20,40]){
 const result=verify(questions,counts(n),n);
 assert.equal(result.size,8);
 assert.equal(result.get("q01").reduce((a,b)=>a+b,0),n);
}
const rejected=(rows,ballots,pattern)=>assert.throws(()=>verify(questions,rows,ballots),pattern);
rejected(counts(10),20,/inconsistent_public_snapshot/); // compteur ancien
rejected(counts(20),10,/inconsistent_public_snapshot/); // compteur futur
rejected(counts(10),0,/inconsistent_public_snapshot/);  // données avant seuil
rejected([...counts(10),counts(10)[0]],10,/invalid_snapshot_counts/);
rejected([...counts(10),{question_id:"q99",option_value:9,total:1}],10,/invalid_snapshot_counts/);
rejected(counts(10).map((r,i)=>i? r : {...r,total:-1}),10,/invalid_snapshot_counts/);
rejected(counts(10).map((r,i)=>i? r : {...r,total:1.5}),10,/invalid_snapshot_counts/);
rejected(counts(10).map((r,i)=>i? r : {...r,total:"NaN"}),10,/invalid_snapshot_counts/);
rejected(counts(10).map((r,i)=>i? r : {...r,option_value:30}),10,/invalid_snapshot_counts/);
assert.throws(()=>verify([...questions.slice(0,7),questions[0]],[],0),/invalid_snapshot_questions/);
assert.throws(()=>verify(questions,[],Number.MAX_SAFE_INTEGER+1),/invalid_snapshot/);
const oneOption=counts(10); oneOption[0]={question_id:"q01",option_value:0,total:10};
const result=verify(questions,oneOption,10);
assert.equal(result.get("q01")[2],10);
assert.equal(result.get("q01")[5],0);
const cellMatch=edge.match(/function canPublishCells\([\s\S]*?\n}\n+(?=async function publicResults\(\))/);
assert.ok(cellMatch,"Le filtre réel des petites cellules est introuvable");
const compiled=cellMatch[0].replace(
  /function canPublishCells\([\s\S]*?\): boolean\s*\{/,
  "function canPublishCells(counts){"
);
assert.ok(!compiled.includes("Map<string"),"Le test ne doit pas évaluer du TypeScript");
const cellCheck=vm.runInNewContext(
  "const MIN_NONZERO_CELL=5;\n"+compiled+"\ncanPublishCells",
  {},{timeout:2000}
);
const cells=row=>new Map(questions.map(q=>[q.question_id,row.slice()]));
assert.equal(cellCheck(cells([10,0,0,0,0,0])),true);
assert.equal(cellCheck(cells([5,5,0,0,0,0])),true);
assert.equal(cellCheck(cells([9,1,0,0,0,0])),false,"Une réponse seule doit masquer le lot");
assert.equal(cellCheck(cells([6,4,0,0,0,0])),false,"Quatre réponses doivent masquer le lot");
assert.equal(cellCheck(cells([0,0,0,0,0,0])),true,"Zéros autorisés, seuil global indépendant");
const mixed=cells([10,0,0,0,0,0]);mixed.set("q05",[9,1,0,0,0,0]);
assert.equal(cellCheck(mixed),false,"Une seule question sensible doit masquer l'ensemble");
assert.equal(cellCheck(cells([-1,11,0,0,0,0])),false,"Rejeter une valeur négative");
console.log("OK NOVA : catégories 9/1 et 6/4 masquées, 5/5 possible, suppression globale et zéro conservé.");
console.log("OK NOVA : instantanés cohérents 0/10/20/40, 11 cas de fraude ou lecture concurrente rejetés.");
