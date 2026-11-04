import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const data=JSON.parse(await readFile(new URL("../data/portrait-regional-g0-sante-2025.json",import.meta.url),"utf8"));
const diagnostic=JSON.parse(await readFile(new URL("../data/diagnostic-g0-sante-premiere-ligne-2025.json",import.meta.url),"utf8"));
const registre=JSON.parse(await readFile(new URL("../data/registre-donnees-services-nova-sinjira.json",import.meta.url),"utf8"));
const page=await readFile(new URL("../portrait-regional-g0-sante.html",import.meta.url),"utf8");
const byId=Object.fromEntries(data.regions.map(x=>[x.id,x]));
const observed=data.regions.filter(x=>x.included_in_survey);

test("les 18 RSS sont uniques; 16 couvertes et deux exclues sans valeurs fabriquées",()=>{
 assert.equal(data.regions.length,18);
 assert.deepEqual(data.regions.map(x=>x.id),Array.from({length:18},(_,i)=>String(i+1).padStart(2,"0")));
 assert.equal(new Set(data.regions.map(x=>x.name)).size,18);
 assert.equal(observed.length,16);
 assert.deepEqual(data.regions.filter(x=>!x.included_in_survey).map(x=>x.id),["17","18"]);
 assert.ok(data.regions.filter(x=>!x.included_in_survey).every(x=>x.affiliation_percent===null));
 assert.match(data.geography,/PAS régions administratives/);
});

test("16 chiffres d'affiliation fidèles au tableau 8.1 du PDF ISQ (ordre RSS)",()=>{
 const expected=[88.9,87.6,82.9,85.1,79.3,77.1,85.8,80.0,81.1,88.8,89.1,80.3,84.8,87.2,79.8,83.9];
 assert.deepEqual(observed.map(x=>x.affiliation_percent),expected);
 assert.equal(data.public_province.affiliation_percent,82.0);
 assert.ok(observed.every(x=>x.source_of_numeric_value==="ISQ_PANORAMA_2026_TABLEAU_8_1"));
 assert.equal(data.pdf_tabular_data.regional_affiliation_numeric_count,16);
 assert.equal(data.pdf_tabular_data.full_xlsx_verification,false);
});

test("écarts statistiquement rapportés : cinq au-dessus, Montréal au-dessous",()=>{
 assert.deepEqual(observed.filter(x=>x.affiliation_statistical_difference==="SUPERIEUR_RESTE_QUEBEC").map(x=>x.id),["01","02","10","11","14"]);
 assert.deepEqual(observed.filter(x=>x.affiliation_statistical_difference==="INFERIEUR_RESTE_QUEBEC").map(x=>x.id),["06"]);
 assert.ok(observed.filter(x=>x.affiliation_statistical_difference==="AUCUN_ECART_SIGNALE_DANS_TABLEAU").length===10);
 for(const x of observed){
  const sign=x.affiliation_statistical_difference;
  if(sign==="SUPERIEUR_RESTE_QUEBEC")assert.equal(x.relative_to_rest_of_quebec,"au-dessus du reste du Québec");
  if(sign==="INFERIEUR_RESTE_QUEBEC")assert.equal(x.relative_to_rest_of_quebec,"au-dessous du reste du Québec");
 }
});

test("trois lieux de suivi parmi les affiliés totalisent environ 100 %, sans prétendre au financement",()=>{
 const qc=data.public_province.usual_follow_up_affiliated;
 assert.deepEqual([qc.setting_clinic_or_gmf_or_clsc_percent,qc.hospital_or_other_percent,qc.private_clinic_percent],[85.1,7.8,7.1]);
 for(const x of observed){
  const v=x.usual_follow_up_affiliated;
  assert.ok(Math.abs(v.setting_clinic_or_gmf_or_clsc_percent+v.hospital_or_other_percent+v.private_clinic_percent-100)<=0.21);
  assert.match(v.denominator,/personnes AFFILIÉES/);
  assert.equal(v.source_id,"ISQ_PANORAMA_2026_TABLEAU_8_1");
 }
 assert.equal(byId["06"].usual_follow_up_affiliated.private_clinic_percent,8.9);
 assert.equal(byId["10"].usual_follow_up_affiliated.private_clinic_percent,2.0);
 assert.match(byId["10"].usual_follow_up_affiliated.private_clinic_quality_flag,/IMPRECIS/);
});

