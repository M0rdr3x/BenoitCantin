/**
 * Projet Nova — G0.9 : contrat de mise en correspondance statistique RH.
 *
 * Reçoit seulement les métadonnées d'un XLSX déjà acquis et contrôlé G0.8.
 * Aucune lecture automatique de cellules et aucun résultat de personnel autorisé.
 * Les valeurs fictives sont utilisées UNIQUEMENT dans les tests.
 */
export const G09_STATUS = Object.freeze({
  BLOCKED:"SOURCE_ABSENTE",
  METADATA:"METADONNEES_SEULEMENT",
  MAPPING:"MAPPAGE_A_VALIDER",
  HUMAN_REVIEW:"REVUE_HUMAINE_REQUISE"
});
export const G09_ALLOWED_ROLES=Object.freeze([
  "DETAIL","SUBTOTAL","PROVINCIAL_TOTAL","HEADING","SUPPRESSED","NOTE"
]);
export const G09_ALLOWED_UNITS=Object.freeze([
  "PERSONNES","HEURES","ETP_DECLARÉ","CAD"
]);

const plain=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const txt=x=>typeof x==="string"&&x.trim().length>0;
const hex=x=>typeof x==="string"&&/^[0-9a-f]{64}$/i.test(x);
const cell=x=>typeof x==="string"&&/^[A-Z]{1,3}[1-9][0-9]{0,6}$/.test(x);
const rss=x=>typeof x==="string"&&/^(0[1-9]|1[0-8])$/.test(x);
const reasonable=x=>typeof x==="number"&&Number.isFinite(x)&&x>=0;
const same=(a,b)=>a===b;

