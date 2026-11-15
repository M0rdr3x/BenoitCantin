import {test} from "node:test";
import assert from "node:assert/strict";
import {deflateRawSync} from "node:zlib";
import {inspectOfficialRhWorkbook} from "../assets/g08-rh-workbook-inspector.mjs";

const bytes=s=>Buffer.from(s,"utf8");
function crc32(buffer){
  let c=0xffffffff;
  for(const b of buffer){c^=b;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}
  return (c^0xffffffff)>>>0;
}
function fixtureWorkbook({name="Effectifs régionaux",dim="A1:F26",external=false,
  macro=false,duplicateSheetName=false,corruptCrc=false,missingRels=false,
  maliciousXml=false,hidden=false}={}){
 const ct=bytes('<?xml version="1.0"?><Types><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/></Types>');
 const wb=bytes('<?xml version="1.0"?><workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+
   '<sheet name="'+name+'" sheetId="1" r:id="rId1"'+(hidden?' state="hidden"':'')+'/>'+
   (duplicateSheetName?'<sheet name="'+name+'" sheetId="2" r:id="rId2"/>':'')+
   '</sheets></workbook>');
 const relationship='<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>';
 const rels=bytes('<?xml version="1.0"?><Relationships>'+relationship+
   (duplicateSheetName?'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>':'')+
   (external?'<Relationship Id="rId99" TargetMode="External" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLink" Target="https://example.invalid/private.xlsx"/>':'')+
   '</Relationships>');
 const cells=maliciousXml?'<!DOCTYPE x [ <!ENTITY boom SYSTEM "file:///etc/passwd"> ]>':'<sheetData><row r="1"><c r="A1"><v>99999999</v></c></row></sheetData>';
 const sh=bytes('<?xml version="1.0"?><worksheet><dimension ref="'+dim+'"/>'+cells+'</worksheet>');
 const entries=[
  ["[Content_Types].xml",ct],
  ["xl/workbook.xml",wb],
  ...(!missingRels?[["xl/_rels/workbook.xml.rels",rels]]:[]),
  ["xl/worksheets/sheet1.xml",sh],
  ...(duplicateSheetName?[["xl/worksheets/sheet2.xml",sh]]:[]),
  ...(macro?[["xl/vbaProject.bin",bytes("DANGEROUS")]]:[])
 ];
 const local=[],central=[];let pos=0;
 for(const [n,payload] of entries){
  const filename=bytes(n), compressed=deflateRawSync(payload),crc=crc32(payload);
  const lh=Buffer.alloc(30+filename.length);
  lh.writeUInt32LE(0x04034b50,0);lh.writeUInt16LE(20,4);
  lh.writeUInt16LE(8,8);lh.writeUInt32LE(crc,14);lh.writeUInt32LE(compressed.length,18);
  lh.writeUInt32LE(payload.length,22);lh.writeUInt16LE(filename.length,26);
  filename.copy(lh,30);
  const cd=Buffer.alloc(46+filename.length);
  cd.writeUInt32LE(0x02014b50,0);cd.writeUInt16LE(20,4);cd.writeUInt16LE(20,6);
  cd.writeUInt16LE(8,10);
  cd.writeUInt32LE(corruptCrc&&n==="xl/workbook.xml"?crc^1:crc,16);
  cd.writeUInt32LE(compressed.length,20);cd.writeUInt32LE(payload.length,24);
  cd.writeUInt16LE(filename.length,28);cd.writeUInt32LE(pos,42);
  filename.copy(cd,46);
  local.push(lh,compressed);central.push(cd);pos+=lh.length+compressed.length;
 }
 const cdbytes=Buffer.concat(central),end=Buffer.alloc(22);
 end.writeUInt32LE(0x06054b50,0);end.writeUInt16LE(entries.length,8);
 end.writeUInt16LE(entries.length,10);end.writeUInt32LE(cdbytes.length,12);
 end.writeUInt32LE(pos,16);
 return Buffer.concat([...local,cdbytes,end]);
}

test("un classeur synthétique cohérent produit les seuls noms et dimensions",()=>{
 const x=inspectOfficialRhWorkbook(fixtureWorkbook());
 assert.equal(x.audit_level,"L2_STRUCTURE_SEULEMENT");
 assert.equal(x.worksheet_count,1);
 assert.equal(x.sheets[0].name,"Effectifs régionaux");
 assert.equal(x.sheets[0].dimension,"A1:F26");
 assert.equal(x.cell_values_read,false);
 assert.equal(x.clinic_fte_verified,0);
 assert.equal(x.decision,"NON_FRANCHI");
 assert.ok(!JSON.stringify(x).includes("99999999"));
});
test("feuille masquée : état conservé, aucune lecture de valeurs",()=>{
 const x=inspectOfficialRhWorkbook(fixtureWorkbook({hidden:true}));
 assert.equal(x.sheets[0].hidden,true);
 assert.equal(x.cell_values_read,false);
});
test("un classeur sans relationships est refusé",()=>{
 assert.throws(()=>inspectOfficialRhWorkbook(fixtureWorkbook({missingRels:true})),/REQUIRED_PACKAGE_PART_MISSING/);
});
test("un classeur avec macros est bloqué",()=>{
 assert.throws(()=>inspectOfficialRhWorkbook(fixtureWorkbook({macro:true})),/MACRO_EXTERNAL_OR_EMBEDDED_CONTENT/);
});
test("une relation de type External est interdite",()=>{
 assert.throws(()=>inspectOfficialRhWorkbook(fixtureWorkbook({external:true})),/EXTERNAL_WORKBOOK_RELATIONSHIP/);
});
test("un classeur contenant une entité XML externe est rejeté",()=>{
 assert.throws(()=>inspectOfficialRhWorkbook(fixtureWorkbook({maliciousXml:true})),/UNSAFE_XML_ENTITY/);
});
test("un CRC incorrect bloque la métadonnée",()=>{
 assert.throws(()=>inspectOfficialRhWorkbook(fixtureWorkbook({corruptCrc:true})),/CRC_MISMATCH/);
});
test("une dimension non Excel est rejetée",()=>{
 assert.throws(()=>inspectOfficialRhWorkbook(fixtureWorkbook({dim:"../../x"})),/SHEET_DIMENSION_INVALID/);
});
test("deux feuilles au nom identique sont refusées",()=>{
 assert.throws(()=>inspectOfficialRhWorkbook(fixtureWorkbook({duplicateSheetName:true})),/SHEET_NAME_DUPLICATED/);
});
test("un ZIP tronqué ne passe pas l'audit",()=>{
 const b=fixtureWorkbook();assert.throws(()=>inspectOfficialRhWorkbook(b.subarray(0,b.length-7)));
});
test("les cellules fictives n'apparaissent jamais dans la sortie",()=>{
 const report=inspectOfficialRhWorkbook(fixtureWorkbook());
 assert.ok(report.sheets.every(x=>!Object.hasOwn(x,"cells")&&!Object.hasOwn(x,"values")));
 assert.ok(!JSON.stringify(report).includes("99999999"));
 assert.equal(report.regional_worker_counts_verified,0);
 assert.equal(report.cost_per_episode_verified,0);
});
