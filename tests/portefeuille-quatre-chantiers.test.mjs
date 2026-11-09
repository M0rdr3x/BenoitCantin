import test from "node:test";
import assert from "node:assert/strict";
import {loadPortfolioSources,verifierPortefeuille} from
 "../scripts/verifier_portefeuille_quatre_chantiers.mjs";
const {portfolio,nova,civic,sinjira,planText}=await loadPortfolioSources();
const check=(data=portfolio,n=nova,c=civic,s=sinjira,p=planText)=>
 verifierPortefeuille(data,n,c,s,p);
const clone=structuredClone;
test("quatre périmètres de mesure contrôlés, sans pourcentage commun artificiel",()=>{
 const r=check();
 assert.equal(r.ok,true,r.errors.join("; "));
 assert.equal(portfolio.tracks.length,5);
 assert.equal(r.completion_certified,false);
 assert.equal(r.publication_or_activation_authorized,false);
 assert.equal(r.verified_project_completion_date,null);
});
test("Projet Nova : 47/100, 53 manquants, cible 2027 NON garantie",()=>{
 const r=check();assert.equal(r.nova_programme_score,47);
 assert.equal(r.nova_points_missing,53);
 assert.equal(r.candidate_nova_target,"2027-12-31");
 assert.equal(portfolio.tracks[0].target_is_guaranteed,false);
 assert.equal(nova.scoring.documentation_maturity_estimate_percent,75);
 assert.equal(nova.decisions.not_officially_adopted,true);
});
test("modèle Nova–Sinjira : aucune évaluation autonome inventée",()=>{
 const r=check();assert.equal(r.nova_sinjira_percentage,null);
 assert.equal(portfolio.tracks[1].metric_kind,"AUCUN_BAREME_DE_COMPLETUDE_AUTONOME");
 assert.equal(portfolio.tracks[1].measures_sectors_candidate,14);
 assert.equal(portfolio.tracks[1].independently_validated_sectors_in_nova_audit,0);
});
test("boussole : 5 critères sur 12, ce n'est pas un produit terminé",()=>{
 const r=check();
 assert.deepEqual(r.compass_gates,{passed:5,total:12,coverage_only_pct:41.67});
 assert.equal(civic.compass.comparison_enabled,false);
});
test("sondage : 6 sur 11, vote et publication non autorisés",()=>{
 const r=check();
 assert.deepEqual(r.poll_gates,{passed:6,total:11,coverage_only_pct:54.55});
 assert.equal(civic.poll.published_in_source,false);
 assert.equal(civic.decision.opening_poll_approved,false);
});
test("SINJIRA complet : maturité 66,5, 13 portes ouvertes et fin inconnue",()=>{
 const r=check();assert.equal(r.sinjira_product_maturity_estimate,66.5);
 assert.equal(r.sinjira_uncertainty_percentage_points,10);
 assert.equal(r.sinjira_exit_gates_open,13);
 assert.equal(sinjira.forecast.estimated_completion_date,null);
 assert.equal(sinjira.launch.complete,false);
});
test("fausse augmentation de Projet Nova refusée",()=>{
 const p=clone(portfolio);p.tracks[0].earned=75;
 assert.ok(check(p).errors.includes("NOVA_PUBLIC_STATUS_MISREPRESENTED"));
 const n=clone(nova);n.scoring.earned=75;
 assert.ok(check(portfolio,n).errors.includes("NOVA_AUDIT_NOT_RECONCILED"));
});
test("une date de fin SINJIRA inventée ne passe pas",()=>{
 const s=clone(sinjira);s.forecast.estimated_completion_date="2027-12-31";
 assert.ok(check(portfolio,nova,civic,s).errors.includes("SINJIRA_SOURCE_NOT_COMPARABLE"));
});
test("le taux de réussite des critères ne devient pas certification des outils civiques",()=>{
 const c=clone(civic);
 c.compass.gates[5].status="PASSED";
 assert.ok(check(portfolio,nova,c).errors.includes("COMPASS_COVERAGE_IS_NOT_COMPLETION"));
 const d=clone(civic);d.poll.gates[6].status="PASSED";
 assert.ok(check(portfolio,nova,d).errors.includes("POLL_COVERAGE_IS_NOT_AUTHORIZATION"));
});
test("aucune activation de sondage politique sans décision formelle",()=>{
 const c=clone(civic);c.decision.opening_poll_approved=true;
 assert.ok(check(portfolio,nova,c).errors.includes("CIVIC_SOURCE_OR_RELEASE_GATES_CHANGED"));
 const p=clone(portfolio);p.tracks[3].publication_authorized=true;
 assert.ok(check(p).errors.includes("POLL_COVERAGE_IS_NOT_AUTHORIZATION"));
});
test("la maturité SINJIRA ne peut être arbitrairement arrondie au score d'un correctif",()=>{
 const p=clone(portfolio);p.tracks[4].estimated_percent=84;
 assert.ok(check(p).errors.includes("SINJIRA_WEIGHTED_MATURITY_NOT_CERTIFIED"));
 const s=clone(sinjira);s.domains[0].maturity=100;
 assert.ok(check(portfolio,nova,civic,s).errors.includes("SINJIRA_WEIGHTED_MATURITY_NOT_CERTIFIED"));
});
test("absence de certification et de dates précises pour les autres projets",()=>{
 const p=clone(portfolio);p.tracks[1].estimated_percent=47;
 assert.ok(check(p).errors.includes("NOVA_SINJIRA_IS_NOT_A_SEPARATE_CERTIFIED_SCORE"));
 const q=clone(portfolio);q.tracks[4].planned_target_date="2028-12-31";
 assert.ok(check(q).errors.some(e=>e.includes("UNSUPPORTED_CERTIFICATION_OR_DEADLINE")));
});
test("source PDF ou page publique ne certifie rien sans décision",()=>{
 const p=clone(portfolio);p.completion_certified=true;
 assert.ok(check(p).errors.includes("UNAUTHORIZED_COMPLETION_OR_ACTIVATION"));
 const q=clone(portfolio);q.policies.no_public_civic_poll_opening=false;
 assert.ok(check(q).errors.includes("UNAUTHORIZED_COMPLETION_OR_ACTIVATION"));
});
test("source ou dossier manquant bloque le registre",()=>{
 assert.equal(check(null).ok,false);
 assert.equal(check(portfolio,nova,civic,null).ok,false);
 const p=clone(portfolio);p.tracks.pop();
 assert.ok(check(p).errors.includes("TRACKS_MISSING_DUPLICATED_OR_REORDERED"));
});
test("la règle des cinq portes et la non-adoption Nova–Sinjira sont traçables",()=>{
 const r=check(portfolio,nova,civic,sinjira,planText.replace("G4 : généralisation","G4 : pas de contrôle"));
 assert.ok(r.errors.includes("NOVA_SINJIRA_IS_NOT_A_SEPARATE_CERTIFIED_SCORE"));
});
