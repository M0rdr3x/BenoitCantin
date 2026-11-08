/** G0.16y : schéma légal de transition — une ébauche n'est pas une loi. */
const isObj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const ids=Array.from({length:24},(_,i)=>"A"+String(i+1).padStart(2,"0"));
const stageIds=Array.from({length:6},(_,i)=>"ST"+i);
const stopIds=Array.from({length:8},(_,i)=>"STOP"+String(i+1).padStart(2,"0"));
const articleGates=["G01","G01","G03","G03","G04","G02","G02","G05","G05","G05","G06","G06","G08","G07","G07","G03","G09","G09","G09","G02","G10","G10","G10","G10"];
export function inspectG016y(d,concordance){
 const errors=[],bad=s=>errors.push(s);
 if(!isObj(d)||d.schema!=="nova-g016y-conditional-fiscal-transition-framework/v1"||!Array.isArray(d.articles)||!isObj(d.scenario))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.16y"||d.date!=="2026-11-08"||d.score_before!==47||d.score_after!==47||d.basis!=="data/g016x-concordance-fiscale-multiniveau-2026.json"||d.status!=="DRAFT_NO_FORCE_OF_LAW"||d.provisional_legislative_text!=="official/working/avant-projet-loi-cadre-transition-fiscale-nova-g0-16y-v1.md")bad("FALSE_ENACTMENT");
 if(concordance?.schema!=="nova-g016x-multilevel-fiscal-concordance/v1"||concordance?.score_after!==47||concordance?.gates?.length!==10)bad("UPSTREAM_FISCAL_LAW");
 if(d.articles.length!==24||!equal(d.articles.map(x=>x.id),ids)||d.articles.some((a,i)=>a.related_gate!==articleGates[i]||!concordance.gates.some(g=>g.id===a.related_gate)||a.legal_opinion_validated!==false||a.funding_validated!==false||a.adopted!==false||a.entry_into_force_date!==null||!a.title))bad("TWENTY_FOUR_DRAFT_ARTICLES");
 if(!Array.isArray(d.transition_stages)||d.transition_stages.length!==6||!equal(d.transition_stages.map(x=>x.id),stageIds)||d.transition_stages.some(x=>!x.name||x.done!==false||x.planned_date!==null||x.formal_authority_approval!==false))bad("SIX_UNAPPROVED_STAGES");
 if(!Array.isArray(d.mandatory_stops)||d.mandatory_stops.length!==8||!equal(d.mandatory_stops.map(x=>x.id),stopIds)||d.mandatory_stops.some(x=>!x.name||x.block_active!==true||x.clearance_verified!==false||x.evidence_uri!==null))bad("EIGHT_STOPS_STILL_ACTIVE");
 const t=d.two_levy_proposal;
 if(!isObj(t)||t.income_tax_treatment!=="NOT_ENACTED"||t.anti_haven_treatment!=="NOT_ENACTED"||t.certified_rates!==null||t.certified_net_yields!==null)bad("NO_ENACTED_TAX_RATE");
 const canada=d.scenario.QUEBEC_CANADA,sov=d.scenario.QUEBEC_SOUVERAIN;
 if(!isObj(canada)||!isObj(sov)||canada.federal_tax_repealed_by_quebec!==false||canada.municipal_replacement_financed!==false||!equal(canada.annual_10_year_budget,Array(10).fill(null))||sov.federal_transfers_guaranteed!==false||sov.debt_and_functions_allocated!==false||!equal(sov.annual_10_year_budget,Array(10).fill(null)))bad("CONSTITUTIONAL_FRAMEWORK");
 if(!isObj(d.hard_constraints)||Object.keys(d.hard_constraints).length!==8||Object.values(d.hard_constraints).some(x=>x!==true))bad("NON_NEGOTIABLE_PROTECTIONS");
 const r=d.review;
 if(!isObj(r)||r.independent_financial_review_signed!==false||r.independent_legal_review_signed!==false||r.public_consultation_completed!==false||r.formal_adoption!==false)bad("INDEPENDENT_AND_DEMOCRATIC_REVIEW");
 const dec=d.decision;
 if(!isObj(dec)||dec.text_prepared_for_review!==true||dec.law_in_force!==false||dec.fiscal_sustainability_verified!==false||dec.stop_conditions_cleared!==false||dec.score_increase_earned!==false)bad("FALSE_READINESS");
 return {ok:errors.length===0,errors:[...new Set(errors)],phase:"G0.16y",score:47,articles:24,mandatory_stops:8,stops_cleared:0,ready_to_enter_force:false};
}
export function evaluateG016yActivation(d){
 if(!isObj(d)||!Array.isArray(d.mandatory_stops)||!isObj(d.review))return {allowed:false,reason:"MISSING_SCHEMA"};
 const blocking=d.mandatory_stops.filter(x=>x.block_active===true||x.clearance_verified!==true).map(x=>x.id);
 if(!d.review.independent_financial_review_signed)blocking.push("INDEPENDENT_FISCAL_REVIEW");
 if(!d.review.independent_legal_review_signed)blocking.push("INDEPENDENT_LEGAL_REVIEW");
 if(!d.review.public_consultation_completed)blocking.push("PUBLIC_CONSULTATION");
 if(!d.review.formal_adoption)blocking.push("LEGISLATIVE_ADOPTION");
 return {allowed:false,not_an_authorization:true,blocking,reason:blocking.length?"GATES_UNCLEARED":"REQUIRES_SEPARATE_LEGAL_ENACTMENT"};
}
