// G0.16u — portes de préparation et chaîne d'audit documentaire.
// Ce contrôleur ne certifie PAS l'État ni ne prouve des paiements.
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const cents=x=>Math.round(x*100);
const rank=["VISION","INSTITUTIONS","DROITS","SERVICES","ECONOMIE","FINANCES","SOUVERAINETE","EXECUTION","PREUVES","ADOPTION"];
const status="DOCUMENTS_NOT_REQUESTED";
export function inspectG016u(d,a,t){
 const errors=[],fail=s=>errors.push(s);
 if(!object(d)||d.schema!=="nova-g016u-evidence-requests-and-completion-gates/v1"||!Array.isArray(d.dimensions)||!Array.isArray(d.requests)||!object(d.access_procedure))return {ok:false,errors:["SCHEMA"]};
 if(d.phase!=="G0.16u"||d.date!=="2026-11-08"||d.current_audit_file!=="data/audit-completude-programme-nova-2026-11-05.json"||d.program_score_before!==47||d.program_score_after!==47||d.program_percent_remaining!==53||d.score_is_internal_provisional!==true||d.independent_program_validation!==false||d.party_adopted_programme!==false||d.version_of_last_completed_phase!=="G0.16t")fail("FALSE_PROGRESS");
 if(a?.scoring?.earned!==47||a?.scoring?.maximum!==100||!Array.isArray(a?.dimensions)||a.dimensions.length!==10||a.scoring.legal_government_approval!==false)fail("SOURCE_AUDIT");
 if(d.dimensions.length!==10||d.dimensions.map(x=>x.id).join("|")!==rank.join("|")||d.dimensions.some((x,i)=>x.max_points!==a.dimensions[i]?.weight||x.earned_points!==a.dimensions[i]?.points||x.remaining_points!==x.max_points-x.earned_points||x.externally_certified!==false||x.score_increment_suggested_now!==0)||d.dimensions.reduce((s,x)=>s+x.max_points,0)!==100||d.dimensions.reduce((s,x)=>s+x.earned_points,0)!==47||d.dimensions.reduce((s,x)=>s+x.remaining_points,0)!==53)fail("53_POINT_GATE");
 const p=d.access_procedure;
 if(p.prefer_written_request!==true||p.standard_reply_days_calendar!==20||p.possible_extension_days_calendar!==10||p.clock_starts_on_proven_receipt!==true||p.draft_is_not_sent!==true||p.date_submitted!==null||p.date_received_by_institution!==null||p.statutory_deadline!==null||p.response_received_date!==null||p.review_possible_after_written_request!==true||p.review_deadline_days_in_general!==30||p.no_automatic_unconditional_disclosure!==true||p.third_party_privacy_redactions_possible!==true||p.ask_existing_documents_only!==true||p.avoid_identifying_private_bank_account_numbers!==true||p.fees_may_apply!==true)fail("ACCESS_LAW_TIMING");
 const sources=d.primary_sources;
 if(!Array.isArray(sources)||sources.length!==8||!sources.some(x=>x.id==="CAI_PROCESS"&&x.url.startsWith("https://www.cai.gouv.qc.ca/"))||!sources.some(x=>x.id==="MAMH_ACCESS"&&x.url.startsWith("https://www.quebec.ca/"))||!sources.some(x=>x.id==="MUNICIPAL_CONTACT"&&x.url==="https://munpdg.ca/nous-joindre/"))fail("PUBLIC_PROVENANCE");
 const [m,h]=d.requests;
 if(d.requests.length!==2||m.id!=="REQ_MUNI"||m.verified_specific_responsible_email!==null||m.official_site!=="https://munpdg.ca/nous-joindre/"||h.id!=="REQ_MAMH"||h.verified_email!=="accesinfo@mamh.gouv.qc.ca"||!m.draft_file.endsWith("demande-acces-municipalite-g0-16u.md")||!h.draft_file.endsWith("demande-acces-mamh-g0-16u.md")||d.requests.some(x=>x.prepared!==true||x.sent!==false||x.date_sent!==null||x.receipt_verified!==false||x.result!==status))fail("DRAFTS_NOT_SUBMITTED");
 if(t?.schema!=="nova-g016t-gascons-certificate-and-grant-timing/v1"||t?.score_after!==47||t?.decision?.grant_paid_to_municipality_verified!==false)fail("PRIOR_REGISTER");
 const [pay,grant]=d.evidence_chain||[];
 if(!pay||!grant||d.evidence_chain.length!==2||pay.id!=="CHAIN_PAYABLE"||grant.id!=="CHAIN_GRANT"||pay.source!=="G0.16t"||grant.source!=="G0.16t"||cents(pay.authorized_selected_pre_tax_cad)!==cents(t.selected_series.subtotal_all_selected_pre_tax_cad)||grant.committed_total_cad!==t.provincial_commitment.total_committed_cad||d.evidence_chain.some(x=>x.all_documents_available!==false||x.validated_bank_last_step!==false||x.verified_aggregate_cad!==null||x.steps?.length!==7)||!pay.steps.includes("DEBIT_DE_TRESORERIE")||!grant.steps.includes("RECEPTION_BANQUE_MUNICIPALE"))fail("CHAIN_NOT_BANK_RECONCILED");
 if(!Array.isArray(d.evidence_gaps)||d.evidence_gaps.length!==8||d.evidence_gaps.some((x,i)=>x.id!=="G"+(i+1)||x.status!=="NOT_PROVEN"||!["REQ_MUNI","REQ_MAMH",null].includes(x.request)))fail("MISSING_DOCUMENTS");
 if(!object(d.falsifiable_controls)||Object.values(d.falsifiable_controls).some(x=>x!==true))fail("ANTI_FALSE_PROOF");
 const o=d.outcomes;
 if(!object(o)||o.requests_prepared!==2||o.requests_sent!==0||o.receipts_received!==0||o.external_reviews_completed!==0||o.bank_level_payments_confirmed!==0||o.programme_score_increment!==0)fail("NO_OUTPUT_PROOF_YET");
 return {ok:errors.length===0,errors:[...new Set(errors)],score:47,remaining:53,requests_prepared:2,requests_submitted:0,municipal_bank_receipts_verified:0,independent_program_audits:0};
}
