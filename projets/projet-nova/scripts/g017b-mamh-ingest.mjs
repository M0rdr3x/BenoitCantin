#!/usr/bin/env node
/**
 * Usage: node scripts/g017b-mamh-ingest.mjs \
 *  --year2024 path.csv --year2025 path.csv \
 *  --desc2024 description.csv --desc2025 description.csv \
 *  --absent2024 absent.csv --absent2025 absent.csv \
 *  --mapping mapping.json --retrievedAt 2026-11-08 --output audit.json
 *
 * Aucun téléchargement automatique. N'utiliser que des fichiers MAMH locaux obtenus et datés.
 * Ne remplace pas l'expertise comptable, juridique ou la vérification des jeux de données.
 */
import {readFile,writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {parseMamhCsv,inspectMamhPanel,compareMamhPanels} from "../assets/g017b-mamh-csv-import-core.mjs";
const required=["year2024","year2025","desc2024","desc2025","absent2024","absent2025","mapping","retrievedAt","output"];
function usage(){return "Missing arguments. Need: "+required.map(x=>"--"+x).join(" ");}
function hash(b){return createHash("sha256").update(b).digest("hex");}
function toUtf8(buffer){
  return new TextDecoder("utf-8",{fatal:true}).decode(buffer);
}
function colsAsObjects(table){
  const h=table.header;
  return table.rows.map(row=>Object.fromEntries(h.map((key,i)=>[key,row[i]])));
}
function findDescriptions(text,cfg,metrics){
  if(!cfg||!cfg.accountCodeColumn||!cfg.descriptionColumn)throw new Error("DICTIONARY_COLUMN_MAP_REQUIRED");
  const records=colsAsObjects(parseMamhCsv(text));
  const codes=new Map();
  for(const rec of records){
    const code=rec[cfg.accountCodeColumn];
    if(!code)continue;
    if(codes.has(code))throw new Error("DUPLICATE_DICTIONARY_ACCOUNT");
    codes.set(code,(rec[cfg.descriptionColumn]||"").trim());
  }
  for(const m of metrics){
    if(!codes.has(m.accountCode))throw new Error("UNKNOWN_ACCOUNT_CODE_IN_DICTIONARY: "+m.accountCode);
    if(codes.get(m.accountCode)!==m.meaning)throw new Error("DICTIONARY_DESCRIPTION_MISMATCH: "+m.accountCode);
  }
}
function absentCodes(text,conf){
  if(!conf||!conf.codeColumn)throw new Error("MISSING_LIST_CODE_COLUMN_REQUIRED");
  const rows=colsAsObjects(parseMamhCsv(text));
  if(!rows.length)throw new Error("EMPTY_ABSENCE_DOCUMENT");
  const ids=rows.map(x=>x[conf.codeColumn]).filter(Boolean);
  if(new Set(ids).size!==ids.length)throw new Error("DUPLICATE_MISSING_CODES");
  return ids;
}
async function main(){
  const args={};
  for(let i=2;i<process.argv.length;i+=2){
    const name=process.argv[i],value=process.argv[i+1];
    if(!name?.startsWith("--")||value===undefined||value.startsWith("--"))throw new Error(usage());
    args[name.slice(2)]=value;
  }
  if(required.some(k=>!args[k]))throw new Error(usage());
  if(!/^\d{4}-\d{2}-\d{2}$/.test(args.retrievedAt))throw new Error("INVALID_RETRIEVAL_DATE");
  const mapping=JSON.parse(await readFile(args.mapping,"utf8"));
  if(mapping.schema!=="nova-g017b-local-real-mamh-mapping/v1")throw new Error("MAPPING_SCHEMA_MISMATCH");
  if(mapping.approvedForGovernmentClaims===true)throw new Error("CANNOT_APPROVE_PUBLIC_CLAIMS_AUTOMATICALLY");
  const panels=[],lineage={};
  for(const year of [2024,2025]){
    const yr=String(year), dataB=await readFile(args["year"+yr]),dictB=await readFile(args["desc"+yr]),missingB=await readFile(args["absent"+yr]);
    const conf=mapping.years?.[yr];
    if(!conf||!Array.isArray(conf.metrics)||!conf.dictionaryColumns||!conf.missingColumns)throw new Error("YEAR_SPECIFIC_MAPPING_REQUIRED: "+yr);
    const csv=toUtf8(dataB),dictionary=toUtf8(dictB),absent=toUtf8(missingB);
    findDescriptions(dictionary,conf.dictionaryColumns,conf.metrics);
    const missingCodes=absentCodes(absent,conf.missingColumns);
    const panel=inspectMamhPanel({
      csvText:csv,year,config:conf,
      missingOrganismCodes:missingCodes,
      provenance:{
        kind:"OFFICIAL_CSV_BYTES",
        csvSha256:hash(dataB),descriptionSha256:hash(dictB),
        missingListSha256:hash(missingB),
        downloadedYear:year,dictionaryYear:year,
        retrievedAt:args.retrievedAt,
        officialDictionaryChecked:true,
        missingListCompleteForSamePeriod:conf.missingListReviewed===true
      }
    });
    panels.push(panel);
    lineage[yr]={csvSha256:hash(dataB),descriptionSha256:hash(dictB),missingListSha256:hash(missingB),
      rowsInFile:panel.rawRowCount,municipalityRowsSelected:panel.localMunicipalitiesIncluded,
      missingCodesFromFile:missingCodes.length,
      percentCoverageClaimAuthorized:false};
  }
  const compared=compareMamhPanels(panels[0],panels[1],{
    dictionaryComparabilityApproved:mapping.crossYearDictionaryReviewed===true,
    coverageReviewed:mapping.coverageReviewed===true
  });
  // Les agrégats ne sont PAS une preuve que le modèle Nova est financé.
  const audit={
    schema:"nova-g017b-executed-local-csv-data-review/v1",runDate:args.retrievedAt,
    sourceDataset:"https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents",
    byteFingerprints:lineage,
    sourceYears:[2024,2025],
    municipalityCounts:panels.map(p=>({year:p.year,rows:p.localMunicipalitiesIncluded,coverageReady:p.completenessReady})),
    diagnostics:{
      matchedMunicipalities:compared.matchedMunicipalities,
      unmatched2024:compared.unmatched2024,unmatched2025:compared.unmatched2025,
      officialNationalAggregationPermitted:compared.provinceWideConclusionAuthorized,
      annualAccountingValuesForMatchedMunicipalities:compared.matchedRows,
      aggregateOnlyIfAllGatesSatisfied:compared.aggregate,
      intergovernmentalTransferEliminationPerformed:false,
      provincialGovernmentFiscalCalendarReconciled:false,
      auditableMeaningAndSourceBeforePolicy:true
    },
    programCompletionScoreChange:0,
    actualMunicipalDataParsed:true,
    twoLevySystemFinanced:false,
    legalAndIndependentCertification:false
  };
  await writeFile(args.output,JSON.stringify(audit,null,2)+"\n","utf8");
  process.stdout.write(JSON.stringify({reportPath:args.output,years:[2024,2025],
    matchedMunicipalities:compared.matchedMunicipalities,verifiedProvinceWideAggregation:compared.provinceWideConclusionAuthorized,
    taxRateEstablished:false})+"\n");
}
main().catch(e=>{process.stderr.write("Import rejected: "+e.message+"\n");process.exitCode=1;});
