/**
 * Nova–Sinjira : contrôle documentaire des 14 secteurs NV-01..NV-14.
 * Ce rapport mesure des PREUVES, jamais un pourcentage d'achèvement global.
 * Un champ absent/vidé est une preuve manquante, pas une valeur financière zéro.
 */
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';

const MODES=['public_actuel','public_reorganise','prive','cooperative','obnl'];
const EVIDENCE=[
  'source_de_jeu_de_donnees_precis','date_valeur','periode_observation',
  'territoire','population','nombre_unites','annee_de_prix'
];
const HUMAN_GATES=['qualite_verifiee','chiffrage_valide','affectation_personnel_validee'];
const SCHEMA='nova-sinjira-registre-donnees-service/v1';
const nonempty=v=>v!==null&&v!==undefined&&
  (typeof v!=='string'||v.trim()!=='')&&
  (!Array.isArray(v)||v.length>0);
// Une URL candidate ou un objet vide ne constitue pas un jeu précis cité.
const preciseSource=v=>typeof v==='string'&&v.trim().length>0;
// Le montant zéro peut être réel, mais doit être EXPLICITE : unité et
// valeur numérique finie, non négative. Éviter les objets vides, chaînes
// et propriétés héritées qui simulaient jusqu'ici un coût documenté.
export function isDocumentedModeCost(value){
  return Boolean(value&&typeof value==='object'&&!Array.isArray(value)&&
    Object.hasOwn(value,'valeur')&&Object.hasOwn(value,'unite')&&
    typeof value.valeur==='number'&&Number.isFinite(value.valeur)&&
    value.valeur>=0&&typeof value.unite==='string'&&value.unite.trim());
}
export function inspectSectorRegister(data){
  const errors=[];
  if(!data||typeof data!=='object'||Array.isArray(data))
    return {validStructure:false,errors:['registre: objet JSON requis']};
  if(data.schema!==SCHEMA)errors.push('schema: version de registre inattendue');
  const dossiers=data.dossiers;
  if(!Array.isArray(dossiers)||dossiers.length!==14)
    errors.push('dossiers: exactement 14 dossiers NV-01..NV-14 requis');
  const seen=new Set(),rows=[];
  for(const [index,d] of (Array.isArray(dossiers)?dossiers:[]).entries()){
    if(!d||typeof d!=='object'||Array.isArray(d)){
      errors.push(`dossiers[${index}]: objet sectoriel requis`);
      continue;
    }
    const id=d.id;
    const expected=`NV-${String(index+1).padStart(2,'0')}`;
    if(typeof id!=='string'||!/\bNV-\d{2}\b/.test(id)||id!==expected)
      errors.push(`dossiers[${index}]: identifiant attendu ${expected}`);
    if(seen.has(id))errors.push(`dossiers[${index}]: identifiant en double`);
    seen.add(id);
    if(!nonempty(d.domaine)||!nonempty(d.unite_comparaison_proposee))
      errors.push(`${expected}: nom de domaine et unité nécessaires`);
    const missing=EVIDENCE.filter(field=>field==='source_de_jeu_de_donnees_precis'
      ?!preciseSource(d[field]):!nonempty(d[field]));
    for(const gate of HUMAN_GATES)
      if(typeof d[gate]!=='boolean')errors.push(`${expected}: ${gate} doit être booléen`);
    const costs=d.couts_par_mode;
    if(!costs||typeof costs!=='object'||Array.isArray(costs)){
      errors.push(`${expected}: couts_par_mode attendu sous forme d'objet`);
    }else if(MODES.some(mode=>!Object.hasOwn(costs,mode))){
      errors.push(`${expected}: les cinq modes de comparaison doivent être présents`);
    }
    const costModesMissing=MODES.filter(mode=>
      !costs||!Object.hasOwn(costs,mode)||!isDocumentedModeCost(costs[mode]));
    if(d.chiffrage_valide&&(missing.length||costModesMissing.length||!d.qualite_verifiee))
      errors.push(`${expected}: chiffrage déclaré validé sans source, comparaisons complètes et contrôle de qualité`);
    if(d.affectation_personnel_validee&&missing.length)
      errors.push(`${expected}: affectation personnelle prétendue validée sans traçabilité minimale`);
    const humanMissing=HUMAN_GATES.filter(field=>d[field]!==true);
    const documentaryComplete=missing.length===0&&costModesMissing.length===0&&
      humanMissing.length===0;
    rows.push({
      id:d.id,domaine:d.domaine||'Non précisé',
      source_precise:preciseSource(d.source_de_jeu_de_donnees_precis),
      qualite_verifiee:d.qualite_verifiee===true,
      chiffrage_valide:d.chiffrage_valide===true,
      personnel_valide:d.affectation_personnel_validee===true,
      missing_evidence:missing,
      missing_cost_modes:costModesMissing,
      missing_human_checks:humanMissing,
      documentary_complete:documentaryComplete,
      decision:'NON_HOMOLOGUE' // jamais déduire un GO d'un registre
    });
  }
  return {
    schema:'nova-sinjira-evidence-status/v1',
    reference_register_date:data.date_revue||null,
    validStructure:errors.length===0,
    errors,
    scope:'14 dossiers, aucun pourcentage global ni résultat de service inféré',
    totals:{
      sectors:rows.length,
      with_precise_source:rows.filter(x=>x.source_precise).length,
      with_quality_validated:rows.filter(x=>x.qualite_verifiee).length,
      with_costing_validated:rows.filter(x=>x.chiffrage_valide).length,
      with_staffing_validated:rows.filter(x=>x.personnel_valide).length,
      with_complete_documentary_inputs:rows.filter(x=>x.documentary_complete).length
    },
    global_completion_percent:null,
    delivery_date:null,
    sectors:rows
  };
}
const invoked=process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1];
if(invoked){
  const path=process.argv[2]||'projets/projet-nova/data/registre-donnees-services-nova-sinjira.json';
  const report=inspectSectorRegister(JSON.parse(readFileSync(path,'utf8')));
  console.log(JSON.stringify(report,null,2));
  if(!report.validStructure)process.exitCode=1;
}
