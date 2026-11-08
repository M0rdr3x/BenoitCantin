import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const matrix=JSON.parse(await readFile(new URL("../data/matrice-juridique-p0-2026-11-08.json",import.meta.url),"utf8"));
test("P0: 12 questions, 2 contextes distincts, sans conclusion inventée",()=>{
  assert.equal(matrix.schema,"nova-matrice-juridique-p0/v1");
  assert.equal(matrix.date,"2026-11-08");
  assert.equal(matrix.cases.length,12);
  assert.equal(new Set(matrix.cases.map(x=>x.id)).size,12);
  for(const row of matrix.cases){
    assert.match(row.id,/^J(0[1-9]|1[0-2])$/);
    assert.equal(row.statut,"A_EXAMINER");
    for(const context of matrix.jurisdictions){
      assert.equal(row[context]?.legal_status,"NON_VERIFIE");
      assert.ok(row[context].question.trim().length>30);
    }
    assert.equal(row.independent_legal_opinion,null);
    assert.equal(row.adoption_decision,null);
    assert.deepEqual(row.evidence_urls,[]);
    assert.ok(row.source.startsWith("official/"));
    assert.ok(row.required_evidence.length>20);
  }
});
test("P0: inventaire ne relève pas les 47 points ni ne délivre de mandat",()=>{
  assert.equal(matrix.baseline_points,47);
  assert.equal(matrix.maximum_points,100);
  assert.equal(matrix.increment_at_creation,0);
  assert.equal(matrix.independent_juridical_audit_completed,false);
  assert.ok(matrix.cases.every(x=>x.owner_real_name===null&&x.deadline_authorized===null));
  assert.equal(matrix.status,"INVENTAIRE_CANDIDAT_NON_ADOPTE");
});
