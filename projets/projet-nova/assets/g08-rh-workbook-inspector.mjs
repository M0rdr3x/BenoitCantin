/**
 * Projet Nova — G0.8. Inspection prudente des métadonnées XLSX officielles.
 * Les cellules RH ne sont PAS extraites. Ni ETP, ni coûts, ni pilote calculés.
 * Node 22, sans dépendance tierce.
 */
import {inflateRawSync} from "node:zlib";
import {readXlsxZipDirectory,MAX_OFFICIAL_XLSX_BYTES} from "./g07-rh-acquisition-core.mjs";

const MAX_XML_ENTRY_BYTES=12*1024*1024;
const MAX_TOTAL_XML_BYTES=36*1024*1024;
const MAX_SHEETS=100;
const dec=new TextDecoder("utf-8",{fatal:true});

function expect(cond,code){if(!cond)throw new Error(code);}
function hex32(x){return (x>>>0).toString(16).padStart(8,"0");}
function crc32(bytes){
  let crc=0xffffffff;
  for(const b of bytes){crc^=b;for(let i=0;i<8;i++)crc=(crc>>>1) ^ ((crc&1)?0xedb88320:0);}
  return (crc^0xffffffff)>>>0;
}
function xmlText(bytes,label){
  const x=dec.decode(bytes);
  expect(!/<!DOCTYPE|<!ENTITY/i.test(x),"UNSAFE_XML_ENTITY:"+label);
  expect(!/\u0000/.test(x),"INVALID_XML_NULL:"+label);
  return x;
}
function attrs(raw){
  const out={};
  const re=/([\w:.-]+)\s*=\s*(["'])(.*?)\2/g;
  for(const m of raw.matchAll(re))out[m[1]]=m[3]
    .replaceAll("&quot;",'"').replaceAll("&apos;","'")
    .replaceAll("&lt;","<").replaceAll("&gt;",">").replaceAll("&amp;","&");
  return out;
}
function normalizedTarget(s){
  expect(typeof s==="string"&&s.length>0,"SHEET_TARGET_MISSING");
  const raw=s.replaceAll("\\","/");
  const candidate=raw.startsWith("/")?raw.slice(1):"xl/"+raw;
  const out=[];
  for(const p of candidate.split("/")){
    if(p==="."||p==="")continue;
    if(p===".."){expect(out.length>1,"TARGET_ESCAPE");out.pop();continue;}
    out.push(p);
  }
  const path=out.join("/");
  expect(/^xl\/worksheets\/[^/]+\.xml$/.test(path),"TARGET_NOT_WORKSHEET");
  return path;
}
function directory(bytes) {
  expect(bytes instanceof Uint8Array,"XLSX_BYTES_REQUIRED");
  expect(bytes.length>=22&&bytes.length<=MAX_OFFICIAL_XLSX_BYTES,"FILE_SIZE_INVALID");
  // G0.7 checks duplicate names, path traversal, encryption and ZIP64.
  const preliminary=readXlsxZipDirectory(bytes);
  const dv=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  let end=-1;
  for(let i=bytes.length-22;i>=Math.max(0,bytes.length-22-65535);i--){
    if(dv.getUint32(i,true)===0x06054b50&&i+22+dv.getUint16(i+20,true)===bytes.length){end=i;break;}
  }
  expect(end>=0,"EOCD_MISSING");
  const count=dv.getUint16(end+10,true);
  const offset=dv.getUint32(end+16,true);
  const size=dv.getUint32(end+12,true);
  expect(offset+size<=end,"ZIP_DIRECTORY_BOUNDARY");
  const entries=new Map();let pos=offset;
  for(let i=0;i<count;i++){
    expect(pos+46<=offset+size&&dv.getUint32(pos,true)===0x02014b50,"CENTRAL_ENTRY_INVALID");
    const flags=dv.getUint16(pos+8,true),method=dv.getUint16(pos+10,true);
    const crc=dv.getUint32(pos+16,true),compressed=dv.getUint32(pos+20,true);
    const uncompressed=dv.getUint32(pos+24,true);
    const nameLen=dv.getUint16(pos+28,true),extra=dv.getUint16(pos+30,true),comment=dv.getUint16(pos+32,true);
    const local=dv.getUint32(pos+42,true);
    expect(pos+46+nameLen+extra+comment<=offset+size,"CENTRAL_ENTRY_TRUNCATED");
    const name=dec.decode(bytes.subarray(pos+46,pos+46+nameLen));
    expect(!entries.has(name),"DUPLICATE_ENTRY");
    expect(flags&1 ? false : true,"ZIP_ENCRYPTED");
    expect(method===0||method===8,"ZIP_COMPRESSION_UNSUPPORTED");
    expect(uncompressed<=MAX_XML_ENTRY_BYTES||!name.endsWith(".xml"),"XML_SIZE_LIMIT");
    expect(local+30<=offset&&dv.getUint32(local,true)===0x04034b50,"LOCAL_HEADER_MISSING");
    const localNameLen=dv.getUint16(local+26,true),localExtra=dv.getUint16(local+28,true);
    expect(dv.getUint16(local+8,true)===method,"ZIP_METHOD_MISMATCH");
    const localName=dec.decode(bytes.subarray(local+30,local+30+localNameLen));
    expect(localName===name,"ZIP_LOCAL_CENTRAL_NAME_MISMATCH");
    const dataOffset=local+30+localNameLen+localExtra;
    expect(dataOffset+compressed<=offset,"ZIP_DATA_OUT_OF_BOUNDS");
    entries.set(name,{name,method,crc,compressed,uncompressed,dataOffset});
    pos+=46+nameLen+extra+comment;
  }
  expect(pos===offset+size,"CENTRAL_SIZE_MISMATCH");
  return {entries,preliminary};
}
function decompress(entry,bytes){
  expect(entry.uncompressed<=MAX_XML_ENTRY_BYTES,"XML_TOO_LARGE");
  const input=bytes.subarray(entry.dataOffset,entry.dataOffset+entry.compressed);
  const out=entry.method===0?input:inflateRawSync(input,{maxOutputLength:MAX_XML_ENTRY_BYTES});
  expect(out.length===entry.uncompressed,"DECOMPRESSED_SIZE_MISMATCH:"+entry.name);
  expect(crc32(out)===entry.crc,"CRC_MISMATCH:"+entry.name);
  return out;
}
export function inspectOfficialRhWorkbook(input){
  const bytes=input instanceof Uint8Array?input:new Uint8Array(input);
  const {entries,preliminary}=directory(bytes);
  // Abort if workbook embeds executable/macro packages or remote relationships.
  const names=[...entries.keys()];
  expect(!names.some(x=>/vbaProject\.bin|^xl\/(activeX|embeddings|externalLinks)\//i.test(x)),
    "MACRO_EXTERNAL_OR_EMBEDDED_CONTENT");
  for(const n of ["[Content_Types].xml","xl/workbook.xml","xl/_rels/workbook.xml.rels"])
    expect(entries.has(n),"REQUIRED_PACKAGE_PART_MISSING:"+n);
  let total=0;
  function readXml(path){
    const e=entries.get(path);
    expect(!!e,"SOURCE_XML_MISSING:"+path);
    total+=e.uncompressed;
    expect(total<=MAX_TOTAL_XML_BYTES,"TOTAL_XML_SIZE_LIMIT");
    return xmlText(decompress(e,bytes),path);
  }
  const types=readXml("[Content_Types].xml");
  expect(types.includes("spreadsheetml")||types.includes("sheet.main+xml"),
    "NOT_AN_XLSX_CONTENT_TYPE");
  const book=readXml("xl/workbook.xml");
  const rels=readXml("xl/_rels/workbook.xml.rels");
  expect(/<(?:\w+:)?workbook\b/.test(book),"WORKBOOK_XML_ROOT_MISSING");
  expect(/<(?:\w+:)?Relationships\b/.test(rels),"RELATIONSHIPS_XML_ROOT_MISSING");
  const relationships=new Map();
  for(const m of rels.matchAll(/<(?:\w+:)?Relationship\b([^>]*?)\/>/g)){
    const a=attrs(m[1]);
    if(a.TargetMode==="External")throw new Error("EXTERNAL_WORKBOOK_RELATIONSHIP");
    if(a.Type?.endsWith("/worksheet")){
      expect(a.Id && a.Target,"RELATIONSHIP_INCOMPLETE");
      expect(!relationships.has(a.Id),"RELATIONSHIP_ID_DUPLICATED");
      relationships.set(a.Id,normalizedTarget(a.Target));
    }
  }
  expect(relationships.size>0,"WORKSHEET_RELATIONSHIPS_MISSING");
  const sheets=[];const sheetNames=new Set();const pathsUsed=new Set();
  for(const m of book.matchAll(/<(?:\w+:)?sheet\b([^>]*?)\/>/g)){
    const a=attrs(m[1]);
    const sheetName=a.name,relId=a["r:id"];
    expect(typeof sheetName==="string"&&sheetName.length>0&&sheetName.length<=31,
      "SHEET_NAME_INVALID");
    expect(!sheetNames.has(sheetName.toLowerCase()),"SHEET_NAME_DUPLICATED");
    sheetNames.add(sheetName.toLowerCase());
    const path=relationships.get(relId);
    expect(path&&entries.has(path),"SHEET_RELATIONSHIP_UNRESOLVED:"+sheetName);
    expect(!pathsUsed.has(path),"SHEET_PATH_DUPLICATED");
    pathsUsed.add(path);
    // For first-pass audit, inspect the worksheet dimension but not any cell values.
    const xml=readXml(path);
    const dim=xml.match(/<(?:\w+:)?dimension\b[^>]*ref=(["'])(.*?)\1/);
    const dimension=dim?dim[2]:null;
    if(dimension!==null)expect(/^[A-Z]{1,3}[1-9]\d*(?::[A-Z]{1,3}[1-9]\d*)?$/.test(dimension),
      "SHEET_DIMENSION_INVALID:"+sheetName);
    sheets.push({name:sheetName,xml_path:path,dimension,hidden:a.state==="hidden"||a.state==="veryHidden"});
    expect(sheets.length<=MAX_SHEETS,"TOO_MANY_WORKSHEETS");
  }
  expect(sheets.length>0,"NO_WORKSHEET_MAPPING");
  return {
    audit_level:"L2_STRUCTURE_SEULEMENT",
    container_valid:true,
    worksheet_count:sheets.length,
    listed_worksheet_xml_count:preliminary.worksheet_count,
    sheets,
    cell_values_read:false,
    personal_records_collected:false,
    clinic_fte_verified:0,
    regional_worker_counts_verified:0,
    cost_per_episode_verified:0,
    decision:"NON_FRANCHI",
    warnings:[
      "La dimension de feuille est une métadonnée déclarée, pas le nombre de lignes utiles.",
      "Aucune cellule ni valeur de personnel n'a été extraite ou approuvée.",
      "Les données 2024-2025 ne mesurent pas à elles seules la première ligne en novembre 2026."
    ]
  };
}
