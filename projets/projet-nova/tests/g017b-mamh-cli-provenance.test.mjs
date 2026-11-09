import {test} from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,writeFile,readFile,rm} from "node:fs/promises";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";

// Ce test essaie délibérément de faire passer deux CSV inventés pour des fichiers
// OFFICIELS avec de vrais SHA calculés par le CLI. Aucune connexion réseau.
const cli=fileURLToPath(new URL("../scripts/g017b-mamh-ingest.mjs",import.meta.url));
const yearCfg=()=>({
 grain:"MUNICIPALITE_LOCALE",basis:"ACTUAL",consolidation:"INTEGRAL",
 organizationCodeColumn:"CODE",organizationTypeColumn:"TYPE",
 localOrganizationTypeValue:"MUN",
 dictionaryColumns:{accountCodeColumn:"POSTE",descriptionColumn:"DESCRIPTION"},
 missingColumns:{codeColumn:"CODE"},
 missingListReviewed:true,
 metrics:[
 {id:"REVENUS",accountCode:"CRIIX00001",meaning:"Revenus total",
 descriptionVerifiedInYear:true,basis:"ACTUAL",consolidation:"INTEGRAL",unit:"CAD"},
 {id:"CHARGES",accountCode:"CRIIX00002",meaning:"Charges total",
 descriptionVerifiedInYear:true,basis:"ACTUAL",consolidation:"INTEGRAL",unit:"CAD"}
 ]
});
test("CLI: deux fixtures fictives étiquetées comme MAMH ne deviennent pas un total provincial officiel",async()=>{
 const folder=await mkdtemp(join(tmpdir(),"nova-mamh-untrusted-"));
 try{
  const csv24="CODE,TYPE,CRIIX00001,CRIIX00002\n02047,MUN,100.00,90.00\n01234,MUN,200.00,180.00\n99999,MRC,999.00,888.00\n";
  const csv25="CODE,TYPE,CRIIX00001,CRIIX00002\n02047,MUN,110.00,95.00\n01234,MUN,210.00,185.00\n99999,MRC,999.00,888.00\n";
  const dict="POSTE,DESCRIPTION\nCRIIX00001,Revenus total\nCRIIX00002,Charges total\n";
  const absent="CODE,NOTE\n,aucun organisme absent dans cette fixture\n";
  const map={schema:"nova-g017b-local-real-mamh-mapping/v1",
   approvedForGovernmentClaims:false,crossYearDictionaryReviewed:true,coverageReviewed:true,
   years:{"2024":yearCfg(),"2025":yearCfg()}};
  const names={
   year2024:"synthetic-2024.csv",year2025:"synthetic-2025.csv",
   desc2024:"synthetic-description-2024.csv",desc2025:"synthetic-description-2025.csv",
   absent2024:"synthetic-absence-2024.csv",absent2025:"synthetic-absence-2025.csv",
   mapping:"mapping-test-non-officiel.json",output:"results-non-officiels.json"
  };
  for(const [key,filename] of Object.entries(names)){
   const raw=key==="year2024"?csv24:key==="year2025"?csv25:
     key.startsWith("desc")?dict:key.startsWith("absent")?absent:
     key==="mapping"?JSON.stringify(map):null;
   if(raw!==null)await writeFile(join(folder,filename),raw,"utf8");
  }
  const argv=Object.entries(names).flatMap(([k,n])=>["--"+k,join(folder,n)]);
  const result=spawnSync(process.execPath,[cli,...argv,"--retrievedAt","2026-11-09"],{
   encoding:"utf8",timeout:15000,maxBuffer:1024*1024
  });
  assert.equal(result.status,0,result.stderr||result.stdout);
  const report=JSON.parse(await readFile(join(folder,names.output),"utf8"));
  assert.equal(report.actualMunicipalDataParsed,true);
  // Des lignes techniquement parsées ne constituent PAS une couverture officielle.
  assert.ok(report.municipalityCounts.every(x=>x.coverageReady===false));
  assert.equal(report.diagnostics.matchedMunicipalities,2);
  assert.equal(report.diagnostics.technicallyComparableCohortOnly,true);
  assert.equal(report.diagnostics.officialNationalAggregationPermitted,false);
  assert.equal(report.diagnostics.aggregateOnlyIfAllGatesSatisfied,null);
  assert.equal(report.diagnostics.sourceOriginalityIndependentlyVerified,false);
  assert.equal(report.diagnostics.proofOfProvinceMunicipalityTransferCancellation,false);
  assert.equal(report.inputsFromOfficialPublisherIndependentlyAuthenticated,false);
  assert.equal(report.officialProvincialMunicipalTotalsCertified,false);
  assert.equal(report.twoLevySystemFinanced,false);
  assert.equal(report.legalAndIndependentCertification,false);
  assert.equal(report.programCompletionScoreChange,0);
  for(const y of ["2024","2025"]){
   assert.match(report.byteFingerprints[y].csvSha256,/^[0-9a-f]{64}$/);
   assert.equal(report.byteFingerprints[y].publisherSourceAuthenticatedIndependently,false);
   assert.equal(report.byteFingerprints[y].sourceHashMatchedAgainstIndependentPublishedReceipt,false);
  }
  const summary=JSON.parse(result.stdout.trim().split("\n").at(-1));
  assert.equal(summary.verifiedProvinceWideAggregation,false);
  assert.equal(summary.independentPublisherAuthentication,false);
  assert.equal(summary.taxRateEstablished,false);
 }finally{await rm(folder,{recursive:true,force:true});}
});
