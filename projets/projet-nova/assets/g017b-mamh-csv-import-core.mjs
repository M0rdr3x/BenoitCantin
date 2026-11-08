/**
 * Nova G0.17b — lecteur et concordancier prudent des CSV du MAMH.
 * Aucune connexion réseau. Les CSV officiels doivent être fournis et hachés séparément.
 * Échantillons de tests SYNTHETIC_ONLY, pas des observations municipales.
 */
const isObject = x => x !== null && typeof x === "object" && !Array.isArray(x);
const isCode = x => typeof x === "string" && /^[A-Za-z0-9_-]{1,80}$/.test(x);
const HEX = /^[a-fA-F0-9]{64}$/;
function must(ok, why) { if (!ok) throw new Error(why); }
export function parseMamhCsv(input, {delimiter = ",", maxRows = 200000, maxColumns = 30000} = {}) {
  must(typeof input === "string" && input.length > 0 && input.length <= 100000000, "CSV_REQUIRED");
  must(delimiter === "," || delimiter === ";", "DELIMITER_UNSUPPORTED");
  const csv = input.charCodeAt(0) === 0xfeff ? input.slice(1) : input;
  const result = [];
  let row = [], field = "", inQuote = false, closedQuote = false, lastWasNewline = false;
  function appendRow() {
    row.push(field); field = "";
    must(row.length <= maxColumns, "TOO_MANY_COLUMNS");
    if (result.length && row.length !== result[0].length) throw new Error("INCONSISTENT_ROW_WIDTH");
    result.push(row); row = []; closedQuote = false;
    must(result.length <= maxRows + 1, "TOO_MANY_ROWS");
  }
  for (let i = 0; i < csv.length; i++) {
    const ch = csv[i];
    if (inQuote) {
      if (ch === '"') {
        if (csv[i+1] === '"') { field += '"'; i++; }
        else { inQuote = false; closedQuote = true; }
      } else { field += ch; }
      lastWasNewline = false;
      continue;
    }
    if (ch === '"') {
      must(field === "" && !closedQuote, "UNEXPECTED_QUOTE");
      inQuote = true; lastWasNewline = false; continue;
    }
    if (ch === delimiter) {
      row.push(field); field = ""; closedQuote = false; lastWasNewline = false;
      must(row.length < maxColumns, "TOO_MANY_COLUMNS");
      continue;
    }
    if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && csv[i+1] === "\n") i++;
      appendRow(); lastWasNewline = true; continue;
    }
    must(!closedQuote, "INVALID_TRAILING_CHARACTER_AFTER_QUOTE");
    field += ch; lastWasNewline = false;
  }
  must(!inQuote, "UNCLOSED_QUOTE");
  if (!lastWasNewline || row.length > 0 || field !== "") appendRow();
  must(result.length >= 2, "CSV_MISSING_DATA");
  const [header, ...rows] = result;
  must(header.every(x=>x.length>0), "EMPTY_HEADER");
  must(new Set(header).size === header.length, "DUPLICATE_HEADER");
  return {header, rows, rowCount:rows.length, fieldCount:header.length};
}
export function parseAmountCad(raw) {
  if (raw === "" || raw == null) return null;
  must(typeof raw === "string", "AMOUNT_NOT_STRING");
  const s=raw.trim();
  if (s === "") return null;
  must(/^[+-]?[0-9]+(?:\.[0-9]{1,2})?$/.test(s), "INVALID_CAD_AMOUNT");
  const neg=s.startsWith("-"), clean=s.replace(/^[+-]/,""), [integer,decimal=""]=clean.split(".");
  const cents=Number(integer)*100+Number(decimal.padEnd(2,"0"));
  must(Number.isSafeInteger(cents), "AMOUNT_OVERFLOW");
  return neg ? -cents : cents;
}
export function inspectMamhPanel({csvText,year,config,provenance,missingOrganismCodes}) {
  must(year===2024||year===2025, "INVALID_YEAR");
  must(isObject(config)&&isObject(provenance), "CONFIG_REQUIRED");
  must(Array.isArray(missingOrganismCodes), "MISSING_ORGANISMS_LIST_REQUIRED");
  must(config.grain==="MUNICIPALITE_LOCALE"&&config.basis==="ACTUAL"&&config.consolidation==="INTEGRAL", "NONCOMPARABLE_SCOPE");
  must(isCode(config.organizationCodeColumn)&&isCode(config.organizationTypeColumn), "ORGANISM_IDENTIFIERS_MISSING");
  must(typeof config.localOrganizationTypeValue==="string"&&config.localOrganizationTypeValue!=="", "LOCAL_TYPE_MAPPING_REQUIRED");
  must(Array.isArray(config.metrics)&&config.metrics.length>0, "ACCOUNT_CODE_MAPPING_REQUIRED");
  const inspectedReal = provenance.kind==="OFFICIAL_CSV_BYTES";
  const synthetic = provenance.kind==="SYNTHETIC_ONLY";
  must(inspectedReal||synthetic, "PROVENANCE_REQUIRED");
  if (inspectedReal) {
    must(HEX.test(provenance.csvSha256||"")&&HEX.test(provenance.descriptionSha256||"")
      &&HEX.test(provenance.missingListSha256||""), "SOURCE_HASH_REQUIRED");
    must(provenance.downloadedYear===year&&provenance.dictionaryYear===year, "SOURCE_YEAR_MISMATCH");
    must(provenance.officialDictionaryChecked===true, "DICTIONARY_NOT_VERIFIED");
    must(typeof provenance.retrievedAt==="string"&&/^\d{4}-\d\d-\d\d/.test(provenance.retrievedAt),"RETRIEVAL_DATE_REQUIRED");
  }
  const csv=parseMamhCsv(csvText),headers=new Set(csv.header);
  must(headers.has(config.organizationCodeColumn)&&headers.has(config.organizationTypeColumn),"MISSING_ID_OR_TYPE_HEADER");
  must(new Set(config.metrics.map(m=>m.id)).size===config.metrics.length,"DUPLICATE_METRIC");
  must(new Set(config.metrics.map(m=>m.accountCode)).size===config.metrics.length,"ACCOUNT_REUSED");
  for(const m of config.metrics) {
    must(isCode(m.accountCode)&&isCode(m.id)&&headers.has(m.accountCode), "ACCOUNT_HEADER_NOT_FOUND");
    must(m.descriptionVerifiedInYear===true && typeof m.meaning==="string" && m.meaning.length>2, "ACCOUNT_DESCRIPTION_UNVERIFIED");
    must(m.basis==="ACTUAL"&&m.consolidation==="INTEGRAL"&&m.unit==="CAD", "ACCOUNT_SCOPE_INVALID");
  }
  const indices=Object.fromEntries(csv.header.map((h,i)=>[h,i]));
  const entities=[],seen=new Set();
  for(const row of csv.rows){
    if(row[indices[config.organizationTypeColumn]]!==config.localOrganizationTypeValue) continue;
    const orgCode=row[indices[config.organizationCodeColumn]];
    must(isCode(orgCode),"INVALID_ORGANISM_CODE");
    must(!seen.has(orgCode),"DUPLICATE_ORGANISM");
    seen.add(orgCode);
    const values={};
    for(const m of config.metrics) values[m.id]=parseAmountCad(row[indices[m.accountCode]]);
    entities.push({code:orgCode,values});
  }
  must(entities.length>0, "NO_LOCAL_MUNICIPALITY_ROWS");
  const missing=new Set(missingOrganismCodes);
  must([...missing].every(isCode),"INVALID_MISSING_CODE");
  must(!entities.some(x=>missing.has(x.code)),"MISSING_BUT_PRESENT_ORGANISM");
  const completenessReady = Boolean(provenance.missingListCompleteForSamePeriod===true&&provenance.officialDictionaryChecked===true&&inspectedReal);
  const metrics=config.metrics.map(x=>({id:x.id,accountCode:x.accountCode,meaning:x.meaning,basis:x.basis,consolidation:x.consolidation,unit:x.unit}));
  return {
    year,kind:provenance.kind,grain:config.grain,basis:config.basis,consolidation:config.consolidation,
    entities,metrics,
    rawRowCount:csv.rowCount,localMunicipalitiesIncluded:entities.length,
    missingMunicipalityCodes:[...missing].sort(),
    completenessReady,
    sourceFingerprint:inspectedReal?provenance.csvSha256:null,
    officialSourceRecordImported:inspectedReal,
    amountsUnit:"CAD_CENTS_EXACT",
    nationalPopulationCoverageVerified:false,
    novaFiscalModelAudited:false
  };
}
export function compareMamhPanels(a,b,{dictionaryComparabilityApproved=false,coverageReviewed=false}={}){
  must(isObject(a)&&isObject(b)&&a.year===2024&&b.year===2025, "PERIODS_REQUIRE_2024_AND_2025");
  must(a.grain==="MUNICIPALITE_LOCALE"&&b.grain===a.grain&&a.basis==="ACTUAL"&&b.basis==="ACTUAL"
    &&a.consolidation==="INTEGRAL"&&b.consolidation==="INTEGRAL", "MIXED_JURISDICTIONS");
  must(Array.isArray(a.metrics)&&Array.isArray(b.metrics), "METRICS_REQUIRED");
  must(a.metrics.length===b.metrics.length, "ACCOUNT_METRIC_SET_CHANGED");
  const metrics=new Map(b.metrics.map(m=>[m.id,m]));
  for(const m of a.metrics){
    const n=metrics.get(m.id);
    must(n&&n.meaning===m.meaning&&n.basis===m.basis&&n.consolidation===m.consolidation&&n.unit===m.unit, "ACCOUNT_DEFINITION_CHANGED");
    if(n.accountCode!==m.accountCode) must(dictionaryComparabilityApproved, "ACCOUNT_CODE_CHANGED_UNAPPROVED");
  }
  const mapB=new Map(b.entities.map(x=>[x.code,x]));
  const matched=a.entities.filter(x=>mapB.has(x.code)).map(x=>{
    const y=mapB.get(x.code),metricValues={};
    for(const m of a.metrics){
      const x0=x.values[m.id],y0=y.values[m.id];
      metricValues[m.id]={year2024CadCents:x0,year2025CadCents:y0,
        absoluteChangeCadCents:x0===null||y0===null?null:y0-x0,
        pctChange:x0===null||y0===null||x0===0?null:(y0-x0)/x0*100};
    }
    return {municipalityCode:x.code,metrics:metricValues};
  });
  const codesA=new Set(a.entities.map(x=>x.code)),codesB=new Set(b.entities.map(x=>x.code));
  const unmatched2024=[...codesA].filter(x=>!codesB.has(x)).sort();
  const unmatched2025=[...codesB].filter(x=>!codesA.has(x)).sort();
  const comparable=Boolean(dictionaryComparabilityApproved&&coverageReviewed&&a.completenessReady&&b.completenessReady
    &&a.officialSourceRecordImported&&b.officialSourceRecordImported
    &&a.sourceFingerprint!==b.sourceFingerprint
    &&unmatched2024.length===0&&unmatched2025.length===0
    &&a.missingMunicipalityCodes.length===0&&b.missingMunicipalityCodes.length===0);
  const aggregate=comparable?Object.fromEntries(a.metrics.map(m=>{
    const vals=matched.map(x=>x.metrics[m.id]);
    const hasMissing=vals.some(x=>x.year2024CadCents===null||x.year2025CadCents===null);
    const sum0=hasMissing?null:vals.reduce((s,x)=>s+x.year2024CadCents,0);
    const sum1=hasMissing?null:vals.reduce((s,x)=>s+x.year2025CadCents,0);
    return [m.id,{year2024CadCents:sum0,year2025CadCents:sum1,
      changeCadCents:sum0===null||sum1===null?null:sum1-sum0}];
  })):null;
  return {year2024:2024,year2025:2025,matchedMunicipalities:matched.length,unmatched2024,unmatched2025,
    matchedRows:matched,aggregate,
    provinceWideConclusionAuthorized:comparable,
    verified2026NovaReplacementRevenueCad:null,
    official2026MunicipalForecastCad:null,
    doubleCountedProvinceToMunicipalTransfersEliminated:false,
    scoreIncrementEarned:false};
}
