/**
 * Projet Nova — G0.11 : contrôler les cellules originales MSSS 2024–2025.
 * Un SHA-256 de la copie n'est pas une signature gouvernementale.
 */
export const G11_EXPECTED_HASH="8d65573b2f0bf0a935a58c75ba1b4b76050a08b902760f7a03b3cae0cdb86219";
export const G11_EXPECTED_SIZE=139566;
export const G11_ETC_TOLERANCE=1e-8;
const isobj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const uint=x=>Number.isSafeInteger(x)&&x>=0;
export function inspectG11Evidence(e,prior){
 const errors=[];
 if(!isobj(e)||e.schema!=="nova-rh-g0-11-official-xlsx-cell-verification/v1"||
    !isobj(e.source)||!isobj(e.worksheet)||!isobj(e.totals)||!Array.isArray(e.worksheet.rows))
   return {ok:false,errors:["SCHEMA_INVALID"],g0_passed:false};
 const s=e.source,t=e.totals,rows=e.worksheet.rows;
 if(s.original_sha256!==G11_EXPECTED_HASH||s.original_byte_count!==G11_EXPECTED_SIZE||
    s.zip_crc_checked!==true||s.workbook_sheet_count!==7||s.response_status!==200||
    s.original_bytes_archived_in_repo!==false||s.source_signed_by_government!==false)
   errors.push("SOURCE_PROVENANCE_INVALID");
 if(e.worksheet.name!=="Feuille A - 2"||e.worksheet.part!=="xl/worksheets/sheet4.xml"||
    e.worksheet.exact_source_cells_verified!==true||rows.length!==19)
   errors.push("SOURCE_SHEET_INVALID");
 const lookup=new Map((prior?.regions??[]).map(x=>[x.rss_id,x]));
 let people25=0,people24=0,rawEtc=0,roundedEtc=0;
 rows.forEach((r,i)=>{
  const id=String(i).padStart(2,"0");
  if(!isobj(r)||r.code!==id||!r.original_label?.startsWith(id+" - ")||
     r.source_cell_persons_2025!=="B"+(5+i)||
     r.source_cell_persons_2024!==(i===0?null:"C"+(5+i))||
     r.source_cell_paid_etc_2024_2025!=="B"+(51+i))
     {errors.push("ROW_CELLS_INVALID:"+id);return;}
  const raw=Number(r.paid_etc_excel_raw);
  if(!uint(r.persons_2025)||!(i===0?r.persons_2024===null:uint(r.persons_2024))||
     typeof r.paid_etc_excel_raw!=="string"||!/^\d+(\.\d+)?$/.test(r.paid_etc_excel_raw)||
     !Number.isFinite(raw)||raw<0||!uint(r.paid_etc_displayed_integer)||
     Math.round(raw)!==r.paid_etc_displayed_integer||
     Math.abs(raw-Number(r.paid_etc_4dp))>0.000051)
     {errors.push("ROW_VALUES_INVALID:"+id);return;}
  people25+=r.persons_2025;people24+=r.persons_2024??0;
  rawEtc+=raw;roundedEtc+=r.paid_etc_displayed_integer;
  if(i===0){
   if(r.persons_2025!==prior?.separate_hq?.persons_2025||
      r.paid_etc_displayed_integer!==prior?.separate_hq?.etc_2024_2025)
     errors.push("HQ_PREVIOUS_MISMATCH");
  }else{
   const q=lookup.get(id);
   if(!q||q.persons_2025!==r.persons_2025||
      q.persons_2024!==r.persons_2024||
      q.etc_2024_2025!==r.paid_etc_displayed_integer)
    errors.push("RSS_PREVIOUS_MISMATCH:"+id);
  }
 });
 const rawTotal=Number(t.etc_2024_2025_raw);
 if(t.people_2025_cell!=="B24"||t.people_2024_cell!=="C24"||
    Number(t.people_2025_raw)!==people25||people25!==344056||
    Number(t.people_2024_raw)!==people24||people24!==336730||
    t.people_2025_rss18!==343252||t.people_2025_headquarters!==804)
   errors.push("PERSON_RECONCILIATION_INVALID");
 if(t.etc_2024_2025_cell!=="B70"||!Number.isFinite(rawTotal)||
    Math.abs(rawEtc-rawTotal)>G11_ETC_TOLERANCE||
    roundedEtc!==283738||Math.round(rawTotal)!==283740||
    t.etc_sum_19_individually_rounded!==roundedEtc||
    t.etc_rounded_total!==283740||t.etc_rounding_difference!==2||
    t.etc_raw_sum_equals_source_within_1e_8!==true||
    e.arithmetic?.rounding_explains_display_discrepancy!==true)
   errors.push("ETC_ROUNDING_NOT_CONFIRMED");
 if(e.decision?.binary_externally_retrieved!==true||
    e.decision?.cell_level_arithmetic_checked!==true||
    e.decision?.independent_institutional_review!==false||
    e.decision?.personnel_clinical_availability_certified!==false||
    e.decision?.g0_passed!==false||e.decision?.pilot_authorized!==false||
    e.decision?.savings_certified!==false)
   errors.push("INAPPROPRIATE_DECISION_CLAIMS");
 return {ok:errors.length===0,errors:[...new Set(errors)],
  rows_checked:rows.length,persons_2025:people25,persons_2024:people24,
  raw_etc_sum:rawEtc,raw_etc_total:rawTotal,rounded_line_sum:roundedEtc,
  rounded_total:Math.round(rawTotal),rounding_explained:errors.length===0,
  institutional_approval:false,clinical_fte_certified:false,
  g0_passed:false,pilot_authorized:false};
}
function entity(s){
 return s.replace(/&(amp|lt|gt|quot|apos|#\d+|#x[0-9a-f]+);/gi,(v,k)=>{
  if(k[0]==="#"){
    const n=k[1]?.toLowerCase()==="x"?parseInt(k.slice(2),16):parseInt(k.slice(1),10);
    return n>=0&&n<=1114111?String.fromCodePoint(n):v;
  }
  return {amp:"&",lt:"<",gt:">",quot:'"',apos:"'"}[k]??v;
 });
}
function attribute(tag,name){
 if(name!=="r"&&name!=="t")throw new Error("ATTRIBUTE_NOT_ALLOWED");
 const p=new RegExp("(?:^|\\s)"+name+"\\s*=\\s*([\\\"'])(.*?)\\1");
 const m=tag.match(p);return m?entity(m[2]):null;
}
export function readOriginalA2Cells(sheetXml,sharedXml){
 if(typeof sheetXml!=="string"||typeof sharedXml!=="string"||
    /<!DOCTYPE|<!ENTITY/i.test(sheetXml+sharedXml))throw new Error("UNSAFE_XML");
 const shared=[];
 for(const si of sharedXml.matchAll(/<si(?:\s[^>]*)?>([\s\S]*?)<\/si>/g)){
  shared.push([...si[1].matchAll(/<t(?:\s[^>]*)?>([\s\S]*?)<\/t>/g)]
    .map(m=>entity(m[1])).join(""));
 }
 if(!shared.length)throw new Error("EMPTY_SHARED_STRINGS");
 const cells={};
 for(const c of sheetXml.matchAll(/<c\b([^>]*)>([\s\S]*?)<\/c>/g)){
  const ref=attribute(c[1],"r");if(!ref||!(/^[A-Z]{1,3}[1-9]\d*$/.test(ref)))continue;
  const v=c[2].match(/<v>([\s\S]*?)<\/v>/);
  if(!v)continue;
  const raw=entity(v[1]);
  if(attribute(c[1],"t")==="s"){
   const idx=Number(raw);
   if(!Number.isSafeInteger(idx)||idx<0||idx>=shared.length)throw new Error("BAD_STRING_INDEX");
   cells[ref]=shared[idx];
  }else cells[ref]=raw;
 }
 return cells;
}
export function compareOriginalA2Cells(cells,e){
 const errors=[],rows=e?.worksheet?.rows??[],t=e?.totals;
 if(!isobj(cells)||rows.length!==19)return {ok:false,errors:["CELL_SET_INVALID"]};
 for(const r of rows){
  if(cells["A"+(5+Number(r.code))]!==r.original_label)errors.push("LABEL:"+r.code);
  if(Number(cells[r.source_cell_persons_2025])!==r.persons_2025)errors.push("PERSONS:"+r.code);
  if(r.source_cell_persons_2024&&Number(cells[r.source_cell_persons_2024])!==r.persons_2024)
   errors.push("PRIOR_PERSONS:"+r.code);
  if(cells[r.source_cell_paid_etc_2024_2025]!==r.paid_etc_excel_raw)
   errors.push("ETC:"+r.code);
 }
 if(Number(cells.B24)!==Number(t?.people_2025_raw)||
    Number(cells.C24)!==Number(t?.people_2024_raw)||
    cells.B70!==t?.etc_2024_2025_raw)errors.push("TOTAL_CELLS");
 return {ok:errors.length===0,errors,
  original_rows_checked:rows.length,publication_authorized:false,
  clinical_fte_certified:false,g0_passed:false,pilot_authorized:false};
}
