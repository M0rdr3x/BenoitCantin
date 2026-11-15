// Projet Nova G0.16j — validation des dépenses réelles MAMH 2024 et 2023.
// Ces valeurs observées ne constituent PAS un coût futur garanti ni une projection Nova.
export const OBSERVED_FUNCTIONS=Object.freeze([
 ["ADMIN",3441813458,3115734876],
 ["SECURITE",4510158652,4218784701],
 ["TRANSPORT",8699354143,8336293056],
 ["MILIEU",4178810239,3889761273],
 ["SANTE_BIEN_ETRE",599704334,519887878],
 ["AMENAGEMENT",1368707794,1236665107],
 ["LOISIRS_CULTURE",3813614056,3569750989],
 ["ELECTRICITE",409672407,398862206],
 ["FINANCEMENT",1332060734,1181427913],
 ["RESTRUCTURATION",13064005,1880806]
]);
export const OBSERVED_DETAILS=Object.freeze([
 ["POLICE","SECURITE",2769781797,2587664526],
 ["INCENDIE_PREMIERS_REPONDANTS","SECURITE",52861631,21029770],
 ["INCENDIE_AUTRES","SECURITE",1480250246,1418116899],
 ["SECURITE_CIVILE","SECURITE",79409647,78764232],
 ["SECURITE_AUTRES","SECURITE",127855331,113209274],
 ["VOIRIE","TRANSPORT",2551882022,2385469323],
 ["DENEIGEMENT","TRANSPORT",1159992215,1254057731],
 ["ECLAIRAGE_RUES","TRANSPORT",168759751,165711268],
 ["CIRCULATION_STATIONNEMENT","TRANSPORT",359607348,332660965],
 ["TRANSPORT_EN_COMMUN","TRANSPORT",4187478816,3951481215],
 ["TRANSPORT_AERIEN","TRANSPORT",34863926,34082448],
 ["TRANSPORT_PAR_EAU","TRANSPORT",12742609,9533192],
 ["TRANSPORT_AUTRES","TRANSPORT",224027456,203296914],
 ["EAU_PRODUCTION_TRAITEMENT","MILIEU",587281926,546634669],
 ["EAU_DISTRIBUTION","MILIEU",766770167,716850281],
 ["EAUX_USEES_TRAITEMENT","MILIEU",564654613,532890376],
 ["EGOUTS_RESEAUX","MILIEU",600720086,567450270],
 ["DECHETS_COLLECTE","MILIEU",367252365,337354509],
 ["DECHETS_ELIMINATION","MILIEU",332486829,304828031],
 ["RECYCLABLES_COLLECTE","MILIEU",233009434,215967254],
 ["RECYCLABLES_TRI","MILIEU",93884030,90652717],
 ["ORGANIQUES_COLLECTE","MILIEU",160884577,157866211],
 ["ORGANIQUES_TRAITEMENT","MILIEU",80526043,68077484],
 ["MATERIAUX_SECS","MILIEU",116921150,101632727],
 ["MATIERES_AUTRES","MILIEU",31070266,27119993],
 ["PLAN_GESTION","MILIEU",14588137,5973511],
 ["PLAN_AUTRES","MILIEU",26696517,17627292],
 ["COURS_EAU","MILIEU",19322370,15584475],
 ["PROTECTION_ENVIRONNEMENT","MILIEU",132671390,119152977],
 ["MILIEU_AUTRES","MILIEU",50070339,64098496],
 ["LOGEMENT_SOCIAL","SANTE_BIEN_ETRE",399545604,330884904],
 ["HABITATION_AUTRES","SANTE_BIEN_ETRE",46812442,52579056],
 ["SECURITE_REVENU","SANTE_BIEN_ETRE",9385555,10148706],
 ["BIEN_ETRE_AUTRES","SANTE_BIEN_ETRE",143960733,126275212]
]);
export const SUBSET_IDS=Object.freeze([
 ["EAU_EGOUTS",["EAU_PRODUCTION_TRAITEMENT","EAU_DISTRIBUTION","EAUX_USEES_TRAITEMENT","EGOUTS_RESEAUX"]],
 ["VOIRIE_DENEIGEMENT",["VOIRIE","DENEIGEMENT"]],
 ["INCENDIE",["INCENDIE_PREMIERS_REPONDANTS","INCENDIE_AUTRES"]]
]);
const FILE_URL="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/rapports_financiers_organismes_municipaux/2024/RAP_financier_2024_sommation_municipalites_locales.pdf";
const isObject=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const sum=(rows,key)=>rows.reduce((a,v)=>a+v[key],0);
const unknownCostFields=["municipal_service_cost_cad","local_tax_replacement_revenue_cad",
 "provincial_and_federal_transfer_net_cad","staff_and_pensions_cost_cad","net_balance_cad"];
