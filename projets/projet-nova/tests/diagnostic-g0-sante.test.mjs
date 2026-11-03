import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const diagnostic=JSON.parse(await readFile(new URL("../data/diagnostic-g0-sante-premiere-ligne-2025.json",import.meta.url),"utf8"));
const registry=JSON.parse(await readFile(new URL("../data/registre-donnees-services-nova-sinjira.json",import.meta.url),"utf8"));
const page=await readFile(new URL("../diagnostic-g0-sante.html",import.meta.url),"utf8");
const sourceMap=new Map(diagnostic.sources.map(s=>[s.id,s]));
const acquisition=JSON.parse(await readFile(new URL("../data/plan-acquisition-donnees-g0-sante.json",import.meta.url),"utf8"));

test("G0 santé : aucun pilote, financement, coût par épisode ou économie prétendus",()=>{
  assert.equal(diagnostic.g0_completed,false);
  assert.equal(diagnostic.authorized_pilot,false);
  assert.equal(diagnostic.authorized_funding,false);
  assert.equal(diagnostic.external_audit_completed,false);
  assert.equal(diagnostic.legal_review_completed,false);
  for(const k of ["cost_public_per_episode","cost_private_per_episode","cost_cooperative_per_episode","expected_savings"])
    assert.equal(diagnostic[k],null,`${k} doit rester null`);
  const nv03=registry.dossiers.find(x=>x.id==="NV-03");
  assert.equal(nv03.chiffrage_valide,false);
  assert.equal(nv03.diagnostic_non_financier.porte_g0_franchie,false);
  for(const v of Object.values(nv03.couts_par_mode)) assert.equal(v,null);
});

test("toutes les observations ont une provenance et une période, aucune valeur vide",()=>{
  assert.equal(diagnostic.observations.length,4);
  for(const o of diagnostic.observations){
    assert.ok(sourceMap.has(o.source_id));
    assert.ok(o.population && o.time_period && o.precision && o.label);
    assert.equal(o.unit,"percent");
    assert.ok(Number.isFinite(o.value) && o.value>=0 && o.value<=100);
  }
  assert.equal(sourceMap.size,diagnostic.sources.length);
});

test("enquête 2025 : chiffres explicitement bornés à la population observée",()=>{
  const o=Object.fromEntries(diagnostic.observations.map(x=>[x.id,x]));
  assert.equal(o["G0-SAN-01"].value,82);
  assert.equal(o["G0-SAN-02"].value,18);
  assert.equal(o["G0-SAN-03"].value,10);
  assert.equal(o["G0-SAN-04"].value,19);
  assert.equal(o["G0-SAN-03"].scope,"association_not_causation");
  assert.equal(o["G0-SAN-04"].scope,"association_not_causation");
  assert.equal(diagnostic.diagnostic_population.respondents,9391);
  assert.equal(diagnostic.diagnostic_population.survey_collection_start,"2025-01-06");
  assert.equal(diagnostic.diagnostic_population.survey_collection_end,"2025-05-11");
  assert.equal(diagnostic.diagnostic_population.publication_date,"2026-11-02");
  assert.match(diagnostic.diagnostic_population.excluded,/Nunavik/);
});

test("distinguer les indicateurs administratifs 2024 et les observations d'enquête 2025",()=>{
  assert.equal(diagnostic.context_not_comparable_as_trend.length,2);
  assert.equal(diagnostic.context_not_comparable_as_trend[0].value,72);
  assert.equal(diagnostic.context_not_comparable_as_trend[1].value,84.3);
  assert.notEqual(diagnostic.context_not_comparable_as_trend[0].source_id,diagnostic.observations[0].source_id);
  assert.ok(diagnostic.notes.some(s=>s.includes("définitions et populations différentes")));
});

test("G0 non franchi : neuf jeux de données exigés avant G1",()=>{
  assert.equal(diagnostic.missing_before_g0_complete.length,9);
  assert.ok(diagnostic.missing_before_g0_complete.every(x=>x.status==="NON_RECU"));
  assert.match(diagnostic.next_gate,/G0/);
});

test("page publique : déclaration de statut, source directe et lien vers la preuve",()=>{
  assert.match(page,/NON FRANCHIE/);
  assert.match(page,/2026/);
  assert.ok(page.includes("statistique.quebec.ca/fr/document/utilisation-services-sante-et-services-sociaux/publication/utilisation-services-sante-sociaux-premiere-ligne-2025"));
  assert.ok(page.includes("diagnostic-g0-sante-premiere-ligne-v1.md"));
  assert.ok(page.includes("</main>") && page.includes("</html>"));
});

test("plan de demandes G0 sans demande transmise ni données personnelles",()=>{
  assert.equal(acquisition.status,"PLAN_NON_TRANSMIS_NON_AUTORISE");
  assert.equal(acquisition.demandes.length,9);
  const ids=diagnostic.missing_before_g0_complete.map(x=>x.id).sort();
  assert.deepEqual(acquisition.demandes.map(x=>x.id).sort(),ids);
  for(const r of acquisition.demandes) {
    assert.equal(r.statut,"NON_TRANSMISE");
    assert.equal(r.autorite_confirmee,null);
    assert.equal(r.demande_envoyee_le,null);
    assert.equal(r.reponse_recue_le,null);
    assert.equal(r.validation_independante,false);
    assert.equal(r.proteger_donnees_personnelles,true);
    assert.ok(r.autorites_candidates.length>=1);
    assert.ok(r.champs_de_metadonnees_exiges.includes("territoire"));
  }
});
