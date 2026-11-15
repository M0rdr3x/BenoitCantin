import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {
 G11_EXPECTED_HASH,G11_EXPECTED_SIZE,
 inspectG11Evidence,readOriginalA2Cells,compareOriginalA2Cells
} from "../assets/g11-rh-evidence-core.mjs";

const e=JSON.parse(await readFile(new URL(
 "../data/preuve-binaire-rh-msss-g0-11-2024-2025.json",import.meta.url),"utf8"));
const old=JSON.parse(await readFile(new URL(
 "../data/portrait-rh-msss-g0-10-2024-2025.json",import.meta.url),"utf8"));
const clone=x=>structuredClone(x);
const makeCells=()=>{
 const c={B24:e.totals.people_2025_raw,C24:e.totals.people_2024_raw,
   B70:e.totals.etc_2024_2025_raw};
 for(const r of e.worksheet.rows){
  c["A"+(5+Number(r.code))]=r.original_label;
  c[r.source_cell_persons_2025]=String(r.persons_2025);
  if(r.source_cell_persons_2024)c[r.source_cell_persons_2024]=String(r.persons_2024);
  c[r.source_cell_paid_etc_2024_2025]=r.paid_etc_excel_raw;
 }
 return c;
};
test("provenance binaire : empreinte, taille, sept feuilles et CRC",()=>{
 assert.equal(e.source.original_sha256,G11_EXPECTED_HASH);
 assert.equal(e.source.original_byte_count,G11_EXPECTED_SIZE);
 assert.equal(e.source.zip_crc_checked,true);
 assert.equal(e.source.workbook_sheet_count,7);
 assert.equal(e.source.source_signed_by_government,false);
});
test("19 lignes source : 18 régions et siège Santé Québec distinct",()=>{
 const v=inspectG11Evidence(e,old);
 assert.equal(v.ok,true);assert.equal(v.rows_checked,19);
 assert.equal(e.worksheet.rows[0].code,"00");
 assert.equal(e.worksheet.rows[18].code,"18");
});
test("personnes 2025 et 2024 réconciliées sur cellules B24 et C24",()=>{
 const v=inspectG11Evidence(e,old);
 assert.equal(v.persons_2025,344056);
 assert.equal(v.persons_2024,336730);
});
test("l'écart apparent de deux ETC est uniquement un effet d'arrondi",()=>{
 const v=inspectG11Evidence(e,old);
 assert.equal(v.ok,true);
 assert.equal(v.rounded_line_sum,283738);
 assert.equal(v.rounded_total,283740);
 assert.ok(Math.abs(v.raw_etc_sum-v.raw_etc_total)<1e-8);
 assert.equal(v.rounding_explained,true);
});
test("contrôle sans faux ETP cliniques ni autorisation de pilote",()=>{
 const v=inspectG11Evidence(e,old);
 assert.equal(v.clinical_fte_certified,false);
 assert.equal(v.g0_passed,false);
 assert.equal(v.pilot_authorized,false);
 assert.equal(e.source.original_bytes_archived_in_repo,false);
});
test("modifier un effectif de RSS sans nouvelle preuve bloque le contrôle",()=>{
 const d=clone(e);d.worksheet.rows[4].persons_2025+=1;
 assert.equal(inspectG11Evidence(d,old).ok,false);
});
test("modifier l'ETC brut ou la coordonnée d'une cellule bloque le contrôle",()=>{
 const a=clone(e);a.worksheet.rows[8].paid_etc_excel_raw="20000.0";
 const b=clone(e);b.worksheet.rows[8].source_cell_paid_etc_2024_2025="B99";
 assert.equal(inspectG11Evidence(a,old).ok,false);
 assert.equal(inspectG11Evidence(b,old).ok,false);
});
test("empreinte falsifiée et attestation gouvernementale inventée sont refusées",()=>{
 const a=clone(e);a.source.original_sha256="b".repeat(64);
 const b=clone(e);b.source.source_signed_by_government=true;
 assert.equal(inspectG11Evidence(a,old).ok,false);
 assert.equal(inspectG11Evidence(b,old).ok,false);
});
test("aucune déclaration G0 franchie ou revue institutionnelle accomplie",()=>{
 const a=clone(e);a.decision.g0_passed=true;
 const b=clone(e);b.decision.independent_institutional_review=true;
 assert.equal(inspectG11Evidence(a,old).ok,false);
 assert.equal(inspectG11Evidence(b,old).ok,false);
});
test("les cellules de la preuve peuvent être rapprochées exactement",()=>{
 const v=compareOriginalA2Cells(makeCells(),e);
 assert.equal(v.ok,true);
 assert.equal(v.original_rows_checked,19);
 assert.equal(v.publication_authorized,false);
});
test("une cellule originale modifiée est détectée",()=>{
 const c=makeCells();c.B70="283741";
 assert.equal(compareOriginalA2Cells(c,e).ok,false);
});
test("le parseur XML lit chaînes partagées, entités et valeurs numériques",()=>{
 const shared='<sst><si><t>00 - Santé Qu&#233;bec</t></si></sst>';
 const worksheet='<worksheet><sheetData><row r="5"><c r="A5" t="s"><v>0</v></c>'+
  '<c r="B5" t="n"><v>804</v></c></row></sheetData></worksheet>';
 const cells=readOriginalA2Cells(worksheet,shared);
 assert.equal(cells.A5,"00 - Santé Québec");
 assert.equal(cells.B5,"804");
});
test("une entité XML est refusée",()=>{
 assert.throws(()=>readOriginalA2Cells('<!DOCTYPE foo><worksheet/>','<sst/>'),/UNSAFE_XML/);
});
test("mauvaise valeur de chaîne partagée est rejetée",()=>{
 assert.throws(()=>readOriginalA2Cells(
 '<worksheet><c r="A5" t="s"><v>999</v></c></worksheet>',
 '<sst><si><t>x</t></si></sst>'),/BAD_STRING_INDEX/);
});

test("cellules vides autofermées ne masquent pas le premier RSS suivant",()=>{
 const shared='<sst><si><t>00 - Santé Québec</t></si>'+
   '<si><t>01 - Bas-Saint-Laurent</t></si></sst>';
 const xml='<worksheet><sheetData>'+
   '<row r="5"><c r="A5" t="s"><v>0</v></c><c r="B5"><v>804</v></c>'+
   '<c r="C5" s="53"/><c r="D5" s="53"/></row>'+
   '<row r="6"><c r="A6" t="s"><v>1</v></c><c r="B6"><v>9057</v></c></row>'+
   '</sheetData></worksheet>';
 const cells=readOriginalA2Cells(xml,shared);
 assert.equal(cells.A5,"00 - Santé Québec");
 assert.equal(cells.A6,"01 - Bas-Saint-Laurent");
 assert.equal(cells.B6,"9057");
});