export function inspectG016jServiceExpenses(data,h,i){
 const errors=[],bad=x=>errors.push(x);
 if(!isObject(data)||data.schema!=="nova-g016j-municipal-service-costs/v1"||
   !isObject(data.primary_pdf)||!isObject(data.reference_total)||!Array.isArray(data.functions)||
   !Array.isArray(data.details)||!Array.isArray(data.non_overlapping_observed_subsets)||
   !isObject(data.maturity)||!isObject(data.baseline_links)||
   !Array.isArray(data.service_continuity)||!Array.isArray(data.separate_scenarios)||
   !Array.isArray(data.conditions_for_next_gate)||!isObject(data.decision))
   return {ok:false,errors:["SCHEMA"],score:null};
 if(data.stage!=="G0.16j"||data.record_date!=="2026-11-07"||
    data.status!=="HISTORICAL_EXPENSE_RECONCILIATION_ONLY"||
    data.adopted!==false||data.score_before!==47||data.score_after!==47)
   bad("FALSE_PROGRAMME_STATUS");
 const pdf=data.primary_pdf;
 if(pdf.url!==FILE_URL||pdf.year!==2024||pdf.comparison_year!==2023||
    pdf.municipalities_count!==1056||pdf.non_exhaustive!==true||
    pdf.images_reviewed_by_analyst!==true||
    pdf.external_independent_reviewer_for_nova!==false||
    pdf.population_by_municipality_not_available!==true||
    pdf.municipal_level_records_imported!==false||
    pdf.comparison_perimeter_identical_years_not_proven!==true||
    !equal(pdf.pages,[
      {pdf_page_zero_based:7,printed_page:"S7 / 3",content:"État consolidé des résultats",section_detailed_not_audited:false},
      {pdf_page_zero_based:51,printed_page:"S28 / 47",content:"Analyse des charges consolidées — sécurité et transports",section_detailed_not_audited:true},
      {pdf_page_zero_based:52,printed_page:"S28 / 48",content:"Analyse des charges consolidées — hygiène et santé",section_detailed_not_audited:true}
    ]))bad("SOURCE_SCOPE_OR_AUDIT");
 if(data.functions.length!==OBSERVED_FUNCTIONS.length||
    data.functions.some((f,idx)=>!isObject(f)||
      !equal([f.id,f.y2024,f.y2023],OBSERVED_FUNCTIONS[idx])||
      f.already_in_total!==true)||
    sum(data.functions,"y2024")!==28366959822||
    sum(data.functions,"y2023")!==26469048805)
   bad("FUNCTION_EXPENSE_RECONCILIATION");
 if(data.details.length!==OBSERVED_DETAILS.length||
    data.details.some((d,j)=>!isObject(d)||
      !equal([d.id,d.group,d.y2024,d.y2023],OBSERVED_DETAILS[j])||
      d.parent_includes_this!==true||d.extra_future_financing_need!==null))
   bad("DETAIL_EXPENSE_PROVENANCE");
 const groups=["SECURITE","TRANSPORT","MILIEU","SANTE_BIEN_ETRE"];
 if(groups.some(id=>{
   const parent=data.functions.find(f=>f.id===id);
   const subset=data.details.filter(d=>d.group===id);
   return !parent||sum(subset,"y2024")!==parent.y2024||
     sum(subset,"y2023")!==parent.y2023;
 }))bad("DOUBLE_COUNTED_FUNCTIONS");
 if(data.non_overlapping_observed_subsets.length!==3||
    data.non_overlapping_observed_subsets.some((x,j)=>{
      const [id,members]=SUBSET_IDS[j];
      if(x?.id!==id||!equal(x.members,members)||
        x.extra_sum_on_function_expenses!==false)return true;
      const d=data.details.filter(v=>members.includes(v.id));
      return d.length!==members.length||
        x.y2024!==sum(d,"y2024")||x.y2023!==sum(d,"y2023");
    }))bad("PARTIAL_SERVICE_SUBTOTAL");
 const b=data.reference_total;
 if(!equal(b,{y2024:28366959822,y2023:26469048805,
   revenues2024:32109026468,financing_already_in_expenses2024:1332060734})||
   h?.schema!=="nova-g016h-finances-municipales-observees/v1"||
   h?.annual?.[0]?.total_expenses_cad!==b.y2024||
   h?.annual?.[1]?.total_expenses_cad!==b.y2023||
   h?.annual?.[0]?.total_revenues_cad!==b.revenues2024||
   h?.annual?.[0]?.financing_charges_cad!==b.financing_already_in_expenses2024||
   i?.schema!=="nova-g016i-local-tax-continuity-static/v1"||
   i?.fixed_2024_baseline?.total_expenses_cad!==b.y2024||
   i?.programme_score_after!==47)
   bad("PREDECESSOR_BASE_MISMATCH");
 const mat=data.maturity;
 const requiredTrue=["historic_functions_reconciled","selected_subgroups_reconciled",
  "historical_2023_2024_comparisons_are_not_inflation_adjusted",
  "source_excerpt_detail_non_audited","costs_not_automatically_avoidable_if_tax_removed",
  "taxes_school_federal_and_municipal_not_collapsed"];
 const requiredFalse=["covers_all_municipalities","annual_2025_financial_values_verified",
   "municipal_and_mrc_transfers_eliminated","expenditure_needs_2026_2036_financed",
   "costs_assignable_to_abolished_taxes","worker_rights_liabilities_verified",
   "independent_public_finance_review"];
 if(mat.expenditure_year!=="2024"||
   requiredTrue.some(k=>mat[k]!==true)||requiredFalse.some(k=>mat[k]!==false))
   bad("FICTITIOUS_SERVICE_CERTIFICATION");
 if(!equal(data.baseline_links,{
   g016h:"data/finances-municipales-g0-16h-2024.json",
   g016i:"data/risque-transition-taxes-locales-g0-16i-2024.json",
   from_g016h_reference_expenses_cad:28366959822,
   from_g016i_reference_expenses_cad:28366959822,
   double_count_transport_and_road:false,double_count_milieu_and_water:false,
   finance_charges_already_in_total:true,other_services_not_zero_cost:true
 }))bad("REFERENCE_ACCOUNTING_RULES");
 const expectedServices=["EAU_EGOUTS","VOIRIE_DENEIGEMENT","INCENDIE",
   "TRANSPORT_COLLECTIF","DECHETS","LOGEMENT_SOCIAL","ADMINISTRATION","AUTRES_ET_PENSIONS"];
 if(!equal(data.service_continuity.map(s=>s?.category),expectedServices)||
    data.service_continuity.some(s=>s.historical_2024_used_only_as_reference!==true||
      s.service_level_target_approved!==false||s.service_continuity_cost_per_year_cad!==null||
      s.replacement_funding_verified_cad!==null||
      s.workers_protection_legal_review!==false||s.regional_coverage_verified!==false))
   bad("SERVICE_CONTINUITY_NOT_FUNDED");
 if(!equal(data.separate_scenarios.map(s=>s?.id),["QUEBEC_CANADA","QUEBEC_SOUVERAIN"])||
    data.separate_scenarios.some(s=>s.competence_approved!==false||
      s.transfer_elimination_reviewed!==false||s.independent_budget_reviewed!==false||
      !Array.isArray(s.annual)||s.annual.length!==10||
      s.annual.some((a,k)=>a.year!==(2026+k)+"-"+(2027+k)||
        unknownCostFields.some(key=>a[key]!==null)||
        a.debt_financing_included_verified!==false||
        a.independent_validation!==false)))
   bad("PREMATURE_DECADAL_BUDGET");
 if(!equal(data.conditions_for_next_gate.map(x=>x?.key),["C01","C02","C03","C04","C05","C06"])||
    data.conditions_for_next_gate.some(x=>x.complete!==false||typeof x.label!=="string"))
   bad("CONDITIONS_FALSE_APPROVAL");
 const decision=data.decision;
 if(decision.g016j_documentary_reconciliation_completed!==true||
    ["g016j_financial_sustainability_passed","tax_removal_authorized",
      "all_municipalities_covered","ten_year_budgets_balanced","staff_rights_proven",
      "programme_ready"].some(k=>decision[k]!==false))
   bad("POLICY_PREMATURE");
 return {ok:errors.length===0,errors:[...new Set(errors)],programme_score:47,
   observed_2024_expenses_cad:28366959822,observed_2023_expenses_cad:26469048805,
   detailed_rows:data.details.length,reconciled_function_groups:groups.length,
   water_and_sewer_2024_cad:2519426792,
   road_and_snow_2024_cad:3711874237,
   fire_services_2024_cad:1533111877,
   audited_nova_replacement:false,approved_fiscal_change:false};
}
