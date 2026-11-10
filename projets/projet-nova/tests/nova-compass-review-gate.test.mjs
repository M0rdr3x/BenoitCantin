import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectReviewGate} from "../assets/nova-compass-review-gate-core.mjs";
const read=async path=>JSON.parse(await readFile(new URL("../data/"+path,import.meta.url),"utf8"));
const base={
 questionnaire:await read("boussole-electorale-v2.json"),
 parties:await read("boussole-partis-2026.json"),
 sources:await read("boussole-sources-partis-2026.json"),
 preuves:await read("boussole-preuves-2026.json")
};
const run=x=>inspectReviewGate(x||base);
const copy=()=>structuredClone(base);
test("quatre corpus cohérents et positionnement public toujours fermé",()=>{
 const r=run();
 assert.equal(r.ok,true,r.errors.join(" ; "));
 assert.equal(r.party_comparison_authorized,false);
 assert.equal(r.release_documentary_gate_passed,false);
 assert.equal(r.percent_complete,null);
});
test("140 fiches et 140 relectures ChatGPT ne valent PAS 140 avis humains",()=>{
 const r=run();
 assert.equal(r.counts.evidence_candidate_count,140);
 assert.equal(r.counts.declared_finalizable,140);
 assert.equal(r.counts.described_second_reads,140);
 assert.equal(r.counts.ai_documentary_second_reads,140);
 assert.equal(r.reviewerCategories.non_ai_named,0);
 assert.equal(r.independent_human_reviews_attested_in_this_audit,0);
 assert.equal(r.decision,"NO_GO_REVIEW_HUMAN_ATTESTATION_NOT_PRESENT");
});
test("toutes les URL sont structurellement https; cela ne prouve PAS leur contenu",()=>{
 const r=run();
 assert.equal(r.counts.source_urls_structurally_valid,140);
 assert.equal(r.external_source_content_verification_performed,false);
 assert.equal(r.external_reviewer_identity_authentication_performed,false);
});
test("22 formations et 64 questions sans score partisan",()=>{
 assert.equal(base.parties.parties.length,22);
 assert.equal(base.questionnaire.questions.length,64);
 assert.equal(base.preuves.questions.length,64);
 assert.equal(base.parties.parties.filter(x=>x.comparisonEligible).length,0);
 assert.equal(base.parties.parties.filter(x=>Object.keys(x.positions||{}).length).length,0);
});
test("une fiche avec même question et parti en double est refusée",()=>{
 const x=copy();x.preuves.evidenceRecords.push(structuredClone(x.preuves.evidenceRecords[0]));
 assert.ok(run(x).errors.includes("FICHE_PREUVE_DUPLIQUEE"));
});
test("une preuve avec mauvaise direction politique n'est pas libérée",()=>{
 const x=copy();x.preuves.evidenceRecords[0].proposedStatus="documented_opposition";
 assert.ok(run(x).errors.includes("FICHE_MATRICE_NON_CONCORDANTE"));
});
test("le retrait d'une preuve de la matrice est détecté",()=>{
 const x=copy();x.preuves.evidenceRecords.splice(0,1);
 assert.ok(run(x).errors.includes("MATRICE_SANS_FICHE"));
});
test("URL non sécurisée ou altérée rejetée sans vérifier politiquement la source",()=>{
 const x=copy();x.preuves.evidenceRecords[0].sourceUrl="http://exemple.test/source";
 assert.ok(run(x).errors.includes("SOURCE_URL_NON_SECURISÉE"));
 const y=copy();y.preuves.evidenceRecords[0].sourceUrl="https://user:pass@example.test/source";
 assert.ok(run(y).errors.includes("SOURCE_URL_NON_SECURISÉE"));
});
test("libérer une formation dans le registre sans revue externe est bloqué",()=>{
 const x=copy();x.parties.parties[0].comparisonEligible=true;
 assert.ok(run(x).errors.includes("COMPARAISON_POLITIQUE_ACTIVEE_SANS_RECEPTEUR_INDEPENDANT"));
 assert.equal(run(x).party_comparison_authorized,false);
});
test("un score partisan ajouté avant avis humain n'est pas autorisé",()=>{
 const x=copy();x.parties.parties[0].positions={q01:3};
 assert.ok(run(x).errors.includes("COMPARAISON_POLITIQUE_ACTIVEE_SANS_RECEPTEUR_INDEPENDANT"));
});
test("une fausse déclaration de relecteur humain dans la source ne devient pas une attestation",()=>{
 const x=copy();x.preuves.evidenceRecords[0].secondIndependentReview.reviewer="Expert externe";
 const r=run(x);
 assert.equal(r.reviewerCategories.non_ai_named,1);
 assert.equal(r.independent_human_reviews_attested_in_this_audit,0);
 assert.equal(r.release_documentary_gate_passed,false);
});
test("retirer la règle de deuxième lecture ne débloque pas la publication",()=>{
 const x=copy();x.preuves.evidenceRules.secondIndependentReviewRequiredBeforeFinalization=false;
 const r=run(x);
 assert.ok(r.errors.includes("REGLE_DE_RELECTURE_OMISE"));
 assert.equal(r.party_comparison_authorized,false);
});
test("corpus source manquant ou incomplet interdit tout score de validation",()=>{
 const x=copy();x.preuves.partyIds.pop();
 assert.equal(run(x).ok,false);
 assert.equal(run(x).percent_complete,null);
 assert.equal(inspectReviewGate(null).release_documentary_gate_passed,false);
});
