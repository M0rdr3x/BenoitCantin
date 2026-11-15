import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {createReviewPackage,inspectOfficialAcquisition,inspectMappedRows,inspectG09Registry} from "../assets/g09-rh-reconciliation-core.mjs";

const registry=JSON.parse(await readFile(new URL("../data/registre-rapprochement-rh-g0-9.json",import.meta.url),"utf8"));
const hash="a".repeat(64);
const acquired={
 status:"ACQUIRED_UNINTERPRETED",source_id:"MSSS_RH_2024_2025",size_bytes:136000,sha256:hash,
 etp_clinical_values_imported:0,regional_workforce_values_imported:0,
 pilot_authorized:false,g0_formally_passed:false,
 xlsx_metadata:{audit_level:"L2_STRUCTURE_SEULEMENT",container_valid:true,cell_values_read:false,
 worksheet_count:1,sheets:[{name:"TEST",xml_path:"xl/worksheets/sheet1.xml",dimension:"A1:E50",hidden:false}]}
};
const pkg=createReviewPackage(acquired);
const row={sheet_name:"TEST",cell_ref:"D24",source_sha256:hash,row_role:"DETAIL",
 rss_id:"01",source_geography:"RSS",unit:"PERSONNES",measure_id:"NOMBRE_TEST",
 profession_group:"GROUPE_TEST",source_period:"2024-2025",population_scope:"FICTIVE",
 value:12,zero_explicitly_observed:false,human_mapping_checked:true,
 primary_document_checked:true,reviewer:"TEST",mixed_population_excluded:true,
 is_aggregate_of_other_selected_rows:false};

test("registre non chiffré: 18 RSS et 13 contrôles",()=>{
 const result=inspectG09Registry(registry);
 assert.equal(result.regions,18);assert.equal(result.controls,13);
 assert.equal(result.unverified_numbers_present,false);
 assert.equal(result.pilot_authorized,false);
});
test("source absente empêche tout mappage",()=>{
 const x=createReviewPackage({status:"DOWNLOAD_BLOCKED"});
 assert.equal(x.sheets.length,0);assert.equal(x.values_interpreted,0);
});
test("le package L2 ne contient aucune cellule RH",()=>{
 assert.equal(inspectOfficialAcquisition(acquired).ok,true);
 assert.equal(pkg.sheets.length,1);
 assert.equal(pkg.reviewed_aggregates.length,0);
 assert.equal(pkg.values_interpreted,0);
});
test("aucune valeur, même revue, n'autorise un pilote",()=>{
 const r=inspectMappedRows([row],pkg);
 assert.equal(r.ok,true);assert.equal(r.ready_for_release,false);
 assert.equal(r.g0_passed,false);assert.equal(r.pilot_authorized,false);
});
test("deux cellules identiques sont rejetées",()=>{
 const r=inspectMappedRows([row,row],pkg);
 assert.equal(r.ok,false);assert.ok(r.errors.some(x=>x.includes("DUPLICATE_CELL_REF")));
});
test("les sous-totaux ne sont pas ajoutés aux détails",()=>{
 const r=inspectMappedRows([row,{...row,cell_ref:"D48",row_role:"SUBTOTAL",value:200}],pkg);
 assert.equal(r.ok,true);assert.equal(r.detail_candidates.length,1);
});
test("un zéro non vérifié est refusé",()=>{
 assert.equal(inspectMappedRows([{...row,value:0}],pkg).ok,false);
 assert.equal(inspectMappedRows([{...row,value:0,zero_explicitly_observed:true}],pkg).ok,true);
});
test("une cellule supprimée ne peut contenir une valeur",()=>{
 const r=inspectMappedRows([{...row,row_role:"SUPPRESSED",value:0}],pkg);
 assert.equal(r.ok,false);
});
test("un faux code RSS et une unité non reconnue sont rejetés",()=>{
 const r=inspectMappedRows([{...row,rss_id:"19",unit:"AUTRE"}],pkg);
 assert.equal(r.ok,false);
});
test("aucun chiffre sans revue humaine",()=>{
 const r=inspectMappedRows([{...row,human_mapping_checked:false}],pkg);
 assert.equal(r.ok,false);
});
