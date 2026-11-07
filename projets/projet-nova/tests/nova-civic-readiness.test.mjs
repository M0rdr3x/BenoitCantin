import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const d=JSON.parse(await readFile(new URL("../data/validation-sondage-boussole-2026-11-07.json",import.meta.url),"utf8"));
const types=["PASSED","PENDING"];
const passed=x=>x.gates.filter(g=>g.status==="PASSED").length;
const validate=x=>{
 assert.equal(x.all_mandatory_gates_passed,false);
 const ids=x.gates.map(g=>g.id);
 assert.equal(new Set(ids).size,ids.length);
 for(const gate of x.gates){
   assert.ok(types.includes(gate.status));
   assert.ok(typeof gate.criteria==="string"&&gate.criteria.length>15);
   assert.ok(typeof gate.evidence==="string"&&gate.evidence.length>0);
   assert.ok(typeof gate.scope==="string"&&gate.scope.length>0);
 }
};
test("deux outils : matrice complète et audit Nova distinct",()=>{
 assert.equal(d.schema,"nova-civic-two-tools-readiness/v1");
 assert.equal(d.programme_audit_g012.preparation_percent,47);
 assert.equal(d.programme_audit_g012.unrelated_to_ui_readiness,true);
 assert.equal(d.decision.both_tools_100_percent,false);
 assert.equal(d.status,"NON_HOMOLOGUE");
});
test("boussole : quatre portes passées et six encore en attente",()=>{
 assert.equal(d.compass.questions,64);
 assert.equal(d.compass.dimensions,16);
 assert.equal(d.compass.gates.length,10);
 assert.equal(passed(d.compass),4);
 validate(d.compass);
});
test("sondage : cinq portes passées et cinq encore en attente",()=>{
 assert.equal(d.poll.questions,8);
 assert.equal(d.poll.gates.length,10);
 assert.equal(passed(d.poll),5);
 validate(d.poll);
});
test("vote en production non simulé, ni ouvert artificiellement",()=>{
 assert.equal(d.poll.published_in_source,false);
 assert.equal(d.poll.has_recorded_ballots,false);
 assert.equal(d.poll.public_publication_ballots,0);
 assert.equal(d.cross_cutting.production_ballots_sent_for_test,0);
 assert.equal(d.decision.opening_poll_approved,false);
});
test("aucune certification de déploiement ou d'audit externe non fondée",()=>{
 assert.equal(d.cross_cutting.latest_github_actions_pass_verified,false);
 assert.equal(d.cross_cutting.latest_public_scripts_deployed_verified,false);
 assert.equal(d.cross_cutting.independent_security_audit_completed,false);
 assert.equal(d.decision.deployments_verified,false);
});
test("aucune comparaison partis n'est activée avant les preuves",()=>{
 assert.equal(d.compass.comparison_enabled,false);
 assert.equal(d.cross_cutting.party_comparison_enabled,false);
 assert.equal(d.decision.party_comparison_approved,false);
 assert.equal(d.compass.gates.find(g=>g.id==="COMPASS_DOCUMENTARY_VALIDATION").status,"PENDING");
});
test("la mise en service exige une autorisation séparée",()=>{
 assert.equal(d.poll.gates.find(g=>g.id==="POLL_APPROVAL_GO_LIVE").status,"PENDING");
 assert.equal(d.poll.gates.find(g=>g.id==="POLL_LEGAL_REVIEW").status,"PENDING");
 assert.equal(d.poll.gates.find(g=>g.id==="POLL_CAPTCHA_ANTIREPLAY").status,"PENDING");
});
test("le score politique 47/100 n'est jamais déduit du nombre de tests",()=>{
 assert.equal(d.decision.overall_programme_percent_revised,false);
 assert.equal(d.programme_audit_g012.preparation_percent,47);
});
