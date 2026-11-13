import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const js=await readFile(new URL("../assets/boussole-electorale.js",import.meta.url),"utf8");
const source=JSON.parse(await readFile(new URL("../data/boussole-preuves-2026.json",import.meta.url),"utf8"));
const parties=JSON.parse(await readFile(new URL("../data/boussole-partis-2026.json",import.meta.url),"utf8"));
test("écran public: les fiches ne sont plus présentées comme finalisées par un humain",()=>{
 assert.ok(js.includes("Fiches pré-codées"));
 assert.ok(js.includes("avis externe requis"));
 assert.ok(!js.includes("Fiches finalisées"));
});
test("écran public: le type IA apparaît à côté de la deuxième lecture",()=>{
 assert.ok(js.includes("Nature de la relecture"));
 assert.ok(js.includes("Relecture par IA, sans attestation indépendante"));
 assert.ok(js.includes("Relecture déclarée, attestation externe non vérifiée"));
 assert.ok(js.includes("Relectures documentaires consignées"));
});
test("synthèse: aucune révision IA n'est présentée comme signature humaine externe",()=>{
 assert.ok(js.includes("aucune attestation humaine externe n'est fournie ici"));
 assert.ok(js.includes("La comparaison des partis reste désactivée."));
 assert.ok(!js.includes("en attente d’une deuxième révision indépendante"));
});
test("interface: les fiches inconnues ne deviennent pas positions supposées",()=>{
 assert.ok(js.includes("Aucune preuve pré-codée ne permet d’établir une position"));
 assert.ok(js.includes("Cela ne signifie ni appui, ni opposition, ni neutralité."));
 assert.ok(js.includes("Position indéterminée — source ambiguë"));
});
test("corpus historique non altéré, statut politique et classement demeurent désactivés",()=>{
 assert.equal(source.evidenceRecords.length,140);
 assert.equal(source.evidenceRecords.filter(x=>x.finalizable).length,140);
 assert.equal(source.evidenceRecords.filter(x=>/ChatGPT/i.test(x.secondIndependentReview?.reviewer||"")).length,140);
 assert.ok(parties.parties.every(x=>x.comparisonEligible===false));
 assert.ok(parties.parties.every(x=>Object.keys(x.positions||{}).length===0));
});
