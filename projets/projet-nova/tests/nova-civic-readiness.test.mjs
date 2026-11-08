import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const d=JSON.parse(await readFile(new URL("../../../docs/nova-sondages/reception-sondage-boussole-2026-11-08.json",import.meta.url),"utf8"));
const historical=JSON.parse(await readFile(new URL("../data/validation-sondage-boussole-2026-11-07.json",import.meta.url),"utf8"));
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
test("boussole : six portes vérifiées sur douze dans la matrice du 8 novembre",()=>{
 assert.equal(d.compass.questions,64);
 assert.equal(d.compass.dimensions,16);
 assert.equal(d.compass.gates.length,12);
 assert.equal(passed(d.compass),6);
 validate(d.compass);
});
test("sondage : six portes contrôlées sur onze",()=>{
 assert.equal(d.poll.questions,8);
 assert.equal(d.poll.gates.length,11);
 assert.equal(passed(d.poll),6);
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

test("audit de lecture seule Supabase : version et preuves, sans ouverture du vote",async()=>{
 const review=d.cross_cutting.supabase_readonly_review;
 assert.equal(review.audit_date,"2026-11-08");
 assert.equal(d.poll.edge_function_version,6);
 assert.equal(review.edge_function_version,d.poll.edge_function_version);
 assert.equal(review.edge_source_exactly_matches_github,true);
 assert.equal(review.tables_with_rls,5);
 assert.equal(review.anon_and_authenticated_direct_crud_grants,false);
 assert.equal(review.submit_rpc_service_role_only,true);
 for(const key of ["receipt_rows","raw_count_rows","published_count_rows","published_ballots"]){
  assert.equal(review[key],0,key);
 }
 assert.equal(d.poll.gates.find(x=>x.id==="POLL_DB_ACCESS").status,"PASSED");
 assert.equal(d.poll.gates.find(x=>x.id==="POLL_PRIVATE_PREFLIGHT").status,"PENDING");
 assert.equal(d.poll.gates.find(x=>x.id==="POLL_LEGAL_REVIEW").status,"PENDING");
 assert.equal(d.poll.published_in_source,false);
 assert.equal(d.decision.opening_poll_approved,false);
 const text=await readFile(new URL("../../../docs/nova-sondages/verification-supabase-lecture-seule-2026-11-08.md",import.meta.url),"utf8");
 assert.match(text,/version \*\*6\*\*/);
 assert.match(text,/NON HOMOLOGUÉ/);
 assert.match(text,/Aucun vote/);
});

test("le parcours E2E local de 64 questions est prouvé sur trois moteurs, le live ne l’est pas",()=>{
 assert.equal(d.cross_cutting.score_parity_test_cases,260);
 assert.equal(d.cross_cutting.last_browser_all_skip_questions_verified,28);
 assert.equal(d.cross_cutting.last_browser_full_64_completed,false);
 assert.equal(d.cross_cutting.ci_local_compass_full_64_verified,true);
 assert.deepEqual(d.cross_cutting.ci_local_compass_full_64_browsers,["chromium","firefox","webkit"]);
 assert.equal(d.compass.gates.find(x=>x.id==="COMPASS_FULL_64_RESULT").status,"PASSED");
 assert.equal(d.compass.gates.find(x=>x.id==="COMPASS_FULL_64_RESULT").scope,"browser_e2e_local_pr_881_seulement_non_live");
 assert.match(d.cross_cutting.ci_local_compass_full_64_workflow_url,/actions\/runs\/42531076014$/);
 assert.equal(d.compass.gates.find(x=>x.id==="COMPASS_SCORE_PARITY").status,"PASSED");
 assert.equal(d.compass.gates.find(x=>x.id==="COMPASS_PARTIAL_PROFILE_RELEASE").status,"PENDING");
});
test("revue du code serveur sans autoriser la soumission en production",()=>{
 assert.equal(d.poll.gates.find(x=>x.id==="POLL_SERVER_SOURCE_REVIEW").status,"PASSED");
 assert.equal(d.cross_cutting.vote_post_live_tested,false);
 assert.equal(d.poll.published_in_source,false);
 assert.equal(d.decision.opening_poll_approved,false);
});


test("les taux publics de réception dérivent exactement de la matrice versionnée",async()=>{
 const html=await readFile(new URL("../sondages-a-valider.html",import.meta.url),"utf8");
 const start=html.indexOf('id="etat-validation-outils"');
 const end=html.indexOf("</section>",start);
 assert.ok(start>=0&&end>start,"Section accessible sur la page de lecture seule");
 const section=html.slice(start,end);
 const numbers=[
  {object:d.poll,denominator:11,expected:6,label:"sondage",name:"Critères de réception du sondage"},
  {object:d.compass,denominator:12,expected:6,label:"boussole",name:"Critères de réception de la boussole"}
 ];
 for(const item of numbers){
  const n=passed(item.object),total=item.object.gates.length;
  assert.equal(total,item.denominator,item.label);
  assert.equal(n,item.expected,item.label);
  const percent=(100*n/total).toFixed(1).replace(".",",")+" %";
  assert.ok(section.includes(percent),percent);
  assert.ok(section.includes(n+" critères sur "+total),item.label);
  assert.ok(section.includes('aria-label="'+item.name+'"'));
  assert.ok(section.includes('aria-valuenow="'+n+'"'),item.label);
  assert.ok(section.includes('aria-valuemax="'+total+'"'),item.label);
 }
 assert.ok(section.includes("8 novembre 2026"));
 assert.match(section,/les pourcentages ci-dessous mesurent uniquement/i);
 assert.ok(section.includes("matrice de réception officielle"));
});
test("la grille d'avancement ne lance aucun vote ni une comparaison partisane",async()=>{
 const html=await readFile(new URL("../sondages-a-valider.html",import.meta.url),"utf8");
 const start=html.indexOf('id="etat-validation-outils"');
 const end=html.indexOf("</section>",start);
 const section=html.slice(start,end);
 assert.ok(start>=0&&end>start);
 assert.doesNotMatch(section,/<form\b|<input\b|type="submit"|turnstile|onclick=/i);
 assert.ok(section.includes("Collecte fermée"));
 assert.ok(section.includes("comparaison avec les partis demeure désactivée"));
 assert.equal(d.poll.published_in_source,false);
 assert.equal(d.compass.comparison_enabled,false);
 assert.equal(d.decision.opening_poll_approved,false);
});
test("les pourcentages de réception ne sont pas des autorisations de production",()=>{
 assert.ok(passed(d.poll)<d.poll.gates.length);
 assert.ok(passed(d.compass)<d.compass.gates.length);
 assert.equal(d.decision.both_tools_100_percent,false);
 assert.equal(d.decision.deployments_verified,false);
 assert.equal(d.status,"NON_HOMOLOGUE");
 assert.equal(d.programme_audit_g012.unrelated_to_ui_readiness,true);
});


test("les deux outils officiels rendent visible l'état daté sans ouvrir le sondage",async()=>{
 const [pollHtml,compassHtml]=await Promise.all([
  readFile(new URL("../sondage-citoyen.html",import.meta.url),"utf8"),
  readFile(new URL("../boussole-electorale.html",import.meta.url),"utf8")
 ]);
 const pollPct=(100*passed(d.poll)/d.poll.gates.length).toFixed(1).replace(".",",")+" %";
 const compassPct=(100*passed(d.compass)/d.compass.gates.length).toFixed(1).replace(".",",")+" %";
 assert.ok(pollHtml.includes(pollPct));
 assert.ok(compassHtml.includes(compassPct));
 assert.ok(pollHtml.includes("6 critères sur 11 validés"));
 assert.ok(compassHtml.includes("6 critères sur 12 validés"));
 assert.ok(compassHtml.includes("assets/boussole-electorale.js?v=3.4.25"),"Cache de la boussole invalidé après correction");
 assert.ok(pollHtml.includes("la collecte reste fermée"));
 for(const html of [pollHtml,compassHtml]){
  assert.ok(html.includes('href="sondages-a-valider.html#etat-validation-outils"'));
  assert.ok(html.includes("Suivi de réception au 8 novembre 2026"));
 }
 assert.match(pollHtml,/id="poll-send"[^>]*\bdisabled\b/);
});


test("le registre de 7 novembre demeure historique, sans réécriture des preuves",()=>{
 assert.equal(historical.as_of,"2026-11-07");
 assert.equal(historical.compass.gates.find(x=>x.id==="COMPASS_FULL_64_RESULT").status,"PENDING");
 assert.equal(d.as_of,"2026-11-08");
 assert.equal(d.previous_audit,"projets/projet-nova/data/validation-sondage-boussole-2026-11-07.json");
 assert.equal(d.summary.compass.passed,6);
 assert.equal(d.summary.compass.total,12);
 assert.equal(d.summary.compass.percent,50);
 assert.equal(d.summary.poll.passed,6);
 assert.equal(d.summary.poll.percent,54.5);
});
test("l'E2E local ne valide pas l'ouverture du sondage ni le déploiement public",()=>{
 assert.equal(d.cross_cutting.latest_public_scripts_deployed_verified,false);
 assert.equal(d.cross_cutting.independent_security_audit_completed,false);
 assert.equal(d.decision.deployments_verified,false);
 assert.equal(d.decision.opening_poll_approved,false);
 assert.equal(d.poll.published_in_source,false);
 assert.equal(d.compass.comparison_enabled,false);
 assert.equal(d.compass.gates.find(x=>x.id==="COMPASS_CROSS_BROWSER").status,"PENDING");
 assert.equal(d.compass.gates.find(x=>x.id==="COMPASS_PARTIAL_PROFILE_RELEASE").status,"PENDING");
 assert.equal(d.compass.gates.find(x=>x.id==="COMPASS_ACCESSIBILITY").status,"PENDING");
});
