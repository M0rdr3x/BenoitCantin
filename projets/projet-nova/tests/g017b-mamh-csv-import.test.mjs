import test from "node:test";
import assert from "node:assert/strict";
import {parseMamhCsv,parseAmountCad,inspectMamhPanel,compareMamhPanels}
from "../assets/g017b-mamh-csv-import-core.mjs";
const config={
 grain:"MUNICIPALITE_LOCALE",basis:"ACTUAL",consolidation:"INTEGRAL",
 organizationCodeColumn:"CODE",organizationTypeColumn:"CATEGORIE",localOrganizationTypeValue:"MUN",
 metrics:[
  {id:"REVENUS",accountCode:"CRIIX00001",meaning:"Revenus total",descriptionVerifiedInYear:true,basis:"ACTUAL",consolidation:"INTEGRAL",unit:"CAD"},
  {id:"CHARGES",accountCode:"CRIIX00002",meaning:"Charges total",descriptionVerifiedInYear:true,basis:"ACTUAL",consolidation:"INTEGRAL",unit:"CAD"}
 ]
};
const C24="CODE,CATEGORIE,CRIIX00001,CRIIX00002\n02047,MUN,100.20,80.10\n01234,MUN,200.00,150.00\n00001,MRC,900.00,800.00\n";
const C25="CODE,CATEGORIE,CRIIX00001,CRIIX00002\n02047,MUN,110.20,85.10\n05678,MUN,50.00,40.00\n00001,MRC,999.00,850.00\n";
const synthetic={kind:"SYNTHETIC_ONLY",officialDictionaryChecked:false,missingListCompleteForSamePeriod:false};
const panel=(year,csvText,modify={},missing=[])=>inspectMamhPanel({
 csvText,year,config:{...structuredClone(config),...modify},provenance:structuredClone(synthetic),missingOrganismCodes:missing
});
const a=panel(2024,C24),b=panel(2025,C25);
const throws=(f,msg)=>assert.throws(f,new RegExp(msg));
test("CSV: UTF-8 BOM stripped",()=>assert.deepEqual(parseMamhCsv("\ufeffA,B\n1,2\n").header,["A","B"]));
test("CSV: comma parser",()=>assert.equal(parseMamhCsv("A,B\n1,2\n").rowCount,1));
test("CSV: double quote and embedded comma",()=>assert.equal(parseMamhCsv('A,B\n"val,une",2\n').rows[0][0],"val,une"));
test("CSV: double quote escape",()=>assert.equal(parseMamhCsv('A,B\n"la ""citation""",2').rows[0][0],'la "citation"'));
test("CSV: CRLF accepted",()=>assert.deepEqual(parseMamhCsv("A,B\r\n1,2\r\n").rows,[["1","2"]]));
test("CSV: multiline quotes",()=>assert.equal(parseMamhCsv('A,B\n"ligne\nsuite",2\n').rows[0][0],"ligne\nsuite"));
test("CSV: explicit semicolon supported",()=>assert.equal(parseMamhCsv("A;B\n1;2",{delimiter:";"}).rows[0][1],"2"));
test("CSV: incomplete quote rejected",()=>throws(()=>parseMamhCsv('A,B\n"abc,2\n'),"UNCLOSED_QUOTE"));
test("CSV: trailing after quote rejected",()=>throws(()=>parseMamhCsv('A,B\n"x"q,2\n'),"INVALID_TRAILING_CHARACTER_AFTER_QUOTE"));
test("CSV: quote inside unquoted field rejected",()=>throws(()=>parseMamhCsv('A,B\nx"q,2\n'),"UNEXPECTED_QUOTE"));
test("CSV: row width mismatch rejected",()=>throws(()=>parseMamhCsv("A,B\n1,2,3"),"INCONSISTENT_ROW_WIDTH"));
test("CSV: duplicate column rejected",()=>throws(()=>parseMamhCsv("A,A\n1,2\n"),"DUPLICATE_HEADER"));
test("CSV: missing data rejected",()=>throws(()=>parseMamhCsv("A,B\n"),"CSV_MISSING_DATA"));
test("CSV: oversized max rows rejected",()=>throws(()=>parseMamhCsv("A,B\n1,2\n3,4\n",{maxRows:1}),"TOO_MANY_ROWS"));
test("CAD: zero",()=>assert.equal(parseAmountCad("0"),0));
test("CAD: cents",()=>assert.equal(parseAmountCad("123.45"),12345));
test("CAD: negative cents",()=>assert.equal(parseAmountCad("-5.01"),-501));
test("CAD: blank is unknown null",()=>assert.equal(parseAmountCad(""),null));
test("CAD: whitespace is unknown",()=>assert.equal(parseAmountCad("   "),null));
test("CAD: decimal comma rejected without explicit parsing",()=>throws(()=>parseAmountCad("1,25"),"INVALID_CAD_AMOUNT"));
test("CAD: thousands separated string rejected",()=>throws(()=>parseAmountCad("1 234"),"INVALID_CAD_AMOUNT"));
test("CAD: scientific notation rejected",()=>throws(()=>parseAmountCad("1e6"),"INVALID_CAD_AMOUNT"));
test("CAD: unsafe large number rejected",()=>throws(()=>parseAmountCad("999999999999999"),"AMOUNT_OVERFLOW"));
test("Panel: one municipality per row and MRC excluded",()=>assert.equal(a.entities.length,2));
test("Panel: leading zero organizational code preserved",()=>assert.equal(a.entities[0].code,"02047"));
test("Panel: figures in exact CAD cents",()=>assert.equal(a.entities[0].values.REVENUS,10020));
test("Panel: status synthetic",()=>assert.equal(a.kind,"SYNTHETIC_ONLY"));
test("Panel: national population coverage not verified by synthetic",()=>assert.equal(a.completenessReady,false));
test("Panel: year 2023 rejected",()=>throws(()=>panel(2023,C24),"INVALID_YEAR"));
test("Panel: missing declared column rejected",()=>throws(()=>panel(2024,C24,{organizationCodeColumn:"NEANT"}),"MISSING_ID_OR_TYPE_HEADER"));
test("Panel: wrong accounting basis rejected",()=>throws(()=>panel(2024,C24,{basis:"BUDGET"}),"NONCOMPARABLE_SCOPE"));
test("Panel: case without local organization filter rejected",()=>throws(()=>panel(2024,C24,{localOrganizationTypeValue:""}),"LOCAL_TYPE_MAPPING_REQUIRED"));
test("Panel: unknown account code rejected",()=>{const c=structuredClone(config);c.metrics[0].accountCode="ZZZZZ";throws(()=>panel(2024,C24,{metrics:c.metrics}),"ACCOUNT_HEADER_NOT_FOUND");});
test("Panel: source description must be approved",()=>{const c=structuredClone(config);c.metrics[0].descriptionVerifiedInYear=false;throws(()=>panel(2024,C24,{metrics:c.metrics}),"ACCOUNT_DESCRIPTION_UNVERIFIED");});
test("Panel: missing organizer set mandatory",()=>throws(()=>inspectMamhPanel({csvText:C24,year:2024,config,provenance:synthetic}),"MISSING_ORGANISMS_LIST_REQUIRED"));
test("Panel: duplicates cannot silently double count",()=>throws(()=>panel(2024,C24+C24.split("\n")[1]+"\n"),"DUPLICATE_ORGANISM"));
test("Panel: missing-not-actually-missing is rejected",()=>throws(()=>panel(2024,C24,{},["02047"]),"MISSING_BUT_PRESENT_ORGANISM"));
test("Panel: empty municipal cohort rejected",()=>throws(()=>panel(2024,C24,{localOrganizationTypeValue:"SCHOOL"}),"NO_LOCAL_MUNICIPALITY_ROWS"));
test("Panel: real source cannot be claimed without three SHA256",()=>throws(()=>inspectMamhPanel({csvText:C24,year:2024,config,provenance:{kind:"OFFICIAL_CSV_BYTES"},missingOrganismCodes:[]}),"SOURCE_HASH_REQUIRED"));
test("Panel: real source cannot mix 2024 with 2025 dictionary",()=>throws(()=>inspectMamhPanel({csvText:C24,year:2024,config,provenance:{kind:"OFFICIAL_CSV_BYTES",csvSha256:"a".repeat(64),descriptionSha256:"b".repeat(64),missingListSha256:"c".repeat(64),downloadedYear:2024,dictionaryYear:2025},missingOrganismCodes:[]}),"SOURCE_YEAR_MISMATCH"));
test("Comparison: common municipality matches",()=>assert.equal(compareMamhPanels(a,b).matchedMunicipalities,1));
test("Comparison: unmatched 2024 entity surfaced",()=>assert.deepEqual(compareMamhPanels(a,b).unmatched2024,["01234"]));
test("Comparison: unmatched 2025 entity surfaced",()=>assert.deepEqual(compareMamhPanels(a,b).unmatched2025,["05678"]));
test("Comparison: synthetic data never authorizes province-wide aggregation",()=>assert.equal(compareMamhPanels(a,b,{dictionaryComparabilityApproved:true,coverageReviewed:true}).provinceWideConclusionAuthorized,false));
test("Comparison: national aggregate withheld",()=>assert.equal(compareMamhPanels(a,b).aggregate,null));
test("Comparison: synthetic row delta is not a government budget",()=>assert.equal(compareMamhPanels(a,b).matchedRows[0].metrics.REVENUS.absoluteChangeCadCents,1000));
test("Comparison: wrong years rejected",()=>throws(()=>compareMamhPanels(b,a),"PERIODS_REQUIRE_2024_AND_2025"));
test("Comparison: different account meaning rejected",()=>{const c=structuredClone(b);c.metrics[0].meaning="Autre définition";throws(()=>compareMamhPanels(a,c),"ACCOUNT_DEFINITION_CHANGED");});
test("Comparison: changed account code without dictionary approval rejected",()=>{const c=structuredClone(b);c.metrics[0].accountCode="CRIIX00123";throws(()=>compareMamhPanels(a,c),"ACCOUNT_CODE_CHANGED_UNAPPROVED");});
test("Comparison: no sovereign or Nova budget invented",()=>assert.equal(compareMamhPanels(a,b).verified2026NovaReplacementRevenueCad,null));
test("Comparison: transfer cancellation not automatically assumed",()=>assert.equal(compareMamhPanels(a,b).doubleCountedProvinceToMunicipalTransfersEliminated,false));
test("Comparison: no score increment inferred",()=>assert.equal(compareMamhPanels(a,b).scoreIncrementEarned,false));
