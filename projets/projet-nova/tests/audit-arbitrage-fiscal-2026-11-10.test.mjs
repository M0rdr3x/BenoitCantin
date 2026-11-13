import test from 'node:test';
import assert from 'node:assert/strict';
import {assess,load} from '../scripts/audit-arbitrage-fiscal-2026-11-10.mjs';

const original=load(),copy=()=>structuredClone(original);
function reject(change,regex){
  const c=copy();change(c);
  assert.throws(()=>assess(c),regex);
}
test('référence : 3 options, 2 régimes, 60 exercices attendus et zéro certifié',()=>{
  const result=assess(copy());
  assert.equal(result.options_examinees,3);
  assert.equal(result.regimes_a_expertiser,2);
  assert.equal(result.exercices_scenarios_a_auditer,60);
  assert.equal(result.exercices_certifies,0);
  assert.equal(result.score_nova,47);
  assert.equal(result.points_supplementaires_autorises,0);
  assert.equal(result.horizon_certifie,null);
  assert.equal(result.publication_taux_fiscal_autorisee,false);
});
test('bloque un ancien modèle déclaré adopté',()=>reject(
  x=>{x.historical_candidate.formally_adopted=true},/ancien modèle/));
test('bloque une taxe anti-paradis fiscaux déclarée automatiquement légale',()=>reject(
  x=>{x.recent_candidate.anti_haven_legal_classification='TAXE_AUTONOME'},/classification juridique/));
test('bloque une option retenue sans arbitrage',()=>reject(
  x=>{x.choices[1].adopted=true},/option adoptée/));
test('bloque un doublon ou la suppression d’une alternative',()=>reject(
  x=>{x.choices[2].id=x.choices[1].id},/identifiants ou doublons/));
test('bloque le renommage d’un régime politique',()=>reject(
  x=>{x.regimes[0].id='CANADA_ENTIER'},/identifiants ou doublons/));
test('bloque un avis juridique sans preuve',()=>reject(
  x=>{x.regimes[0].legal_competence_review=true},/revue juridique/));
test('bloque un budget décennal incomplet maquillé en 60 cas',()=>reject(
  x=>{x.projected_finances.total_exercises_expected=59},/deux régimes/));
test('bloque un recouvrement anti-évasion inventé',()=>reject(
  x=>{x.projected_finances.anti_haven_receipt_increment_certified=300},/financement ou recette/));
test('bloque l’authentification artificielle de CSV municipaux',()=>reject(
  x=>{x.projected_finances.municipal_2024_2025_import_certified=true},/financement ou recette/));
test('bloque une revue indépendante fabriquée',()=>reject(
  x=>{x.audit_requirements.independent_legal_opinions_complete=true},/avis, consultation/));
test('bloque une hausse de score par seule création de document',()=>reject(
  x=>{x.programme_reference.progress_points=48},/score Nova/));
test('bloque la date de fin certifiée inventée',()=>reject(
  x=>{x.decision.certified_finish_date='2027-12-31'},/décision ou calendrier/));
test('bloque le choix final sans autorité compétente',()=>reject(
  x=>{x.decision.selected_option='TAXE_UNIQUE'},/décision ou calendrier/));
test('bloque un avis budgétaire indépendant imaginaire',()=>reject(
  x=>{x.regimes[1].independent_budget_review=true},/revue juridique/));
test('bloque l’existence fictive d’un article de concordance validé',()=>reject(
  x=>{x.historical_candidate.article_level_concordance_verified=true},/ancien modèle/));
