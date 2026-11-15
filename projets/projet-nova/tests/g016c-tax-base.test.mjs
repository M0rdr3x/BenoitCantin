import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {validateG016cTaxBase} from "../assets/g016c-tax-base-core.mjs";
const base=new URL("../data/",import.meta.url);
const data=JSON.parse(await readFile(new URL("assiette-fiscale-particuliers-g0-16c-2023.json",base),"utf8"));
const g15=JSON.parse(await readFile(new URL("matrice-preuves-g0-15-fiscalite.json",base),"utf8"));
const g16b=JSON.parse(await readFile(new URL("reperes-publics-g0-16b-2023.json",base),"utf8"));
const clone=x=>structuredClone(x);
const check=x=>validateG016cTaxBase(x,g15,g16b);

test("2023 : montants officiels et 47 % sans réforme calibrée",()=>{
 const r=check(data);assert.equal(r.ok,true,r.errors.join("|"));
 assert.equal(r.historical_taxable_income_mcad,372261);
 assert.equal(r.eligible_for_policy_simulation,false);
 assert.equal(r.programme_percent,47);
});
test("7 220 140 déclarants se répartissent exactement",()=>{
 const t=data.taxpayer_counts;
 assert.equal(t.all_returns,7220140);
 assert.equal(t.taxable_returns+t.nontaxable_returns,t.all_returns);
});
test("revenu total 427915 M$ et revenu net 387023 M$",()=>{
 const a=data.tax_return_aggregates_mcad;
 assert.equal(a.total_declared_income-a.net_income_deductions,a.net_income);
 assert.equal(a.net_income,387023);
});
test("revenu imposable 372261 M$ : arrondi à 1 M$ admis",()=>{
 const a=data.tax_return_aggregates_mcad;
 assert.equal(Math.abs(a.net_income-a.taxable_income_deductions-a.taxable_income),1);
 assert.equal(a.taxable_income,372261);
});
test("impôt dû et remboursements ne sont pas des recettes budgétaires Nova",()=>{
 const a=data.tax_return_aggregates_mcad;
 assert.equal(a.tax_on_taxable_income-a.nonrefundable_credits_applied,a.income_tax_payable);
 assert.equal(a.income_tax_payable-a.refundable_credits_applied,a.income_tax_payable_less_refundable_credits);
 assert.equal(a.income_tax_payable_less_refundable_credits,31485);
 assert.equal(data.comparison_constraints.is_projected_2026_2027_tax_revenue,false);
});
test("les quintiles des contribuables ne sont pas les déciles des ménages",()=>{
 const qs=data.quintiles_of_tax_filers_by_total_income;
 assert.equal(qs.length,5);
 assert.ok(Math.abs(qs.reduce((s,x)=>s+x.income_share_pct,0)-100)<.02);
 assert.ok(Math.abs(qs.reduce((s,x)=>s+x.tax_payable_share_pct,0)-100)<.02);
 assert.equal(data.comparison_constraints.five_quintiles_not_ten_household_deciles,true);
});
test("69,41 % d'impôt payable relève du 5e quintile de revenu total",()=>{
 assert.equal(data.quintiles_of_tax_filers_by_total_income[4].tax_payable_share_pct,69.41);
 assert.equal(data.quintiles_of_tax_filers_by_total_income[4].income_share_pct,50.10);
});
test("un faux taux de réforme est refusé",()=>{
 const d=clone(data);d.unverified.new_income_tax_rate_pct=21;
 assert.ok(check(d).errors.includes("INVENTED_POLICY_OUTCOME"));
});
test("un budget Nova fictif est refusé",()=>{
 const d=clone(data);d.unverified.revenue_nova_mcad=40000;
 assert.ok(check(d).errors.includes("INVENTED_POLICY_OUTCOME"));
});
test("taux moyen officiel modifié sans preuve est refusé",()=>{
 const d=clone(data);d.reported_mean_tax_rate_percent=12.7;
 assert.ok(check(d).errors.includes("FISCAL_RECONCILIATION"));
});
test("un revenu imposable artificiellement modifié est refusé",()=>{
 const d=clone(data);d.tax_return_aggregates_mcad.taxable_income=480000;
 assert.ok(check(d).errors.includes("ALTERED_TAX_AGGREGATES"));
});
test("étiquette de 2026 ou source substituée est rejetée",()=>{
 const d=clone(data);d.source_year=2026;
 assert.ok(check(d).errors.includes("UNSUPPORTED_STATUS"));
 const e=clone(data);e.sources[0].url="https://example.org/fiscal";
 assert.ok(check(e).errors.includes("UNVERIFIED_PROVENANCE"));
});
test("les quintiles ne peuvent être déplacés ou gonflés",()=>{
 const d=clone(data);d.quintiles_of_tax_filers_by_total_income[4].tax_payable_share_pct=76;
 assert.ok(check(d).errors.includes("QUINTILE_SOURCE_ALTERED"));
});
test("les comptes de déclarations non imposables doivent être conservés",()=>{
 const d=clone(data);d.taxpayer_counts.nontaxable_returns=0;
 assert.ok(check(d).errors.includes("TAXPAYER_COUNTS"));
});
test("une donnée sur les entreprises ne peut être inventée",()=>{
 const d=clone(data);d.unverified.corporate_tax_base_mcad=125000;
 assert.ok(check(d).errors.includes("INVENTED_POLICY_OUTCOME"));
});
test("G0.15 : les quinze preuves indépendantes ne sont pas acquises",()=>{
 const d=clone(g15);d.proofs[0].status="REVUE_INDEPENDANTE";
 assert.ok(validateG016cTaxBase(data,d,g16b).errors.includes("G015_NOT_PASSED"));
});
test("G0.16b : aucune calibration ou nouvelle assiette fictive",()=>{
 const d=clone(g16b);d.approved_for_microsimulation=true;
 assert.ok(validateG016cTaxBase(data,g15,d).errors.includes("G016B_MISMATCH"));
});
test("une nouvelle norme n'augmente pas artificiellement le score",()=>{
 const d=clone(data);d.decision.programme_pct_after=48;
 assert.ok(check(d).errors.includes("INVENTED_POLICY_OUTCOME"));
});
test("aucune dépense par décile attribuée artificiellement",()=>{
 const d=clone(data);d.comparison_constraints.cannot_join_with_statcan_average_expenses=false;
 assert.ok(check(d).errors.includes("FISCAL_SCOPE_MISREPRESENTED"));
});
test("une source corrompue échoue sans créer de gain de fiscalité",()=>{
 const d=clone(data);d.sources[0]=null;
 const r=check(d);assert.equal(r.ok,false);
 assert.equal(r.new_nova_tax_rate,null);
});

test("la page publique conserve le 47 % et décrit les grandeurs fiscales 2023",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/id="assiette-g016c"/);
 assert.match(html,/372,3 G\$/);
 assert.match(html,/40,8 G\$/);
 assert.match(html,/7,22 M/);
 assert.match(html,/ne correspondent pas aux/);
 assert.match(html,/Le score du projet reste à <strong>47 %<\/strong>/);
 assert.match(html,/Aucune simulation Nova réalisée/);
});
