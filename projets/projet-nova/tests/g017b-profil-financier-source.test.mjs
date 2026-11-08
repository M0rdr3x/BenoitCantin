import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const load=async name=>JSON.parse(await readFile(new URL("../data/"+name,import.meta.url),"utf8"));
const [contract,audit,previous]=await Promise.all([
 load("g017b-mamh-municipal-ingestion-contract-2024-2025.json"),
 load("audit-completude-programme-nova-2026-11-05.json"),
 load("g017c-recettes-municipales-2024-et-couts-eau-2023.json")
]);
const profile=contract.profile_financier_crosscheck_2024;
test("la ressource agrégée concerne 2024 et seulement les municipalités locales",()=>{
 assert.equal(profile.resource_id,"5dec077d-4ef9-4e22-99e9-0c4f3a6dd52d");
 assert.equal(profile.source_year,2024);
 assert.equal(profile.edition,"2024-2025");
 assert.match(profile.variable_period_for_this_resource,/2024_NOT_2025/);
 assert.equal(profile.role,"COMPLEMENTARY_MUNICIPAL_LOCAL_PROFILE_NOT_ENTIRE_MUNICIPAL_ORGANIZATIONS");
 assert.equal(profile.source_csv_url,"https://mamh.gouv.qc.ca/fichiersdonneesouvertes/PF-2024-2024-Prov.csv");
});
test("une fiche catalogue n'est pas une donnée financière téléchargée",()=>{
 assert.equal(profile.downloaded_bytes_available,false);
 assert.equal(profile.file_sha256,null);
 assert.equal(profile.csv_rows_inspected,0);
 assert.equal(profile.account_code_mapping_confirmed,false);
 assert.equal(profile.crosscheck_completed,false);
 assert.equal(profile.independent_review_complete,false);
 assert.equal(profile.verified_2024_municipal_revenue_cad,null);
 assert.equal(profile.verified_2024_municipal_expenditure_cad,null);
});
test("on ne remplace jamais un montant inconnu par zéro",()=>{
 assert.notEqual(profile.verified_2024_municipal_revenue_cad,0);
 assert.notEqual(profile.verified_2024_municipal_expenditure_cad,0);
 assert.equal(contract.intended_output.verified_2024_municipal_revenue_cad,null);
 assert.equal(contract.intended_output.verified_2025_municipal_revenue_cad,null);
});
test("statuts des vraies séries 2024 et 2025 inchangés",()=>{
 assert.deepEqual(contract.datasets.map(x=>x.year),[2024,2025]);
 for(const s of contract.datasets){
  assert.equal(s.local_csv_imported,false);
  assert.equal(s.file_sha256,null);
  assert.equal(s.local_rows_loaded,0);
 }
 assert.equal(contract.access_restrictions.local_2024_profile_csv_download_attempted,true);
 assert.equal(contract.access_restrictions.local_2024_profile_download_error,
 "DNS_RESOLUTION_FAILURE_ON_MAMH_GOUV_QC_CA_IN_LOCAL_RUNTIME");
});
test("différence de périmètre avec la statistique 2024 des organismes municipaux",()=>{
 assert.equal(previous.municipal.year,2024);
 assert.equal(previous.municipal.scope,"QUEBEC_CONSOLIDATED_MUNICIPAL_ORGANIZATIONS");
 assert.notEqual(profile.role,previous.municipal.scope);
 assert.equal(profile.crosscheck_completed,false);
});
test("la découverte ne certifie pas le programme et ne modifie pas 47/100",()=>{
 assert.equal(audit.scoring.earned,47);
 assert.equal(contract.score_before,47);
 assert.equal(contract.score_after,47);
 assert.equal(contract.points_remaining,53);
 assert.equal(contract.intended_output.programme_score_increment,0);
 assert.equal(profile.independent_review_complete,false);
});
test("les sources, millésimes et limitations restent explicites",()=>{
 assert.match(profile.resource_page,/^https:\/\/www\.donneesquebec\.ca\//);
 assert.equal(profile.resource_last_updated_metadata,"2026-09-01");
 assert.equal(profile.dataset_catalog_latest_metadata,"2026-11-07");
 assert.equal(profile.license,"CC-BY 4.0");
 assert.ok(profile.limitations.length>=4);
});
