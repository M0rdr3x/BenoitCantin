/**
 * Projet Nova — G0.7: provenance et contrôle d'acquisition du classeur RH officiel.
 * Ne lit aucun dossier personnel, ne calcule aucun ETP, n'autorise aucune réforme.
 */
export const OFFICIAL_RH_XLSX_URL =
  "https://cdn-contenu.quebec.ca/cdn-contenu/sante/documents/Systeme_et_services_de_sante/organisation-services/donnees-systeme-sante-quebecois-services/ressources-humaines/denombrement-et-remuneration-effectif-rsss-2024-2025.xlsx";
export const RH_SOURCE_ID = "MSSS_RH_2024_2025";
export const MAX_OFFICIAL_XLSX_BYTES = 5 * 1024 * 1024;
export const ALLOWED_ACQUISITION_STATES = Object.freeze([
  "NOT_ACQUIRED", "DOWNLOAD_BLOCKED", "ACQUIRED_UNINTERPRETED"
]);

const isPlain = x => x!==null && typeof x==="object" && !Array.isArray(x);
const sha256 = x => typeof x==="string" && /^[0-9a-f]{64}$/i.test(x);
const dateIso = x => typeof x==="string" && !Number.isNaN(Date.parse(x));
const str = x => typeof x==="string" && x.length>0;

/**
 * L'inventaire est celui de l'annuaire central ZIP, non des valeurs des cellules.
 * Retourne un état documentaire, jamais un résultat de personnel.
 */
export function inspectXlsxInventory(entries) {
  const failures = [];
  if (!Array.isArray(entries) || entries.length<3 || entries.length>5000)
    return {ok:false,failures:["ZIP_DIRECTORY_INVALID"],worksheets:[],worksheet_count:0};
  const names = new Set();
  for (const entry of entries) {
    if (!isPlain(entry) || !str(entry.name) || entry.name.length>500 ||
        entry.name.startsWith("/") || entry.name.includes("\\") ||
        entry.name.split("/").some(x => x===".." || x===".")) {
      failures.push("ENTRY_NAME_INVALID");
      continue;
    }
    if (names.has(entry.name)) failures.push("DUPLICATE_ARCHIVE_ENTRY");
    names.add(entry.name);
    if (entry.encrypted===true) failures.push("ENCRYPTED_ENTRY");
    if (entry.uncompressed_size>100*1024*1024) failures.push("EXCESSIVE_UNCOMPRESSED_ENTRY");
  }
  if (!names.has("[Content_Types].xml")) failures.push("CONTENT_TYPES_MISSING");
  if (!names.has("xl/workbook.xml")) failures.push("WORKBOOK_MISSING");
  const sheets=[...names].filter(x=>/^xl\/worksheets\/sheet[1-9][0-9]*\.xml$/.test(x)).sort();
  if (sheets.length===0) failures.push("WORKSHEETS_MISSING");
  return {ok:failures.length===0,failures:[...new Set(failures)],
    worksheets:sheets,worksheet_count:sheets.length};
}

/**
 * Refuse de confondre fichier récupéré et effectifs extraits ou audités.
 * Les valeurs de personnel sont volontairement absentes de ce schéma.
 */
export function inspectAcquisitionManifest(m) {
  const failures=[];
  if (!isPlain(m)) return {ok:false,failures:["INVALID_MANIFEST"]};
  if (m.schema!=="nova-rh-g07-acquisition/v1") failures.push("SCHEMA_MISMATCH");
  if (m.source_id!==RH_SOURCE_ID) failures.push("SOURCE_MISMATCH");
  if (m.official_url!==OFFICIAL_RH_XLSX_URL) failures.push("URL_NOT_OFFICIAL");
  if (!ALLOWED_ACQUISITION_STATES.includes(m.status)) failures.push("STATUS_NOT_ALLOWED");
  if (m.etp_clinical_values_imported!==0 || m.regional_workforce_values_imported!==0)
    failures.push("UNVERIFIED_RH_VALUES");
  if (m.external_validation_completed!==false || m.g0_formally_passed!==false ||
      m.pilot_authorized!==false || m.financial_savings_certified!==false)
    failures.push("UNAUTHORIZED_DECISION");
  if (m.status==="ACQUIRED_UNINTERPRETED") {
    if (!sha256(m.sha256)) failures.push("HASH_MISSING");
    if (!Number.isSafeInteger(m.size_bytes) || m.size_bytes<1000 ||
        m.size_bytes>MAX_OFFICIAL_XLSX_BYTES) failures.push("SIZE_INVALID");
    if (!dateIso(m.retrieved_at_utc)) failures.push("DATE_INVALID");
    if (!isPlain(m.xlsx_inventory) || m.xlsx_inventory.ok!==true ||
        !Number.isInteger(m.xlsx_inventory.worksheet_count) ||
        m.xlsx_inventory.worksheet_count<1) failures.push("XLSX_INVENTORY_MISSING");
  } else {
    if (m.sha256!==null || m.size_bytes!==null ||
        m.retrieved_at_utc!==null || m.xlsx_inventory!==null)
      failures.push("NOT_ACQUIRED_BUT_HASH_PRESENT");
  }
  return {ok:failures.length===0,failures};
}

/**
 * Produire un bilan vérifiable des 18 RSS sans faux décompte de travailleurs.
 */
export function summarizeG07(baseline, priorRh) {
  if (!isPlain(baseline) || !isPlain(priorRh) ||
      !Array.isArray(priorRh.regions) || priorRh.regions.length!==18 ||
      !Array.isArray(baseline.source_attempts)) throw new TypeError("Registres RH invalides");
  const validation=inspectAcquisitionManifest(baseline);
  return {
    provenance_status:baseline.status,
    manifest_consistent:validation.ok,
    blocking_errors:validation.failures,
    regions:priorRh.regions.length,
    regions_with_official_workforce_values:priorRh.regions.filter(r=>
      r.source_data_imported===true && Number.isFinite(r.etp_clinical_first_line) &&
      r.independent_review===true).length,
    clinical_etp_certified:0,
    pilot_authorized:false,
    g0_formally_passed:false,
    notice:"Aucune présence numérique n'est une preuve de capacité ou de coût sans périmètre et audit."
  };
}