test("tableau 8.3 : démarche vers urgence, sous-population différente et qualité explicite",()=>{
 assert.equal(data.public_province.nonurgent_semiurgent_emergency_step_percent,11.1);
 assert.equal(byId["09"].nonurgent_semiurgent_emergency_step.emergency_as_one_step_percent,31.0);
 assert.equal(byId["10"].nonurgent_semiurgent_emergency_step.emergency_as_one_step_percent,41.5);
 assert.equal(byId["06"].nonurgent_semiurgent_emergency_step.emergency_as_one_step_percent,10.0);
 assert.equal(byId["14"].nonurgent_semiurgent_emergency_step.emergency_as_one_step_percent,7.0);
 for(const x of observed){
  const e=x.nonurgent_semiurgent_emergency_step;
  assert.ok(e.emergency_as_one_step_percent>=0 && e.emergency_as_one_step_percent<=100);
  assert.equal(e.source_id,"ISQ_PANORAMA_2026_TABLEAU_8_3");
  assert.match(e.denominator,/dernier besoin seulement/);
  assert.match(e.count_type,/plusieurs démarches possibles/);
 }
 assert.match(byId["14"].nonurgent_semiurgent_emergency_step.quality_flag,/IMPRECIS/);
});

test("tous les coûts, effectifs, intervalles, pilotes et audits externes demeurent indisponibles",()=>{
 for(const x of data.regions){
  assert.equal(x.confidence_interval,null);
  assert.equal(x.sample_size,null);
  assert.equal(x.cost_public_per_episode,null);
  assert.equal(x.cost_private_per_episode,null);
  assert.equal(x.health_outcomes,null);
  assert.equal(x.priority_for_pilot,null);
 }
 assert.equal(diagnostic.g0_completed,false);
 assert.equal(diagnostic.authorized_pilot,false);
 const sector=registre.dossiers.find(x=>x.id==="NV-03");
 assert.equal(sector.chiffrage_valide,false);
 assert.ok(Object.values(sector.couts_par_mode).every(x=>x===null));
 assert.equal(sector.territorial_baseline.gate_g0_completed,false);
});

test("l'origine PDF doit être prouvée sans attribuer au XLSX une analyse jamais faite",()=>{
 const pdf=data.primary_sources.filter(x=>x.kind==="official_pdf_table");
 assert.equal(pdf.length,2);
 assert.deepEqual(pdf.map(x=>x.id),["ISQ_PANORAMA_2026_TABLEAU_8_1","ISQ_PANORAMA_2026_TABLEAU_8_3"]);
 assert.ok(pdf.every(x=>x.url.endsWith("panorama-des-regions-du-quebec-2026-sante.pdf")));
 assert.ok(pdf.every(x=>x.original_xlsx_imported===false));
 const xlsx=data.primary_sources.find(x=>x.id==="ISQ_EQUSSSS_2025_TABLEAUX");
 assert.equal(xlsx.no_row_level_values_extracted,true);
 assert.equal(data.pdf_tabular_data.confidence_intervals_imported,false);
 assert.equal(data.pdf_tabular_data.regional_sample_sizes_imported,false);
});

test("page publique : les 16 valeurs sources, 18 régions et avertissements sont lisibles",()=>{
 assert.equal((page.match(/class="nv-code"/g)||[]).length,18);
 assert.ok(page.includes("88,8 %"));
 assert.ok(page.includes("41,5 %"));
 assert.ok(page.includes("31,0 %"));
 assert.ok(page.includes("77,1 %"));
 assert.match(page,/dénominateur/i);
 assert.match(page,/n'a pas.*pu être téléchargé/);
 assert.ok(page.includes("protocole-portrait-regional-sante-g0-v2.md"));
 assert.ok(page.includes("</main>") && page.includes("</html>"));
});
