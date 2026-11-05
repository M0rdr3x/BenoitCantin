/**
 * Projet Nova G0.11 — Refaire l'audit des cellules MSSS sur le fichier original.
 * Fonctionne après acquisition manuelle G0.7/G0.8 et mappage G0.9.
 * Vérifie l'identité SHA-256, les coordonnées et l'effet de l'arrondi.
 * N'écrit AUCUN nombre de salariés dans le programme normatif.
 */
import {readFile,writeFile} from "node:fs/promises";
import {resolve,join} from "node:path";
import {createHash} from "node:crypto";
import {inspectOfficialRhWorkbook,readXlsxValidatedXmlParts}
  from "../assets/g08-rh-workbook-inspector.mjs";
import {inspectG11Evidence,readOriginalA2Cells,compareOriginalA2Cells}
  from "../assets/g11-rh-evidence-core.mjs";

const outputDir=resolve(process.env.G07_ARTIFACT_DIR||"g07-acquisition-output");
const binaryPath=join(outputDir,"rh-rsss-2024-2025-source.xlsx");
const outputPath=join(outputDir,"g11-original-cell-evidence-audit.json");

let report={
 schema:"nova-g11-workflow-execution/v1",
 status:"NOT_VERIFIED",
 file_sha256:null,
 file_size:null,
 source_rows_checked:0,
 original_cells_match:false,
 rounding_gap_explained:false,
 independently_approved:false,
 clinical_fte_validated:false,
 g0_passed:false,pilot_authorized:false
};
try {
 const evidence=JSON.parse(await readFile(
   new URL("../data/preuve-binaire-rh-msss-g0-11-2024-2025.json",import.meta.url),"utf8"));
 const provisional=JSON.parse(await readFile(
   new URL("../data/portrait-rh-msss-g0-10-2024-2025.json",import.meta.url),"utf8"));
 const contract=inspectG11Evidence(evidence,provisional);
 if(!contract.ok)throw new Error("G11_EVIDENCE_CONTRACT_INVALID:"+contract.errors.join(","));
 const buf=await readFile(binaryPath);
 const digest=createHash("sha256").update(buf).digest("hex");
 if(digest!==evidence.source.original_sha256||buf.length!==evidence.source.original_byte_count)
  throw new Error("G11_ORIGINAL_SHA256_OR_SIZE_CHANGED");
 const workbook=inspectOfficialRhWorkbook(buf);
 if(workbook.worksheet_count!==7||
    !workbook.sheets.some(s=>s.name==="Feuille A - 2"&&
      s.xml_path==="xl/worksheets/sheet4.xml"))
  throw new Error("G11_SHEET_IDENTITY_CHANGED");
 const p=readXlsxValidatedXmlParts(buf,["xl/worksheets/sheet4.xml","xl/sharedStrings.xml"]);
 const cells=readOriginalA2Cells(p["xl/worksheets/sheet4.xml"],p["xl/sharedStrings.xml"]);
 const validation=compareOriginalA2Cells(cells,evidence);
 if(!validation.ok)throw new Error("G11_SOURCE_CELL_MISMATCH:"+validation.errors.join(","));
 report={...report,status:"ORIGINAL_CELLS_MATCH_REVIEW_PENDING",
  file_sha256:digest,file_size:buf.length,
  source_rows_checked:validation.original_rows_checked,
  original_cells_match:true,rounding_gap_explained:true,
  reported_people_2025:contract.persons_2025,
  reported_etc_rounded_2024_2025:contract.rounded_total,
  displayed_row_rounding_gap:2,
  statement:"Intégrité et cellules du XLSX conformes à la copie de référence; aucune capacité clinique ni décision approuvée."};
 console.log("G0.11: SHA-256, 19 lignes de la Feuille A - 2, total 344056 et arrondi ETC vérifiés.");
} catch(e) {
 report.error_code=String(e instanceof Error?e.message:e).slice(0,200);
 process.exitCode=1;
 console.error("G0.11 non vérifié : "+report.error_code);
}
await writeFile(outputPath,JSON.stringify(report,null,2)+"\n");
console.log("Rapport G0.11 : "+outputPath);
