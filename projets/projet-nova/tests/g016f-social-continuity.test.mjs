import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {verifyG016fSocialContinuity} from "../assets/g016f-social-continuity-core.mjs";
const read=async name=>JSON.parse(await readFile(new URL("../data/"+name,import.meta.url),"utf8"));
const [data,g15,g16e,g14]=await Promise.all([
 read("continuite-regimes-g0-16f-2024-2026.json"),
 read("matrice-preuves-g0-15-fiscalite.json"),
 read("pont-financier-g0-16e-2021-2026.json"),
 read("registre-assiettes-fiscales-g0-14-2026-2027.json")
]);
const copy=()=>structuredClone(data);
const verify=d=>verifyG016fSocialContinuity(d,g15,g16e,g14);
test("G0.16f référence sept pages primaires; 47 %, aucune réforme certifiée",()=>{
 const r=verify(data);assert.equal(r.ok,true,r.errors.join("|"));
 assert.equal(r.primary_pages_cited,7);
 assert.equal(r.programme_percent,47);
 assert.equal(r.can_remove_fss,false);
});
test("RRQ 2026 : exemption et tranches de cotisation",()=>{
 const x=data.rrq;
 assert.equal(x.contribution_exemption_cad,3500);
 assert.equal(x.maximum_pensionable_earnings_cad,74600);
 assert.equal(x.additional_maximum_pensionable_earnings_cad,85000);
 assert.equal(x.employee_first_bracket_pct,6.3);
 assert.equal(x.employee_second_bracket_pct,4);
});
test("RRQ marge actuarielle spéciale 0,12 et non 0,33 point",()=>{
 const x=data.rrq;
 assert.equal(x.actuarial_base_contribution_rate_total_pct-x.actuarial_base_required_rate_pct,0.11999999999999922);
 assert.equal(x.actuarial_base_margin_pct_points,0.12);
 assert.equal(x.independent_actuary_nova_review,false);
});
test("RQAP 2026 : trois taux et transfert au 1er mai",()=>{
 const x=data.rqap;
 assert.deepEqual([x.employee_rate_pct,x.employer_rate_pct,x.self_employed_rate_pct],[0.430,0.602,0.764]);
 assert.equal(x.roles_transferred_effective,"2026-05-01");
 assert.equal(x.fund_character,"FONDS_FIDUCIAIRE_NON_BUDGETAIRE");
});
test("RAMQ 2024-2025 : source FSS, médicaments et autres séparés",()=>{
 const x=data.ramq.financing_mcad;
 assert.equal(x.fss,8937);assert.equal(x.drug_insurance_fund,4354);
 assert.equal(x.other,1250);assert.equal(x.published_total,14542);
 assert.equal(Math.abs(x.fss+x.drug_insurance_fund+x.other-x.published_total),1);
});
test("RAMQ 2024-2025 : les coûts des programmes 14232 se rapprochent",()=>{
 const x=data.ramq.program_cost_mcad;
 assert.equal(x.physician_remuneration+x.pharmacy_drugs_services+x.other,x.published_total);
 assert.equal(x.published_total,14232);
});
test("RAMQ ≠ toutes les dépenses de santé du Québec",()=>{
 assert.equal(data.ramq.scope,"RAMQ_ADMINISTERED_PROGRAMS_NOT_WHOLE_HEALTH_SYSTEM");
 assert.equal(data.health_system.do_not_sum_with_ramq_total,true);
 assert.equal(data.health_system.values_approximate,true);
});
test("RAMQ 2024-2025 et budget FSS 2026-2027 ne sont pas le même montant",()=>{
 assert.equal(data.ramq.financing_mcad.fss,8937);
 assert.equal(data.cross_year_reference.fss_revenue_2026_2027_mcad,9538);
 assert.equal(data.cross_year_reference.not_equivalent_to_ramq_fss_financing_2024_2025,true);
});
test("source RRQ ou mandat modifié refusé",()=>{
 const d=copy();d.sources[0].url="https://example.org";assert.ok(verify(d).errors.includes("SOURCE_PROVENANCE"));
});
test("un taux de RRQ inventé est refusé",()=>{
 const d=copy();d.rrq.employee_first_bracket_pct=5;
 assert.ok(verify(d).errors.includes("RRQ_RATES_ACTUARIAL_OR_RIGHTS"));
});
test("une marge actuarielle améliorée fictivement est refusée",()=>{
 const d=copy();d.rrq.actuarial_base_margin_pct_points=3.3;
 assert.ok(verify(d).errors.includes("RRQ_RATES_ACTUARIAL_OR_RIGHTS"));
});
test("une suppression RRQ prétendument financée est refusée",()=>{
 const d=copy();d.rrq.replacement_financing_mcad=20000;
 assert.ok(verify(d).errors.includes("RRQ_RATES_ACTUARIAL_OR_RIGHTS"));
});
test("RQAP n'est pas une recette fiscale libre à redistribuer",()=>{
 const d=copy();d.rqap.fund_character="RECETTE_GENERALE";
 assert.ok(verify(d).errors.includes("RQAP_FUND_AND_TRANSFER"));
});
test("l'ancienne responsabilité du Conseil ne peut être présumée actuelle",()=>{
 const d=copy();d.rqap.roles_transferred_to="Conseil de gestion";
 assert.ok(verify(d).errors.includes("RQAP_FUND_AND_TRANSFER"));
});
test("le financement RAMQ ne devient pas un budget de tout le réseau",()=>{
 const d=copy();d.ramq.scope="SANTE_TOTALE";
 assert.ok(verify(d).errors.includes("RAMQ_SCOPE_OR_RECONCILIATION"));
});
test("pas de pseudo-surplus automatique entre financement et coûts RAMQ",()=>{
 const d=copy();d.ramq.difference_financing_costs_not_identified_as_surplus=false;
 assert.ok(verify(d).errors.includes("RAMQ_SCOPE_OR_RECONCILIATION"));
});
test("les 81 G$ des dépenses totales ne s'ajoutent pas aux budgets RAMQ",()=>{
 const d=copy();d.health_system.do_not_sum_with_ramq_total=false;
 assert.ok(verify(d).errors.includes("HEALTH_SYSTEM_DOUBLE_COUNT"));
});
test("FSS 9538 M$ 2026-2027 ne devient pas 8937 M$ 2024-2025",()=>{
 const d=copy();d.cross_year_reference.fss_revenue_2026_2027_mcad=8937;
 assert.ok(verify(d).errors.includes("FSS_MILLENNIUM_MISMATCH"));
});
test("V07 à V09 n'ont pas été validées indépendamment",()=>{
 const x=structuredClone(g15);x.proofs.find(p=>p.id==="V09").status="REVUE_INDEPENDANTE";
 assert.ok(verifyG016fSocialContinuity(data,x,g16e,g14).errors.includes("UNPASSED_SOURCE_PROOFS"));
});
test("une certification artificielle est rejetée",()=>{
 const d=copy();d.decision.all_health_services_financed=true;
 assert.ok(verify(d).errors.includes("FICTIONAL_AUTHORIZATION"));
});
test("le 47 % ne grimpe pas à 48 avec des sources seulement",()=>{
 const d=copy();d.programme_percent_after=48;
 assert.ok(verify(d).errors.includes("UNVERIFIED_STAGE"));
});
test("les droits et obligations non démontrés demeurent inconnus",()=>{
 assert.equal(data.rrq.rights_maintained_under_nova,null);
 assert.equal(data.ramq.costs_covered_after_nova_tax_reform,null);
 assert.equal(data.decision.g016f_completed,false);
});
