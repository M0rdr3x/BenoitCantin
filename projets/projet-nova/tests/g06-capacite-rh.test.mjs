import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectRegistry,inspectRHCohort,calculateETPReallocation} from "../assets/g06-capacite-rh-core.mjs";

const matrix=JSON.parse(await readFile(new URL("../data/registre-rh-regional-g0-6-sante.json",import.meta.url),"utf8"));
const region=JSON.parse(await readFile(new URL("../data/portrait-regional-g0-sante-2025.json",import.meta.url),"utf8"));
const pageRH=await readFile(new URL("../capacite-rh-g0-6-sante.html",import.meta.url),"utf8");
const inputs={unit:"ETP_CLINIQUES_PRESENTS_PREMIERE_LIGNE",same_professions:true,
  same_periods_comparable:true,same_rss:true,no_overlap_documented:true,
  public_before:80,nonpublic_before:20,public_after:70,nonpublic_after:30};

test("registres G0.6: 18 régions, valeurs RH null et source ISQ intacte",()=>{
 const v=inspectRegistry(matrix);
 assert.equal(v.regions,18);
 assert.equal(v.regions_without_validated_rh,18);
 assert.equal(v.available_region_costs,0);
 assert.equal(v.gate,"NON_FRANCHI");
 assert.equal(v.pilot_authorized,false);
 assert.equal(v.region_ranking_authorized,false);
 assert.deepEqual(matrix.regions.map(x=>x.rss_id),region.regions.map(x=>x.id));
 for(let i=0;i<18;i++)assert.equal(matrix.regions[i].prior_isq_2025_affiliation_percent,region.regions[i].affiliation_percent);
});

test("provenance: quatre séries distinctes non confondues avec leur téléchargement",()=>{
 assert.equal(matrix.sources.length,4);
 assert.equal(matrix.sources.find(x=>x.id==="MSSS_RH_2425").data_inspected,false);
 assert.match(matrix.sources.find(x=>x.id==="MSSS_RH_2425").status,/ECHOUE/);
 assert.equal(matrix.sources.find(x=>x.id==="RAMQ_STAT").data_inspected,false);
 assert.equal(matrix.sources.find(x=>x.id==="QUEBEC_R22").status,"DEFINITIONS_VERIFIEES_VALEURS_NON_EXTRAITES");
 assert.ok(matrix.measures.every(x=>x.validated===false));
});

test("ETP clinique, effectif et personne rémunérée RAMQ ne sont jamais interchangeables",()=>{
 const expected={etp_cliniques_premiere_ligne:"ETP cliniques",
   effectif_personnes_etablissements:"personnes",
   professionnels_remuneres_RAMQ:"personnes rémunérées",
   heures_sup_obligatoires:"heures"};
 for(const [id,unit] of Object.entries(expected)){
  assert.equal(matrix.measures.find(x=>x.id===id)?.unit,unit);
 }
 assert.ok(matrix.evidence_rules.some(x=>x.includes("ne peut pas les additionner")));
});

test("identité ETP: dix unités déplacées public → non public n'ajoutent aucune capacité totale",()=>{
 const v=calculateETPReallocation(inputs);
 assert.equal(v.baseline_total_fte,100);
 assert.equal(v.after_total_fte,100);
 assert.equal(v.delta_public_fte,-10);
 assert.equal(v.delta_nonpublic_fte,10);
 assert.equal(v.delta_total_fte,0);
 assert.equal(v.additional_clinical_encounters,null);
 assert.equal(v.public_savings,null);
 assert.equal(v.pilot_authorized,false);
});

test("identité ETP: cinq ETP additionnels n'autorisent aucune inférence sur les consultations",()=>{
 const v=calculateETPReallocation({...inputs,public_after:85,nonpublic_after:20});
 assert.equal(v.delta_total_fte,5);
 assert.equal(v.additional_clinical_encounters,null);
 assert.equal(v.quality_effect,null);
 assert.equal(v.public_savings,null);
});

test("le moteur refuse unité, période, périmètre et chevauchement invalides",()=>{
 assert.throws(()=>calculateETPReallocation({...inputs,public_before:null}),/obligatoires/);
 assert.throws(()=>calculateETPReallocation({...inputs,public_before:-1}),/obligatoires/);
 assert.throws(()=>calculateETPReallocation({...inputs,public_before:Infinity}),/obligatoires/);
 assert.throws(()=>calculateETPReallocation({...inputs,unit:"PERSONNES"}),/ETP/);
 assert.throws(()=>calculateETPReallocation({...inputs,same_rss:false}),/non comparables/);
 assert.throws(()=>calculateETPReallocation({...inputs,no_overlap_documented:false}),/non comparables/);
});

test("une preuve RH auto-déclarée sans audit, période, couvertures ni empreinte est rejetée",()=>{
 const invalid=inspectRHCohort({rss_id:"01",period_start:"2025-01-01",period_end:"2025-12-31"});
 assert.equal(invalid.valid,false);
 assert.ok(invalid.missing.includes("audit"));
 assert.ok(invalid.missing.includes("coverage"));
 assert.ok(invalid.missing.includes("source_sha256"));
 const valid=inspectRHCohort({
  rss_id:"01",period_start:"2025-01-01",period_end:"2025-12-31",
  profession:"profession synthétique",clinical_scope:"première ligne test",
  same_population_and_time:true,no_overlap_documented:true,
  includes_ramq_professionals:true,includes_salaried_clinicians:true,
  first_line_activity_verified:true,audit_independent:true,
  evidence_url:"https://example.com/fake-audit",source_sha256:"a".repeat(64)
 });
 assert.equal(valid.valid,true);
});

test("les données RSS 17 et 18 sont absentes de l'enquête, jamais zéros RH",()=>{
 for(const id of ["17","18"]){
  const x=matrix.regions.find(x=>x.rss_id===id);
  assert.equal(x.prior_isq_2025_affiliation_percent,null);
  assert.equal(x.etp_clinical_first_line,null);
  assert.equal(x.status,"EN_ATTENTE_DE_DONNEES_AGREGEES");
 }
});

test("aucune réforme ni économie ne résulte du registre RH",()=>{
 assert.equal(matrix.decision.g0,"NON_FRANCHI");
 assert.equal(matrix.decision.pilot_authorized,false);
 assert.equal(matrix.decision.privatization_authorized,false);
 assert.equal(matrix.decision.funding_approved,false);
 assert.equal(matrix.decision.savings_certified,null);
 assert.equal(matrix.decision.external_audit_completed,false);
});

test("page G0.6 : 18 régions, 11 mesures et distinction des unités sont affichées",()=>{
 assert.equal((pageRH.match(/class="rh-code"/g)||[]).length,18);
 assert.equal((pageRH.match(/class="rh-card"/g)||[]).length,13);
 assert.equal((pageRH.match(/class="rh-unknown"/g)||[]).length,54);
 assert.match(pageRH,/un déplacement de travailleurs n'est pas un recrutement net/i);
 assert.ok(pageRH.includes("protocole-g0-6-capacite-personnel-sante-v1.md"));
 assert.ok(pageRH.includes("registre-rh-regional-g0-6-sante.json"));
 assert.ok(pageRH.includes("</main>")&&pageRH.includes("</html>"));
});
