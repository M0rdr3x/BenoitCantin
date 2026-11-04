/**
 * G0.9 — Étape APRÈS le téléchargement manuel officiel G0.7/G0.8.
 * Construit une fiche de mappage à remplir par un analyste; ne lit pas de cellules RH.
 */
import {readFile,writeFile} from "node:fs/promises";
import {resolve,join} from "node:path";
import {createHash} from "node:crypto";
import {createReviewPackage,inspectOfficialAcquisition}
  from "../assets/g09-rh-reconciliation-core.mjs";
import {inspectOfficialRhWorkbook} from "../assets/g08-rh-workbook-inspector.mjs";

const out=resolve(process.env.G07_ARTIFACT_DIR||"g07-acquisition-output");
const auditPath=join(out,"source-audit.json");
const xlsxPath=join(out,"rh-rsss-2024-2025-source.xlsx");
const packagePath=join(out,"g09-review-package.json");

try{
 const audit=JSON.parse(await readFile(auditPath,"utf8"));
 const check=inspectOfficialAcquisition(audit);
 if(!check.ok)throw new Error("G09_REQUIRES_ACQUIRED_L2:"+check.errors.join(","));
 const binary=await readFile(xlsxPath);
 const hash=createHash("sha256").update(binary).digest("hex");
 if(hash!==audit.sha256||binary.length!==audit.size_bytes)
   throw new Error("G09_SOURCE_CHANGED_AFTER_L2");
 const current=inspectOfficialRhWorkbook(binary);
 if(JSON.stringify(current.sheets)!==JSON.stringify(audit.xlsx_metadata.sheets))
   throw new Error("G09_WORKBOOK_MAPPING_CHANGED");
 const pkg=createReviewPackage(audit);
 if(pkg.status!=="METADONNEES_SEULEMENT"||pkg.values_interpreted!==0||
    pkg.reviewed_aggregates.length!==0)
   throw new Error("G09_UNEXPECTED_EXTRACTION");
 await writeFile(packagePath,JSON.stringify(pkg,null,2)+"\n",{flag:"wx"});
 console.log("G0.9: "+pkg.sheets.length+" feuilles répertoriées, aucune valeur RH lue.");
 console.log("Paquet de revue: "+packagePath);
}catch(e){
 console.error("G0.9 REFUS: "+String(e instanceof Error?e.message:e));
 process.exitCode=1;
}
