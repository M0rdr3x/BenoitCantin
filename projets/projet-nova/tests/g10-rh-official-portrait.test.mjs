import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectProvisionalRhPortrait,makePublicTable} from "../assets/g10-rh-official-portrait-core.mjs";

const document=JSON.parse(await readFile(new URL("../data/portrait-rh-msss-g0-10-2024-2025.json",import.meta.url),"utf8"));
test("18 RSS dont Nunavik et Terres-Cries et ligne Santé Québec distincte",()=>{
 const report=inspectProvisionalRhPortrait(document);
 assert.equal(report.ok,true);
 assert.equal(report.rss_count,18);
 assert.equal(document.regions.find(x=>x.rss_id==="17").persons_2025,2010);
 assert.equal(document.regions.find(x=>x.rss_id==="18").persons_2025,2802);
 assert.equal(document.separate_hq.code,"00");
});
test("somme des personnes exact: 343252 + 804 = 344056",()=>{
 const r=inspectProvisionalRhPortrait(document);
 assert.equal(r.persons_regions,343252);
 assert.equal(r.persons_hq,804);
 assert.equal(r.persons_reported,344056);
});
test("ETC: l'écart de deux unités reste déclaré et non corrigé silencieusement",()=>{
 const r=inspectProvisionalRhPortrait(document);
 assert.equal(r.etc_reported,283740);
 assert.equal(r.etc_discrepancy,2);
 assert.equal(document.totals.etc_2024_2025_exact_reconciliation,false);
});
test("données acquises par parseur tiers sans fausse empreinte ou audit indépendant",()=>{
 assert.equal(document.source.original_sha256,null);
 assert.equal(document.source.original_file_bytes_retained,false);
 assert.equal(document.source.independent_audit,false);
 assert.equal(document.decision.certification_complete,false);
 assert.equal(inspectProvisionalRhPortrait(document).release_authorized,false);
});
test("un effectif modifié sans nouveau total est refusé",()=>{
 const d=structuredClone(document);
 d.regions[0].persons_2025+=50;
 assert.equal(inspectProvisionalRhPortrait(d).ok,false);
});
test("une RSS 19 ou manquante n'est jamais acceptée",()=>{
 const d=structuredClone(document);
 d.regions[17].rss_id="19";
 assert.equal(inspectProvisionalRhPortrait(d).ok,false);
});
test("une réconciliation ETC falsifiée comme exacte est refusée",()=>{
 const d=structuredClone(document);
 d.totals.etc_2024_2025_exact_reconciliation=true;
 assert.equal(inspectProvisionalRhPortrait(d).ok,false);
});
test("une fausse certification ou un projet pilote invalide le registre",()=>{
 const d=structuredClone(document);
 d.decision.pilot_authorized=true;
 assert.equal(inspectProvisionalRhPortrait(d).ok,false);
});
test("un ETC clinique inventé ne peut être publié",()=>{
 const d=structuredClone(document);
 d.regions[0].clinical_fte=8000;
 assert.equal(inspectProvisionalRhPortrait(d).ok,false);
});
test("table publique limitée aux personnes et ETC rémunérés",()=>{
 const tbl=makePublicTable(document);
 assert.equal(tbl.length,18);
 assert.equal(tbl.find(x=>x.rss_id==="06").people_2025,107976);
 assert.ok(tbl.every(x=>!Object.hasOwn(x,"clinical_fte")&&
   x.status==="TRANSCRIPTION_SECONDAIRE_NON_CERTIFIEE"));
});

test("concordance CSV avec JSON: 18 RSS, organisation 00 et total publié",async()=>{
 const csv=await readFile(new URL("../data/portrait-rh-msss-g0-10-2024-2025.csv",import.meta.url),"utf8");
 const lines=csv.trim().split("\n");
 const records=lines.map(line=>[...line.matchAll(/"((?:[^"]|"")*)"/g)]
   .map(x=>x[1].replaceAll('""','"')));
 assert.equal(records.length,21);
 assert.ok(records.every(x=>x.length===9));
 for(let i=0;i<18;i++){
  const row=records[i+1],source=document.regions[i];
  assert.equal(row[0],"RSS");assert.equal(row[1],source.rss_id);
  assert.equal(Number(row[3]),source.persons_2025);
  assert.equal(Number(row[4]),source.etc_2024_2025);
  assert.equal(Number(row[5]),source.persons_2024);
 }
 assert.equal(records[19][0],"ORGANISATION");
 assert.equal(Number(records[19][3]),804);
 assert.equal(records[20][0],"TOTAL_PUBLIE");
 assert.equal(Number(records[20][3]),344056);
 assert.equal(Number(records[20][4]),283740);
 assert.ok(records[20][7].includes("2"));
});
