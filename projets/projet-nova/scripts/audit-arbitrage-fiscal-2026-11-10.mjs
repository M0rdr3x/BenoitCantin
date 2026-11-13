#!/usr/bin/env node
/**
 * Contrôle du DOSSIER CANDIDAT fiscal : ne choisit aucune option, aucun taux,
 * aucun revenu anti-évasion et aucune date. Lecture seule, sans accès réseau.
 */
import {readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const PATH='data/arbitrage-fiscal-concordance-2026-11-10.json';
const requiredChoices=['TAXE_UNIQUE','REVENU_PLUS_MECANISME_DISTINCT','REVENU_AVEC_ANTI_EVITEMENT_INTEGRE'];
const requiredRegimes=['QUEBEC_DANS_CANADA','QUEBEC_SOUVERAIN_HYPOTHETIQUE'];
function guard(ok,message){if(!ok)throw new Error('ARBITRAGE FISCAL INVALIDE : '+message);}
function exactIds(items,ids,label){
  guard(Array.isArray(items)&&items.length===ids.length,label+': cardinalité');
  const names=items.map(item=>item?.id);
  guard(new Set(names).size===ids.length&&ids.every(id=>names.includes(id)),
    label+': identifiants ou doublons');
}
export function load(root=ROOT){
  return JSON.parse(readFileSync(resolve(root,PATH),'utf8'));
}
export function assess(record){
  guard(record?.schema==='nova-arbitrage-fiscal-normatif-v1'&&
    record.reference_date==='2026-11-10'&&record.status==='PROPOSITION_NON_ARBITREE',
    'référence et décision provisoire');
  guard(record.historical_candidate?.rule==='TAXE_UNIQUE'&&
    record.historical_candidate.article_level_concordance_verified===false&&
    record.historical_candidate.formally_adopted===false,
    'ancien modèle sans concordance ou fausse adoption');
  guard(record.recent_candidate?.rule==='REVENU_ET_MECANISME_ANTI_PARADIS_FISCAUX'&&
    record.recent_candidate.anti_haven_legal_classification===null&&
    record.recent_candidate.formally_adopted===false,
    'classification juridique de la mesure anti-évasion non établie');
  exactIds(record.choices,requiredChoices,'options');
  guard(record.choices.every(option=>option.adopted===false),'option adoptée sans décision');
  exactIds(record.regimes,requiredRegimes,'régimes');
  guard(record.regimes.every(r=>r.legal_competence_review===null&&
    r.independent_budget_review===null&&
    r.transition_federal_municipal_coverage===null),
    'revue juridique, financière ou transition prétendue acquise');

  const f=record.projected_finances;
  guard(f?.years===10&&f.trajectories_per_regime===3&&
    f.total_exercises_expected===requiredRegimes.length*3*10,
    'deux régimes x trois trajectoires x dix ans');
  guard(f.source_model==='https://github.com/M0rdr3x/BenoitCantin/pull/673',
    'réemploi du modèle P52 existant');
  guard(f.fully_audited_exercises===0&&f.municipal_2024_2025_import_certified===false&&
    f.anti_haven_receipt_increment_certified===null&&f.full_funding_demonstrated===false,
    'financement ou recette anti-paradis fiscaux inventés');

  const evidence=record.audit_requirements;
  guard(Object.keys(evidence||{}).length===6&&
    Object.values(evidence).every(value=>value===false),
    'avis, consultation ou incidence non certifiés');
  const p=record.programme_reference;
  guard(p?.audit_date==='2026-11-05'&&p.progress_points===47&&
    p.finance_points===3&&p.finance_maximum===16&&p.score_increment_authorized===0,
    'score Nova non modifiable sans nouvel audit indépendant');
  const d=record.decision;
  guard(d?.approved===false&&d.selected_option===null&&
    d.competent_body===null&&d.adoption_date===null&&
    d.certified_finish_date===null,'décision ou calendrier fabriqué');
  return {
    reference_date:record.reference_date,
    status:'DECISION_NON_PRISE',
    options_examinees:requiredChoices.length,
    regimes_a_expertiser:requiredRegimes.length,
    exercices_scenarios_a_auditer:f.total_exercises_expected,
    exercices_certifies:f.fully_audited_exercises,
    recettes_anti_paradis_fiscaux_certifiees:null,
    score_nova:47,
    points_finances:'3/16',
    points_supplementaires_autorises:0,
    horizon_certifie:null,
    publication_taux_fiscal_autorisee:false
  };
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try{console.log(JSON.stringify(assess(load()),null,2));}
  catch(e){console.error(e.message);process.exitCode=1;}
}
