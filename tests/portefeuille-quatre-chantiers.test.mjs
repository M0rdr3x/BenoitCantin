import test from "node:test";
import assert from "node:assert/strict";
import {loadPortfolioSources,verifierPortefeuille} from
 "../scripts/verifier_portefeuille_quatre_chantiers.mjs";
const {portfolio,nova,civic,sinjira,planText,historicalCivic}=await loadPortfolioSources();
const check=(data=portfolio,n=nova,c=civic,s=sinjira,p=planText,h=historicalCivic)=>
 verifierPortefeuille(data,n,c,s,p,h);
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
test("boussole : 9 critères sur 12 au 8 novembre, pas une certification",()=>{
 const r=check();
 assert.deepEqual(r.compass_gates,{passed:9,total:12,coverage_only_pct:75});
 assert.deepEqual(r.compass_historical_2026_11_07,{passed:5,total:12});
 assert.equal(civic.compass.comparison_enabled,false);
 assert.equal(civic.compass.gates.find(g=>g.id==="COMPASS_ACCESSIBILITY").status,"PENDING");
 assert.equal(civic.compass.gates.find(g=>g.id==="COMPASS_DOCUMENTARY_VALIDATION").status,"PENDING");
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
 c.compass.gates[8].status="PASSED";
 assert.ok(check(portfolio,nova,c).errors.includes("COMPASS_COVERAGE_IS_NOT_COMPLETION"));
 assert.ok(check(portfolio,nova,c).errors.includes("CIVIC_CERTIFICATION_GATES_REMAIN_PENDING"));
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

test("la réception du 8 novembre remplace le relevé partiel du 7 novembre",()=>{
 const r=check();
 assert.equal(civic.as_of,"2026-11-08");
 assert.equal(historicalCivic.as_of,"2026-11-07");
 assert.equal(r.compass_gates.passed-historicalCivic.compass.gates.filter(g=>g.status==="PASSED").length,4);
 assert.deepEqual(r.civic_tools_combined,{passed:15,total:23,coverage_only_pct:65.22});
 assert.equal(portfolio.civic_combined.certified,false);
});
test("un retour discret au 5/12 après validation source est refusé",()=>{
 const p=clone(portfolio);p.tracks[2].passed=5;
 assert.ok(check(p).errors.includes("COMPASS_COVERAGE_IS_NOT_COMPLETION"));
 const q=clone(portfolio);q.sources.civic.path="projets/projet-nova/data/validation-sondage-boussole-2026-11-07.json";
 assert.ok(check(q).errors.includes("SOURCE_PATH_OR_DATE_CHANGED"));
});
test("une source historique modifiée ne peut simuler quatre améliorations",()=>{
 const h=clone(historicalCivic);h.compass.gates[5].status="PASSED";
 assert.ok(check(portfolio,nova,civic,sinjira,planText,h).errors.includes("CIVIC_HISTORICAL_BASELINE_CHANGED"));
});
test("la somme des critères civiques ne vaut pas certification ni ouverture",()=>{
 const p=clone(portfolio);p.civic_combined.certified=true;
 assert.ok(check(p).errors.includes("CIVIC_TOOLS_TOTAL_IS_NOT_COMPLETION"));
 const q=clone(portfolio);q.civic_combined.passed=23;
 assert.ok(check(q).errors.includes("CIVIC_TOOLS_TOTAL_IS_NOT_COMPLETION"));
 assert.equal(civic.poll.published_in_source,false);
});
