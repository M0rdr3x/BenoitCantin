// Projet Nova G0.14 — contrôle fiscal documentaire; aucun financement certifié.
export function verifyG14(doc,baseline) {
 const errors=[];
 if (!doc || doc.schema!=="nova-g014-assiettes-fiscales/v1" || !Array.isArray(doc.revenue_categories) || !baseline) return {ok:false,errors:["SCHEMA"]};
 const cats=doc.revenue_categories;
 if(cats.length!==9 || new Set(cats.map(x=>x.id)).size!==9)errors.push("CATEGORIES");
 const total=cats.reduce((s,x)=>s+x.amount_mcad,0);
 const federal=cats.find(x=>x.id==="TRANSFERTS_FEDERAUX")?.amount_mcad;
 if(total!==168389||federal!==33046||total-federal!==135343)errors.push("SOURCE_TOTALS");
 const ref=baseline.five_year_income_components_2026_2027;
 const links={IMPOT_PARTICULIERS:"personal_income_tax",IMPOTS_SOCIETES:"corporate_taxes",COTISATIONS_SANTE:"health_services_contributions",FONCIER_SCOLAIRE:"school_property_tax",TAXES_CONSOMMATION:"consumption_taxes",DROITS_PERMIS_REDEVANCES:"duties_licenses_royalties",REVENUS_DIVERS:"miscellaneous_revenue",SOCIETES_ETAT:"government_enterprises",TRANSFERTS_FEDERAUX:"federal_transfers"};
 if(cats.some(x=>!Number.isSafeInteger(x.amount_mcad)||x.amount_mcad<0||ref[links[x.id]]!==x.amount_mcad))errors.push("BASELINE_MAPPING");
 const b=doc.baseline;
 if(b.total_revenue!==168389||b.total_expenditures!==171597||b.contingency_reserve!==2000||b.accounting_balance!==-5208||b.budgetary_balance!==-7690||b.accounting_balance-b.generations_fund_deposits!==b.budgetary_balance)errors.push("BALANCE");
 const exposure=cats.filter(x=>["COTISATIONS_SANTE","FONCIER_SCOLAIRE","TAXES_CONSOMMATION"].includes(x.id)).reduce((s,x)=>s+x.amount_mcad,0);
 const s=doc.mechanical_sensitivity;
 if(exposure!==41521||s.removed_baseline_receipts!==exposure||s.post_removal_revenues_before_any_new_tax_income!==168389-exposure||s.mechanical_budgetary_balance_without_replacement!==-7690-exposure||s.mechanical_accounting_balance_without_replacement!==-5208-exposure||s.net_adjustment_needed_to_reach_zero_budgetary_balance!==7690+exposure||s.forecast_balance_nova!==null||s.type!=="ARITHMETIQUE_FIGEE_HYPOTHETIQUE_NON_PREVISION")errors.push("STRESS_MATH");
 if(doc.jurisdiction_separation.length!==6||doc.jurisdiction_separation.some(x=>x.amount_mcad!==null)||doc.constitutional_scenarios.length!==2||doc.constitutional_scenarios.some(x=>x.budget_balance!==null||x.net_anti_haven_revenue!==null)||doc.constitutional_scenarios.find(x=>x.id==="QUEBEC_SOUVERAIN")?.baseline_federal_transfers_2026_2027!==null)errors.push("COMPETENCE");
 if(doc.tax_design_constraints.income_tax_rate_percent!==null||doc.tax_design_constraints.offshore_revenue_incremental_after_overlap!==null||doc.programme_percent_before!==47||doc.programme_percent_after!==47||doc.decision.g0_passed!==false||doc.decision.nova_budget_certified!==false)errors.push("UNVERIFIED_CLAIMS");
 const required=Object.keys(links);
 if(required.some(id=>!cats.some(x=>x.id===id)) || cats.some(x=>!required.includes(x.id)))errors.push("MISSING_REVENUE_CATEGORY");
 if(doc.reconciliation.income_tax_legal_base_defined!==false||doc.reconciliation.other_revenues_are_not_all_taxes!==true||doc.reconciliation.income_related_category_total_illustrative!==65640)errors.push("MISCLASSIFIED_INCOME_BASE");
 const ids=doc.jurisdiction_separation.map(x=>x.id);
 if(new Set(ids).size!==6||!["FEDERAL_TAXES","MUNICIPAL_TAXES","RRQ","RQAP","ASSURANCE_MEDICAMENTS","PARADIS_FISCAUX"].every(id=>ids.includes(id)))errors.push("JURISDICTIONS_INCOMPLETE");
 const removed=s.removed_category_ids;
 if(removed.length!==3||new Set(removed).size!==3||!["COTISATIONS_SANTE","FONCIER_SCOLAIRE","TAXES_CONSOMMATION"].every(id=>removed.includes(id)))errors.push("EXPOSURE_SCOPE_ALTERED");
 if(s.replacement_or_real_savings_needed_to_reach_official_baseline_balance!==41521||s.remaining_mixed_duties_not_removed!==6484||s.public_service_continuity_verified!==false||!Array.isArray(s.caveats)||s.caveats.length<4)errors.push("ILLUSTRATION_NOT_LABELED");
 const sovereign=doc.constitutional_scenarios.find(x=>x.id==="QUEBEC_SOUVERAIN");
 const province=doc.constitutional_scenarios.find(x=>x.id==="QUEBEC_CANADA");
 if(!sovereign||!province||new Set(doc.constitutional_scenarios.map(x=>x.id)).size!==2||province.baseline_federal_transfers_2026_2027!==33046||[sovereign,province].some(x=>x.new_income_tax_revenue!==null||x.other_receipts_retained!==null||x.jurisdiction_verified!==false))errors.push("UNPROVEN_SCENARIO_RECEIPTS");
 if(!Array.isArray(doc.research_next)||doc.research_next.length<7||doc.research_next.some(x=>x.status!=="NON_ETABLI"))errors.push("UNVERIFIED_RESEARCH_RECORDED_AS_DONE");
 if(doc.tax_design_constraints.no_unfunded_tax_abolitions!==true||doc.tax_design_constraints.no_counter_tariffs_commitment!==true||doc.tax_design_constraints.personal_and_corporate_tax_bases_validated!==false||doc.tax_design_constraints.offshore_measure_legal_authority_reviewed!==false||doc.decision.anti_tax_haven_yield_certified!==false||doc.decision.programme_ready_for_government!==false||doc.decision.independent_legal_review_done!==false)errors.push("PREMATURE_LEGAL_OR_FISCAL_CLAIMS");
 return {ok:errors.length===0,errors,amount_reconciled:total,exposure_mcad:exposure,mechanical_gap_to_zero_mcad:7690+exposure,programme_percent:47,proposal_funded:false,g0_passed:false};
}
