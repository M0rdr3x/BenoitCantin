import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG015V10MunicipalTVQ2027,SOURCE_V10_2027}
  from "../assets/g015-v10-municipal-tvq-core.mjs";

const load=async path=>JSON.parse(await readFile(
  new URL("../data/"+path,import.meta.url),"utf8"));
const [data,discovery,proofs,municipal]=await Promise.all([
  load("transfert-tvq-municipal-g0-15-v10-2027.json"),
  load("reperage-sources-officielles-g0-15-2026-11-07.json"),
  load("matrice-preuves-g0-15-fiscalite.json"),
  load("finances-municipales-g0-16h-2024.json")
]);
const inspect=(x,y=discovery,p=proofs,m=municipal)=>
  inspectG015V10MunicipalTVQ2027(x,y,p,m);
const mutation=(change,code)=>{
  const x=structuredClone(data);change(x);
  const result=inspect(x);
  assert.equal(result.ok,false);
  assert.ok(result.errors.includes(code),result.errors.join(","));
};

test("2027 : enveloppe officielle TVQ 821 M$ et programme 47/100 inchangé",()=>{
  const result=inspect(data);
  assert.equal(result.ok,true,result.errors.join(","));
  assert.equal(result.declared_tvq_growth_transfer_2027_mcad,821);
  assert.equal(result.programme_score,47);
  assert.equal(result.confirmed_new_nova_revenue_mcad,null);
  assert.equal(result.v10_independently_validated,false);
});

test("répartition 2027 : 93,5 % et 6,5 % de l'enveloppe, sans montants par volet certifiés",()=>{
  const a=data.announced_allocation;
  assert.equal(a.component_I_share_pct+a.component_II_share_pct,100);
  assert.equal(a.component_amounts_source_verified,false);
  assert.equal(a.payments_reconciled,false);
  assert.equal(a.amount_is_estimate,true);
});

test("le programme n'additionne pas 821 M$ aux revenus fiscaux NOVA",()=>{
  assert.equal(data.budget_treatment.government_origin,"EXISTING_TVQ_GROWTH");
  assert.equal(data.budget_treatment.flow,"INTERGOVERNMENTAL_TRANSFER");
  assert.equal(data.budget_treatment.add_to_provincial_revenues,false);
  assert.equal(data.missing_evidence.additional_nova_revenue_mcad,null);
  assert.equal(data.missing_evidence.municipal_tax_replacement_mcad,null);
});

test("les transferts 2024 municipaux sont déjà dans les recettes consolidées",()=>{
  const result=inspect(data);
  assert.equal(result.historic_municipal_transfers_2024_cad,5330360838);
  assert.equal(data.budget_treatment.add_to_2024_municipal_revenues,false);
  assert.equal(municipal.annual[0].year,2024);
  assert.equal(data.announced_allocation.reference_year,2027);
});

test("toute substitution de 821 M$ par un rendement de réforme échoue",()=>{
  mutation(x=>x.announced_allocation.allocations_are_nova_revenue=true,
    "ANNOUNCED_AMOUNT_OR_SCOPE");
  mutation(x=>x.missing_evidence.additional_nova_revenue_mcad=821,
    "UNFOUNDED_FINANCING_OR_REVIEW");
  mutation(x=>x.budget_treatment.add_to_provincial_revenues=true,
    "DOUBLE_COUNT_OR_TRANSFERS_MISCLASSIFIED");
});

test("un transfert 2027 ne peut augmenter les comptes observés de 2024",()=>{
  mutation(x=>x.budget_treatment.add_to_2024_municipal_revenues=true,
    "DOUBLE_COUNT_OR_TRANSFERS_MISCLASSIFIED");
  mutation(x=>x.announced_allocation.reference_year=2024,
    "ANNOUNCED_AMOUNT_OR_SCOPE");
});

test("le montant, la provenance et les parts ne peuvent être modifiés sans source",()=>{
  mutation(x=>x.announced_allocation.total_mcad=900,"ANNOUNCED_AMOUNT_OR_SCOPE");
  mutation(x=>x.announced_allocation.component_I_share_pct=90,
    "ANNOUNCED_AMOUNT_OR_SCOPE");
  mutation(x=>x.source.url="https://example.org/budget",
    "PUBLIC_SOURCE_INVALID");
  assert.equal(data.source.url,SOURCE_V10_2027);
});

test("versements non réalisés, statut fiscal non certifié",()=>{
  mutation(x=>x.budget_treatment.forecast_is_actual_payment=true,
    "DOUBLE_COUNT_OR_TRANSFERS_MISCLASSIFIED");
  mutation(x=>x.announced_allocation.payments_reconciled=true,
    "ANNOUNCED_AMOUNT_OR_SCOPE");
  mutation(x=>x.decisions.two_tax_policy_certified=true,"APPROVAL_INVENTED");
  mutation(x=>x.decisions.v10_independently_validated=true,"APPROVAL_INVENTED");
  mutation(x=>x.programme_score_after=100,"STATUS_OR_SCORE_UNSUPPORTED");
});

test("la consultation de page ne certifie pas les 15 preuves G0.15",()=>{
  const altered=structuredClone(proofs);
  altered.proofs.find(x=>x.id==="V10").reviewed_independently=true;
  assert.ok(inspect(data,discovery,altered).errors.includes("G015_V10_NOT_YET_VALIDATED"));
  const altered2=structuredClone(discovery);
  altered2.entries.find(x=>x.id==="V10").statut_preuve_g015="PASSED";
  assert.ok(inspect(data,altered2).errors.includes("G015_V10_NOT_YET_VALIDATED"));
});

test("pas de soustraction de taux municipaux sans preuve de continuité",()=>{
  mutation(x=>x.budget_treatment.replace_municipal_taxes_without_new_proof=true,
    "DOUBLE_COUNT_OR_TRANSFERS_MISCLASSIFIED");
  mutation(x=>x.missing_evidence.legal_continuity_review=true,
    "UNFOUNDED_FINANCING_OR_REVIEW");
  mutation(x=>x.decisions.programme_complete=true,"APPROVAL_INVENTED");
});

test("les soldes 2024 restent ceux du même périmètre de comptes",()=>{
  const altered=structuredClone(municipal);
  altered.annual[0].government_transfers_cad+=821000000;
  assert.ok(inspect(data,discovery,proofs,altered).errors.includes("MUNICIPAL_2024_CROSSCHECK"));
});

test("le site explique l'enveloppe 2027 et sa non-comptabilisation",async()=>{
  const html=await readFile(
    new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
  assert.match(html,/id="transfert-tvq-g015-v10"/);
  const start=html.indexOf('id="transfert-tvq-g015-v10"');
  const end=html.indexOf("</section>",start);
  const section=html.slice(start,end);
  assert.match(section,/821 M\$/);
  assert.match(section,/2027/);
  assert.match(section,/2024/);
  assert.match(section,/47 % inchangé/);
  assert.ok(section.includes(SOURCE_V10_2027));
});
