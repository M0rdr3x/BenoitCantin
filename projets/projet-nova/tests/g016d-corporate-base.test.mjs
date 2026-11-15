import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectG016dCompanies} from "../assets/g016d-corporate-base-core.mjs";
const fetchJson=name=>readFile(new URL("../data/"+name,import.meta.url),"utf8").then(JSON.parse);
const [data,g15,personal]=await Promise.all([
 fetchJson("assiette-societes-g0-16d-2021.json"),
 fetchJson("matrice-preuves-g0-15-fiscalite.json"),
 fetchJson("assiette-fiscale-particuliers-g0-16c-2023.json")
]);
const cp=x=>structuredClone(x);
const check=x=>inspectG016dCompanies(x,g15,personal);
test("source ministérielle 2021, taux Nova inconnus et score 47",()=>{
 const x=check(data);
 assert.equal(x.ok,true,x.errors.join(","));
 assert.equal(x.year,2021);assert.equal(x.programme_score,47);
 assert.equal(x.corporate_taxable_income_mcad,95784);
 assert.equal(x.rates_approved,false);
});
test("assiettes distinctes de 95784 M$ imposables et 155850 M$ de salaires FSS",()=>{
 assert.equal(data.corporate_tax_base.quebec_taxable_income_mcad,95784);
 assert.equal(data.corporate_tax_base.payroll_subject_to_fss_mcad,155850);
 assert.equal(data.cross_year_guardrails.taxable_income_quebec_vs_fss_payroll,"DIFFERENT_TAX_BASES");
});
test("10000 M$ d'impôt + 5327 M$ FSS = 15327 M$",()=>{
 const m=data.receipts;
 assert.equal(m.quebec_corporate_income_tax_mcad+m.health_services_fund_contributions_mcad,m.gross_income_tax_and_fss_mcad);
 assert.equal(m.gross_income_tax_and_fss_mcad,15327);
});
test("le total net affiché peut différer d'une unité par arrondi",()=>{
 const m=data.receipts;
 assert.equal(m.gross_income_tax_and_fss_mcad-m.tax_credits_mcad,12859);
 assert.equal(m.net_after_credits_mcad,12860);
 assert.equal(m.rounding_tolerance_mcad,1);
});
test("542249 + 14858 + 7492 = 564599 sociétés déclarantes",()=>{
 const p=data.population;
 assert.equal(p.small_company_returns+p.medium_company_returns+p.large_company_returns,p.total_company_returns);
});
test("les impôts et FSS des trois tailles se réconcilient",()=>{
 assert.equal(data.sizes.reduce((s,x)=>s+x.income_tax_mcad,0),10000);
 assert.equal(data.sizes.reduce((s,x)=>s+x.fss_mcad,0),5327);
 assert.equal(data.sizes.reduce((s,x)=>s+x.combined_mcad,0),15327);
});
test("les sociétés sans impôt et sans cotisation ne sont pas toutes les mêmes",()=>{
 assert.equal(data.population.company_returns_without_income_tax,322020);
 assert.equal(data.population.company_returns_without_income_tax_or_fss,239628);
});
test("un montant d'assiette inventé est refusé",()=>{
 const d=cp(data);d.corporate_tax_base.quebec_taxable_income_mcad=125000;
 assert.ok(check(d).errors.includes("TAX_BASES_MISREPRESENTED"));
});
test("une estimation mondiale inventée comme base québécoise est refusée",()=>{
 const d=cp(data);d.corporate_tax_base.worldwide_taxable_income_mcad=200000;
 assert.ok(check(d).errors.includes("TAX_BASES_MISREPRESENTED"));
});
test("une baisse des cotisations FSS fausse est refusée",()=>{
 const d=cp(data);d.receipts.health_services_fund_contributions_mcad=0;
 assert.ok(check(d).errors.includes("TAX_AND_FSS_RECONCILIATION"));
});
test("la modification de la répartition par taille est détectée",()=>{
 const d=cp(data);d.sizes[2].combined_mcad=9000;
 assert.ok(check(d).errors.includes("SIZE_DISTRIBUTION_ALTERED"));
});
test("les recettes fiscales 2021 ne sont pas celles prévues en 2026-2027",()=>{
 const d=cp(data);d.cross_year_guardrails["2021_corporate_returns_vs_2026_2027_approved_revenues"]="COMPARABLE";
 assert.ok(check(d).errors.includes("BAD_PERIOD_OR_JURISDICTION"));
});
test("les chiffres ARC ne sont pas déclarés impôt provincial du Québec",()=>{
 const d=cp(data);d.other_primary_source_context.imported=true;
 assert.ok(check(d).errors.includes("FEDERAL_IS_NOT_QUEBEC_TAX"));
});
test("la publication d'une source ne valide aucune preuve G0.15",()=>{
 const d=cp(g15);d.proofs.find(x=>x.id==="V06").status="REVUE_INDEPENDANTE";
 assert.ok(inspectG016dCompanies(data,d,personal).errors.includes("G015_NOT_VERIFIED"));
});
test("les statistiques 2023 des particuliers sont d'un autre millésime",()=>{
 const d=cp(personal);d.source_year=2021;
 assert.ok(inspectG016dCompanies(data,g15,d).errors.includes("G016C_NOT_VERIFIED"));
});
test("aucun impôt unique Nova ne peut être fixé à partir de 2021",()=>{
 const d=cp(data);d.unknown_nova.corporate_rate_percent=19;
 assert.ok(check(d).errors.includes("INVENTED_NOVA_OUTCOME"));
});
test("la continuité du FSS reste à financer",()=>{
 const d=cp(data);d.unknown_nova.fss_continuity_financed_mcad=5327;
 assert.ok(check(d).errors.includes("INVENTED_NOVA_OUTCOME"));
});
test("le score ne passe pas à 48 sans preuve indépendante",()=>{
 const d=cp(data);d.decision.programme_pct_after=48;
 assert.ok(check(d).errors.includes("INVENTED_NOVA_OUTCOME"));
});
test("une revue indépendante ne peut être annoncée sans avoir eu lieu",()=>{
 const d=cp(data);d.source.independent_reviewer_signed=true;
 assert.ok(check(d).errors.includes("SOURCE_INCORRECTE"));
});
test("les sources déformées sont rejetées",()=>{
 const d=cp(data);d.source.url="https://not-official.example.org";
 assert.ok(check(d).errors.includes("SOURCE_INCORRECTE"));
});

test("la page publique présente G0.16d et refuse un taux inventé",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/id="societes-g016d"/);
 assert.match(html,/95,8 G\$/);
 assert.match(html,/155,9 G\$/);
 assert.match(html,/2021 \(sociétés\), 2023 \(particuliers\)/);
 assert.match(html,/0 sur 15 preuves fiscales indépendamment validées/);
 assert.match(html,/score 47 % inchangé/);
});
