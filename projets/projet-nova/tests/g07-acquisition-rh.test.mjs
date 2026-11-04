import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {
  OFFICIAL_RH_XLSX_URL, RH_SOURCE_ID,
  inspectXlsxInventory,readXlsxZipDirectory,
  inspectAcquisitionManifest,summarizeG07
} from "../assets/g07-rh-acquisition-core.mjs";

const baseline=JSON.parse(await readFile(
  new URL("../data/registre-acquisition-rh-g0-7.json",import.meta.url),"utf8"));
const previous=JSON.parse(await readFile(
  new URL("../data/registre-rh-regional-g0-6-sante.json",import.meta.url),"utf8"));

// Fixture ZIP: les en-têtes et l'annuaire sont synthétiques, sans XML ni données RH.
// Teste uniquement le détecteur de structure, pas la lecture d'un vrai classeur.
function fakeZip(names) {
  const local=[],central=[];let start=0;
  for(const row of names){
    const name=typeof row==="string"?row:row.name;
    const encrypted=typeof row==="string"?false:!!row.encrypted;
    const b=Buffer.from(name,"utf8");
    const l=Buffer.alloc(30+b.length);l.writeUInt32LE(0x04034b50,0);
    l.writeUInt16LE(b.length,26);b.copy(l,30);local.push(l);
    const c=Buffer.alloc(46+b.length);c.writeUInt32LE(0x02014b50,0);
    c.writeUInt16LE(encrypted?1:0,8);
    c.writeUInt16LE(b.length,28);c.writeUInt32LE(start,42);b.copy(c,46);
    central.push(c);start+=l.length;
  }
  const centralBytes=Buffer.concat(central);
  const end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50,0);
  end.writeUInt16LE(names.length,8);end.writeUInt16LE(names.length,10);
  end.writeUInt32LE(centralBytes.length,12);end.writeUInt32LE(start,16);
  return Buffer.concat([...local,centralBytes,end]);
}

const officialEntries=[
  "[Content_Types].xml","xl/workbook.xml","xl/worksheets/sheet1.xml"
];

test("URL source et ID exactement définis, sans hôte tiers arbitraire",()=>{
 assert.equal(baseline.source_id,RH_SOURCE_ID);
 assert.equal(baseline.official_url,OFFICIAL_RH_XLSX_URL);
 assert.ok(OFFICIAL_RH_XLSX_URL.startsWith("https://cdn-contenu.quebec.ca/"));
});

test("source repérée mais téléchargement non réussi : aucun SHA ou ETP",()=>{
 assert.equal(baseline.status,"DOWNLOAD_BLOCKED");
 assert.equal(baseline.sha256,null);assert.equal(baseline.size_bytes,null);
 assert.equal(baseline.retrieved_at_utc,null);
 assert.equal(baseline.xlsx_inventory,null);
 assert.equal(baseline.etp_clinical_values_imported,0);
 assert.equal(baseline.regional_workforce_values_imported,0);
 assert.equal(baseline.g0_formally_passed,false);
 assert.equal(baseline.pilot_authorized,false);
 assert.equal(inspectAcquisitionManifest(baseline).ok,true);
});

test("inventaire ZIP synthétique : format de conteneur XLSX détectable",()=>{
 const report=readXlsxZipDirectory(fakeZip(officialEntries));
 assert.equal(report.ok,true);
 assert.equal(report.worksheet_count,1);
 assert.deepEqual(report.worksheets,["xl/worksheets/sheet1.xml"]);
});

test("aucun XLSX sans Workbook XML et feuille ne doit être accepté",()=>{
 assert.equal(inspectXlsxInventory([
   {name:"[Content_Types].xml"},{name:"xl/workbook.xml"},{name:"xl/worksheets/sheet1.xml"}
 ]).ok,true);
 assert.equal(inspectXlsxInventory([{name:"[Content_Types].xml"},{name:"xl/workbook.xml"}]).ok,false);
 assert.throws(()=>readXlsxZipDirectory(fakeZip([
   "[Content_Types].xml","xl/worksheets/sheet1.xml","_rels/.rels"
 ])),/WORKBOOK_MISSING/);
});

