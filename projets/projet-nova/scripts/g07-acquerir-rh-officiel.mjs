/**
 * Projet Nova — G0.7. Acquisition manuelle du classeur public officiel RH.
 * Lance uniquement dans workflow_dispatch. Ne publie aucun tableau de salariés.
 * Écrit un rapport et, en cas de succès, le XLSX dans un artefact GitHub Actions.
 */
import {mkdir,writeFile} from "node:fs/promises";
import {join,resolve} from "node:path";
import {createHash} from "node:crypto";
import {
  OFFICIAL_RH_XLSX_URL,RH_SOURCE_ID,MAX_OFFICIAL_XLSX_BYTES,
  readXlsxZipDirectory,inspectAcquisitionManifest
} from "../assets/g07-rh-acquisition-core.mjs";

const outputDir=resolve(process.env.G07_ARTIFACT_DIR || "g07-acquisition-output");
const savedFile=join(outputDir,"rh-rsss-2024-2025-source.xlsx");
const reportFile=join(outputDir,"source-audit.json");

const base={
  schema:"nova-rh-g07-acquisition/v1",source_id:RH_SOURCE_ID,
  official_url:OFFICIAL_RH_XLSX_URL,
  retrieved_at_utc:null,status:"DOWNLOAD_BLOCKED",sha256:null,size_bytes:null,
  xlsx_inventory:null,source_http_status:null,
  content_type:null,etag:null,last_modified:null,
  etp_clinical_values_imported:0,regional_workforce_values_imported:0,
  external_validation_completed:false,g0_formally_passed:false,
  pilot_authorized:false,financial_savings_certified:false,
  statement:"Contrôle de provenance et conteneur XLSX seulement. Aucun effectif, ETP, consultation ou coût interprété."
};

function requireSafeUrl(raw) {
  const u=new URL(raw);
  const canonical=new URL(OFFICIAL_RH_XLSX_URL);
  if(u.protocol!=="https:" || u.hostname!==canonical.hostname || u.username || u.password ||
     u.port || !u.pathname.startsWith("/cdn-contenu/sante/")) {
    throw new Error("REDIRECT_NOT_IN_OFFICIAL_CDN");
  }
  return u.toString();
}

async function fetchOfficialWorkbook() {
  let current=requireSafeUrl(OFFICIAL_RH_XLSX_URL);
  for(let redirects=0;redirects<4;redirects++) {
    const resp=await fetch(current,{
      method:"GET",redirect:"manual",signal:AbortSignal.timeout(30000),
      headers:{"Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream",
               "User-Agent":"ProjetNova-G07-DocumentaryAudit/1.0"}
    });
    if([301,302,303,307,308].includes(resp.status)) {
      const location=resp.headers.get("location");
      if(!location)throw new Error("REDIRECT_WITHOUT_LOCATION");
      current=requireSafeUrl(new URL(location,current).toString());
      continue;
    }
    if(resp.status!==200)throw new Error("SOURCE_HTTP_"+resp.status);
    const stated=Number(resp.headers.get("content-length")||0);
    if(stated>MAX_OFFICIAL_XLSX_BYTES)throw new Error("SOURCE_FILE_TOO_LARGE");
    if(!resp.body)throw new Error("SOURCE_EMPTY_RESPONSE");
    const chunks=[];let total=0;
    const reader=resp.body.getReader();
    for(;;) {
      const {done,value}=await reader.read();
      if(done)break;
      if(value) {
        total+=value.byteLength;
        if(total>MAX_OFFICIAL_XLSX_BYTES) {
          await reader.cancel("file too large");
          throw new Error("SOURCE_FILE_TOO_LARGE");
        }
        chunks.push(Buffer.from(value));
      }
    }
    if(total<1000)throw new Error("SOURCE_XLSX_UNEXPECTEDLY_SMALL");
    const bytes=Buffer.concat(chunks,total);
    const inventory=readXlsxZipDirectory(bytes);
    return {bytes,inventory,metadata:{
      source_http_status:200,
      content_type:resp.headers.get("content-type"),
      etag:resp.headers.get("etag"),last_modified:resp.headers.get("last-modified"),
      retrieved_at_utc:new Date().toISOString(),
      sha256:createHash("sha256").update(bytes).digest("hex"),
      size_bytes:bytes.byteLength
    }};
  }
  throw new Error("TOO_MANY_REDIRECTS");
}

await mkdir(outputDir,{recursive:true});
let report;
try {
  const {bytes,inventory,metadata}=await fetchOfficialWorkbook();
  report={...base,...metadata,
    xlsx_inventory:inventory,status:"ACQUIRED_UNINTERPRETED"};
  const validation=inspectAcquisitionManifest(report);
  if(!validation.ok)throw new Error("AUDIT_MANIFEST_INVALID_"+validation.failures.join("_"));
  await writeFile(savedFile,bytes,{flag:"wx"});
  console.log("Fichier public officiel acquis: "+report.size_bytes+
    " octets; SHA-256 "+report.sha256+
    "; feuilles XML déclarées: "+inventory.worksheet_count);
  console.log("AUCUN chiffre d'emploi/ETP n'a été extrait ou validé.");
} catch (e) {
  const reason=String(e instanceof Error?e.message:e);
  report={...base,error_code:reason.substring(0,160),note:
    "Échec ou contrôle refusé; aucune source locale certifiée. Ne pas interpréter le fichier comme acquis."};
  process.exitCode=1;
  console.error("Acquisition RH G0.7 bloquée: "+report.error_code);
}
const verdict=inspectAcquisitionManifest(report);
if(!verdict.ok){
  console.error("Manifest acquisition invalide: "+verdict.failures.join(", "));
  process.exitCode=1;
}
await writeFile(reportFile,JSON.stringify(report,null,2)+"\n",{flag:"w"});
console.log("Rapport: "+reportFile);
