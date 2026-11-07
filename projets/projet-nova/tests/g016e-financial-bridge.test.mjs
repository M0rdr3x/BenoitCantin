import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {verifyG016eBridge} from "../assets/g016e-financial-bridge-core.mjs";
const load=async file=>JSON.parse(await readFile(new URL("../data/"+file,import.meta.url),"utf8"));
const [bridge,corp,personal,g14,g15]=await Promise.all([
 load("pont-financier-g0-16e-2021-2026.json"),
 load("assiette-societes-g0-16d-2021.json"),
 load("assiette-fiscale-particuliers-g0-16c-2023.json"),
 load("registre-assiettes-fiscales-g0-14-2026-2027.json"),
 load("matrice-preuves-g0-15-fiscalite.json")
]);
const copy=()=>structuredClone(bridge);
const inspect=d=>verifyG016eBridge(d,corp,personal,g14,g15);
test("source baseline and the 47/100 score",()=>{
 const r=inspect(bridge);assert.equal(r.ok,true,r.errors.join("|"));
 assert.equal(r.programme_score,47);assert.equal(r.budget_years_modelled_nova,0);
});
test("une recette budgétaire n'est pas une assiette imposable",()=>{
 const rows=bridge.historic_and_forecast_ledger;
 assert.equal(rows[0].amount_mcad,372261);
 assert.equal(rows[1].amount_mcad,95784);
 assert.equal(rows[2].type,"MASSE_SALARIALE_COTISABLE");
 assert.ok(rows.every(x=>x.can_directly_fund_nova===false));
});
test("les 3 millésimes sont distincts",()=>{
 assert.deepEqual([...new Set(bridge.historic_and_forecast_ledger.map(x=>x.year))],[2023,2021,2026]);
});
test("les recettes 135343 + 33046 = 168389",()=>{
 const b=bridge.official_baseline_2026_2027;
 assert.equal(b.own_revenue_mcad+b.federal_transfers_mcad,b.total_revenue_mcad);
});
test("réconciliation dépenses: 161081 + 10516 = 171597",()=>{
 const b=bridge.official_baseline_2026_2027;
 assert.equal(b.portfolio_expenditures_mcad+b.debt_service_mcad,b.total_expenditures_mcad);
});
test("solde comptable -5208; solde budgétaire -7690",()=>{
 const b=bridge.official_baseline_2026_2027;
 assert.equal(b.total_revenue_mcad-b.total_expenditures_mcad-b.contingency_reserve_mcad,-5208);
 assert.equal(b.accounting_balance_mcad-b.generations_fund_deposits_mcad,-7690);
});
test("sensibilité figée et hypothétique seulement",()=>{
 const e=bridge.revenue_exposure_illustration;
 assert.equal(e.total_at_risk_mcad,41521);
 assert.equal(e.frozen_budgetary_balance_mcad,-49211);
 assert.equal(e.mechanical_zero_gap_mcad,49211);
 assert.equal(e.nova_policy_decided,false);
});
test("dix années par statut constitutionnel, toutes inconnues",()=>{
 assert.deepEqual(bridge.scenarios.map(x=>x.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"]);
 assert.ok(bridge.scenarios.every(x=>x.annual.length===10));
 assert.ok(bridge.scenarios.every(x=>x.annual.every(y=>y.net_balance_mcad===null)));
});
test("protection de 8 catégories de services et droits en attente",()=>{
 assert.equal(bridge.continuity.length,8);
 assert.ok(bridge.continuity.every(x=>x.assured_financing_mcad===null&&x.legal_review_done===false));
});
test("assiette 2021 fictivement changée",()=>{
 const d=copy();d.historic_and_forecast_ledger[1].amount_mcad=111111;
 assert.ok(inspect(d).errors.includes("HISTORIC_LEDGER_MISMATCH"));
});
test("2011 ou 2026 substituée à 2021",()=>{
 const d=copy();d.historic_and_forecast_ledger[1].year=2026;
 assert.ok(inspect(d).errors.includes("HISTORIC_LEDGER_MISMATCH"));
});
test("mélange illégal de type de revenu",()=>{
 const d=copy();d.historic_and_forecast_ledger[2].type="ASSIETTE_IMPOSABLE";
 assert.ok(inspect(d).errors.includes("HISTORIC_LEDGER_MISMATCH"));
});
test("un transfert fédéral inventé est détecté",()=>{
 const d=copy();d.official_baseline_2026_2027.federal_transfers_mcad=40000;
 assert.ok(inspect(d).errors.includes("BUDGET_BASELINE_MISMATCH"));
});
test("une fausse amélioration du déficit est refusée",()=>{
 const d=copy();d.official_baseline_2026_2027.budgetary_balance_mcad=-100;
 assert.ok(inspect(d).errors.includes("BUDGET_BASELINE_MISMATCH"));
});
test("une suppression supplémentaire de TVQ/FSS change le stress et est rejetée",()=>{
 const d=copy();d.revenue_exposure_illustration.total_at_risk_mcad=50000;
 assert.ok(inspect(d).errors.includes("EXPOSURE_NOT_A_FORECAST"));
});
test("un stress mathématique n'est pas un budget Nova certifié",()=>{
 const d=copy();d.revenue_exposure_illustration.status="BUDGET_NOVA_CERTIFIE";
 assert.ok(inspect(d).errors.includes("EXPOSURE_NOT_A_FORECAST"));
});
test("un régime social ne peut disparaître discrètement",()=>{
 const d=copy();d.continuity.pop();
 assert.ok(inspect(d).errors.includes("SOCIAL_CONTINUITY_UNVERIFIED"));
});
test("la continuité FSS ne peut être présumée financée",()=>{
 const d=copy();d.continuity.find(x=>x.code==="FSS").assured_financing_mcad=10000;
 assert.ok(inspect(d).errors.includes("SOCIAL_CONTINUITY_UNVERIFIED"));
});
test("un scénario souverain n'hérite pas automatiquement des transferts",()=>{
 const d=copy();d.scenarios[1].federal_transfers_assumed_retained=true;
 assert.ok(inspect(d).errors.includes("UNPROVEN_10_YEAR_BUDGET"));
});
test("un budget Nova non audité est refusé",()=>{
 const d=copy();d.scenarios[0].annual[0].net_balance_mcad=18000;
 assert.ok(inspect(d).errors.includes("UNPROVEN_10_YEAR_BUDGET"));
});
test("une année fiscale fantaisiste est refusée",()=>{
 const d=copy();d.scenarios[0].annual[7].year="2040-2041";
 assert.ok(inspect(d).errors.includes("UNPROVEN_10_YEAR_BUDGET"));
});
test("15 preuves G0.15 restent requises",()=>{
 const d=copy();d.required_g015_evidence_ids.pop();
 assert.ok(inspect(d).errors.includes("EVIDENCE_GATES_INCOMPLETE"));
});
test("une économie gouvernementale déclarée réelle est rejetée",()=>{
 const d=copy();d.decision.actual_savings_verified=true;
 assert.ok(inspect(d).errors.includes("PREMATURE_APPROVAL"));
});
test("passage fictif de 47 à 48 est refusé",()=>{
 const d=copy();d.programme_score_after=48;
 assert.ok(inspect(d).errors.includes("FALSE_PROGRAMME_STATUS"));
});
test("source G0.15 non indépendante reste non validée",()=>{
 const d=structuredClone(g15);d.proofs[0].status="REVUE_INDEPENDANTE";
 assert.ok(verifyG016eBridge(bridge,corp,personal,g14,d).errors.includes("PREDECESSOR_EVIDENCE_INVALID"));
});

test("la page G0.16e affiche les soldes et les avertissements",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/id="pont-financier-g016e"/);
 assert.match(html,/168,4 G\$/);
 assert.match(html,/−7,69 G\$/);
 assert.match(html,/−49 211 M\$/);
 assert.match(html,/pas d'une projection de la réforme Nova/);
 assert.match(html,/0 sur 15 exigences fiscales/);
 assert.match(html,/47 %/);
});
