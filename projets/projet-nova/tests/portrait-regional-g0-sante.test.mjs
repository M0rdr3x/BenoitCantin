import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const data=JSON.parse(await readFile(new URL("../data/portrait-regional-g0-sante-2025.json",import.meta.url),"utf8"));
const baseline=JSON.parse(await readFile(new URL("../data/diagnostic-g0-sante-premiere-ligne-2025.json",import.meta.url),"utf8"));
const page=await readFile(new URL("../portrait-regional-g0-sante.html",import.meta.url),"utf8");

test("découpage régional : 18 RSS uniques de 01 à 18, pas 17 régions administratives",()=>{
 assert.equal(data.regions.length,18);
 assert.deepEqual(data.regions.map(x=>x.id),Array.from({length:18},(_,i)=>String(i+1).padStart(2,"0")));
 assert.equal(new Set(data.regions.map(x=>x.name)).size,18);
 assert.match(data.geography,/PAS régions administratives/);
});
test("2025 : régions 17 et 18 non enquêtées, jamais zéro",()=>{
 const outside=data.regions.filter(x=>!x.included_in_survey);
 assert.deepEqual(outside.map(x=>x.id),["17","18"]);
 for(const r of outside) {
  assert.equal(r.interpretation_status,"HORS_CHAMP_ENQUETE");
  assert.equal(r.affiliation_percent,null);
  assert.equal(r.relative_to_rest_of_quebec,null);
  assert.equal(r.needs_xlsx_review,false);
 }
});
test("six différences régionales explicitement signalées et sans valeur chiffrée inventée",()=>{
 const highlighted=data.regions.filter(x=>x.relative_to_rest_of_quebec!==null);
 assert.equal(highlighted.length,6);
 assert.deepEqual(highlighted.map(x=>x.id),["01","02","06","10","11","14"]);
 const below=highlighted.filter(x=>x.relative_to_rest_of_quebec==="au-dessous du reste du Québec");
 const above=highlighted.filter(x=>x.relative_to_rest_of_quebec==="au-dessus du reste du Québec");
 assert.deepEqual(below.map(x=>x.id),["06"]);
 assert.deepEqual(above.map(x=>x.id),["01","02","10","11","14"]);
 assert.equal(data.regions.filter(x=>x.included_in_survey&&x.relative_to_rest_of_quebec===null).length,10);
 assert.equal(data.regions.filter(x=>x.included_in_survey&&x.affiliation_percent===null).length,16);
});
test("statistiques, patientèle et comparaisons de coûts absentes de manière explicite",()=>{
 for(const r of data.regions){
  assert.equal(r.affiliation_percent,null);
  assert.equal(r.confidence_interval,null);
  assert.equal(r.sample_size,null);
  assert.equal(r.cost_public_per_episode,null);
  assert.equal(r.cost_private_per_episode,null);
  assert.equal(r.health_outcomes,null);
  assert.equal(r.priority_for_pilot,null);
 }
 assert.equal(data.public_province.affiliation_percent,82);
 assert.equal(baseline.g0_completed,false);
 assert.equal(baseline.authorized_pilot,false);
});
test("un lien vers le XLSX non téléchargé n'est jamais marqué comme analysé",()=>{
 const xlsx=data.primary_sources.find(x=>x.id==="ISQ_EQUSSSS_2025_TABLEAUX");
 assert.ok(xlsx.url.endsWith(".xlsx"));
 assert.equal(xlsx.no_row_level_values_extracted,true);
 assert.match(xlsx.access_status,/TELECHARGEMENT_IMPOSSIBLE/);
 assert.match(page,/téléchargement a échoué/);
});
test("page régionale : 18 lignes et exclusion expliquée",()=>{
 assert.equal((page.match(/class="region-id"/g)||[]).length,18);
 assert.match(page,/aucune décision de financement/);
 assert.match(page,/Nunavik/);
 assert.match(page,/Terres-Cries-de-la-Baie-James/);
 assert.match(page,/Non extrait/);
 assert.ok(page.includes("</main>")&&page.includes("</html>"));
});