export function inspectOfficialAcquisition(source){
 const errors=[];
 if(!plain(source))return {ok:false,errors:["SOURCE_MISSING"]};
 if(source.status!=="ACQUIRED_UNINTERPRETED")errors.push("NOT_ACQUIRED");
 if(source.source_id!=="MSSS_RH_2024_2025")errors.push("WRONG_SOURCE_ID");
 if(!hex(source.sha256))errors.push("HASH_MISSING");
 if(!Number.isSafeInteger(source.size_bytes)||source.size_bytes<1000)errors.push("INVALID_SIZE");
 if(!plain(source.xlsx_metadata)||source.xlsx_metadata.audit_level!=="L2_STRUCTURE_SEULEMENT"||
    source.xlsx_metadata.container_valid!==true||
    !Array.isArray(source.xlsx_metadata.sheets)||
    source.xlsx_metadata.worksheet_count!==source.xlsx_metadata.sheets.length||
    source.xlsx_metadata.worksheet_count<1||
    source.xlsx_metadata.cell_values_read!==false)
    errors.push("L2_METADATA_NOT_VERIFIED");
 if(source.etp_clinical_values_imported!==0||source.regional_workforce_values_imported!==0||
    source.g0_formally_passed!==false||source.pilot_authorized!==false)
    errors.push("UNAUTHORIZED_NUMBERS_OR_DECISIONS");
 return {ok:errors.length===0,errors};
}
/** Fiche préparatoire sans valeurs numériques, à partir de l'inventaire L2. */
export function createReviewPackage(source){
 const check=inspectOfficialAcquisition(source);
 if(!check.ok) return {
  schema:"nova-g09-rh-review-package/v1",
  status:G09_STATUS.BLOCKED,errors:check.errors,
  official_file_sha256:null,sheets:[],
  reviewed_aggregates:[],values_interpreted:0,
  g0_passed:false,pilot_authorized:false
 };
 const sheets=source.xlsx_metadata.sheets.map(s=>({
  name:s.name,path:s.xml_path,dimension:s.dimension??null,hidden:s.hidden===true,
  headers_observed:false,
  source_grain:null,source_region_type:null,source_period:null,
  column_mappings:[],
  overlapping_totals_reviewed:false,
  privacy_reviewed:false,
  independent_reviewer:null,
  status:G09_STATUS.MAPPING
 }));
 return {
  schema:"nova-g09-rh-review-package/v1",
  status:G09_STATUS.METADATA,
  official_file_sha256:source.sha256,
  source_id:source.source_id,
  source_size_bytes:source.size_bytes,
  source_retrieved_at_utc:source.retrieved_at_utc??null,
  sheets,
  reviewed_aggregates:[],values_interpreted:0,
  coverage_confirmed:false,
  g0_passed:false,pilot_authorized:false,
  note:"Inventaire des feuilles seulement. Un mappage humain doit identifier les entêtes, cellules, unités, catégories et sous-totaux; aucun chiffre RH n'est importé."
 };
}
/** Vérification d'une future ligne mappée; aucune valeur réelle n'est fournie à G0.9. */
export function inspectMappedRows(rows,packageInfo){
 const errors=[],warnings=[],seen=new Set(),validDetails=[];
 if(!Array.isArray(rows))return {ok:false,errors:["ROWS_REQUIRED"],warnings,detail_candidates:[],ready_for_release:false};
 if(!plain(packageInfo)||packageInfo.schema!=="nova-g09-rh-review-package/v1"||
    packageInfo.status!==G09_STATUS.METADATA||!hex(packageInfo.official_file_sha256)||
    !Array.isArray(packageInfo.sheets))
    return {ok:false,errors:["L2_PACKAGE_REQUIRED"],warnings,detail_candidates:[],ready_for_release:false};
 const sheets=new Set(packageInfo.sheets.map(s=>s.name));
 if(rows.length>10000)return {ok:false,errors:["ROW_LIMIT"],warnings,detail_candidates:[],ready_for_release:false};
 rows.forEach((r,i)=>{
  const path="ROW_"+(i+1);
  if(!plain(r)){errors.push(path+":INVALID");return;}
  if(!sheets.has(r.sheet_name)||!cell(r.cell_ref)){
   errors.push(path+":INVALID_SHEET_CELL");return;
  }
  const key=r.sheet_name+"!"+r.cell_ref;
  if(seen.has(key))errors.push(path+":DUPLICATE_CELL_REF");
  seen.add(key);
  if(r.source_sha256!==packageInfo.official_file_sha256)errors.push(path+":SOURCE_HASH_MISMATCH");
  if(!G09_ALLOWED_ROLES.includes(r.row_role))errors.push(path+":UNKNOWN_ROW_ROLE");
  if(r.row_role==="DETAIL"){
   if(!rss(r.rss_id))errors.push(path+":MISSING_RSS_CODE");
   if(!G09_ALLOWED_UNITS.includes(r.unit))errors.push(path+":UNKNOWN_UNIT");
   if(!txt(r.measure_id)||!txt(r.profession_group)||!txt(r.source_period)||
      !txt(r.population_scope))errors.push(path+":DEFINITION_MISSING");
   if(!reasonable(r.value))errors.push(path+":INVALID_OR_MISSING_NUMBER");
   if(r.value===0&&r.zero_explicitly_observed!==true)
       errors.push(path+":UNVERIFIED_ZERO");
   if(r.source_geography!=="RSS")errors.push(path+":NOT_RSS_GEOGRAPHY");
   if(r.human_mapping_checked!==true||r.primary_document_checked!==true||
      !txt(r.reviewer)||r.mixed_population_excluded!==true)
     errors.push(path+":HUMAN_PROVENANCE_NOT_VERIFIED");
   if(r.is_aggregate_of_other_selected_rows===true)
     errors.push(path+":OVERLAPPING_DETAIL");
   validDetails.push({
     rss_id:r.rss_id,measure_id:r.measure_id,unit:r.unit,
     profession_group:r.profession_group,source_period:r.source_period,
     population_scope:r.population_scope,
     source_cell:key,value:r.value,
     status:G09_STATUS.HUMAN_REVIEW
   });
  } else {
   if(r.value!==null&&r.value!==undefined) warnings.push(path+":EXCLUDED_NON_DETAIL_VALUE");
   if(r.row_role==="SUPPRESSED"&&r.value!==null)
     errors.push(path+":SUPPRESSED_VALUE_MUST_BE_NULL");
  }
 });
 if(rows.length===0)warnings.push("NO_VALUES_STAGED");
 // Detect duplicate conceptual observations even when sourced from distinct cells.
 const concepts=new Set();
 for(const d of validDetails){
  const key=[d.rss_id,d.measure_id,d.unit,d.profession_group,
    d.source_period,d.population_scope].join("|");
  if(concepts.has(key))errors.push("DUPLICATE_CONCEPTUAL_GRAIN:"+key);
  concepts.add(key);
 }
 // Even a valid internally reviewed extract does NOT authorize general publication,
 // ETP conversion, payroll interpretation, budgets or reforms.
 return {
  ok:errors.length===0,errors:[...new Set(errors)],warnings,
  detail_candidates:errors.length===0?validDetails:[],
  ready_for_release:false,
  regional_clinical_etp_verified:0,
  savings_verified:null,
  g0_passed:false,pilot_authorized:false
 };
}
export function inspectG09Registry(registry){
 if(!plain(registry)||!Array.isArray(registry.regions)||registry.regions.length!==18||
    !Array.isArray(registry.quality_controls)||registry.quality_controls.length<8)
   throw new Error("G09_REGISTRY_INVALID");
 const unique=new Set(registry.regions.map(r=>r.rss_id));
 if(unique.size!==18||![...unique].every(rss))throw new Error("G09_RSS_INVALID");
 const anyClaims=registry.regions.some(r=>r.headcount_from_official_xlsx!==null||
    r.clinical_fte_verified!==null||r.cost_per_episode!==null);
 return {regions:18,controls:registry.quality_controls.length,
    actual_xlsx_obtained:registry.actual_xlsx_obtained===true,
    unverified_numbers_present:anyClaims,
    g0_passed:false,pilot_authorized:false};
}