test("doublons, chemins suspects et entrées chiffrées sont bloqués",()=>{
 assert.throws(()=>readXlsxZipDirectory(fakeZip([
   ...officialEntries,"xl/workbook.xml"
 ])),/DUPLICATE_ARCHIVE_ENTRY/);
 assert.throws(()=>readXlsxZipDirectory(fakeZip([
   ...officialEntries,"../untrusted.xml"
 ])),/ENTRY_NAME_INVALID/);
 assert.throws(()=>readXlsxZipDirectory(fakeZip([
   ...officialEntries,{name:"xl/worksheets/sheet2.xml",encrypted:true}
 ])),/ENCRYPTED_ENTRY/);
});

test("archive tronquée ne devient jamais une preuve de téléchargement",()=>{
 const b=fakeZip(officialEntries);
 assert.throws(()=>readXlsxZipDirectory(b.subarray(0,b.length-8)),/ZIP_END_CENTRAL_DIRECTORY/);
});

test("un manifeste acquis doit prouver l'empreinte, le nombre d'octets et la date",()=>{
 const m={
  ...baseline,status:"ACQUIRED_UNINTERPRETED",
  retrieved_at_utc:"2026-11-04T22:00:00.000Z",
  sha256:"a".repeat(64),size_bytes:123456,
  xlsx_inventory:{ok:true,worksheet_count:1,worksheets:["xl/worksheets/sheet1.xml"],failures:[]},
  xlsx_metadata:{audit_level:"L2_STRUCTURE_SEULEMENT",container_valid:true,
    worksheet_count:1,cell_values_read:false,clinic_fte_verified:0,
    regional_worker_counts_verified:0,decision:"NON_FRANCHI"}
 };
 assert.equal(inspectAcquisitionManifest(m).ok,true);
 assert.equal(inspectAcquisitionManifest({...m,sha256:null}).ok,false);
 assert.equal(inspectAcquisitionManifest({...m,size_bytes:999999999}).ok,false);
 assert.equal(inspectAcquisitionManifest({...m,source_id:"IMPOSTEUR"}).ok,false);
 assert.equal(inspectAcquisitionManifest({...m,xlsx_metadata:null}).ok,false);
 assert.equal(inspectAcquisitionManifest({...m,xlsx_metadata:{...m.xlsx_metadata,cell_values_read:true}}).ok,false);
});

test("aucune validation clinique, budget, ETP ni autorisation déduite de l'acquisition",()=>{
 const b={...baseline,pilot_authorized:true,financial_savings_certified:true};
 assert.equal(inspectAcquisitionManifest(b).ok,false);
 assert.equal(inspectAcquisitionManifest({...baseline,regional_workforce_values_imported:1}).ok,false);
 assert.equal(inspectAcquisitionManifest({...baseline,etp_clinical_values_imported:1}).ok,false);
 assert.equal(inspectAcquisitionManifest({...baseline,sha256:"a".repeat(64)}).ok,false);
});

test("G0.7 ne convertit pas les taux ISQ en ETP ou coûts par région",()=>{
 const result=summarizeG07(baseline,previous);
 assert.equal(result.regions,18);
 assert.equal(result.regions_without_validated_rh,undefined);
 assert.equal(result.regions_with_official_workforce_values,0);
 assert.equal(result.clinical_etp_certified,0);
 assert.equal(result.g0_formally_passed,false);
 assert.equal(result.pilot_authorized,false);
 assert.equal(result.provenance_status,"DOWNLOAD_BLOCKED");
});

test("la source G0.6 conserve ses 18 RSS et zéro donnée RH inventée",()=>{
 assert.equal(previous.regions.length,18);
 assert.ok(previous.regions.every(x=>x.etp_clinical_first_line===null &&
   x.employment_count===null && x.unit_cost_complete===null));
});
