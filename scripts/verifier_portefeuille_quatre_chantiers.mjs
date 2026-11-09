// Contrôle non mutateur, sans accès réseau ni droit de mise en production.
// Un score documentaire, une CI verte et une URL de preuve NE certifient jamais une fin de programme.
import {readFile} from "node:fs/promises";
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const integer=x=>Number.isInteger(x)&&x>=0;
const near=(a,b)=>typeof a==="number"&&Number.isFinite(a)&&Math.abs(a-b)<.0001;
const ids=["NOVA_POLITIQUE","NOVA_SINJIRA_MODELE","CIVIC_COMPASS","CIVIC_POLL","SINJIRA_TOTAL"];
const paths=[
 "projets/projet-nova/data/audit-completude-programme-nova-2026-11-05.json",
 "projets/projet-nova/official/working/plan-execution-nova-sinjira-v1.md",
 "projets/projet-nova/data/validation-sondage-boussole-2026-11-07.json",
 "docs/sinjira/programme-readiness-2026-11-08.json"
];
const name=x=>String(x??"");
export function verifierPortefeuille(portfolio,nova,civic,sinjira,planText){
 const errors=[],fail=x=>errors.push(x);
 if(!obj(portfolio)||!Array.isArray(portfolio.tracks)||!obj(portfolio.sources)||
   !obj(portfolio.policies)||!obj(nova)||!obj(civic)||!obj(sinjira)||
   typeof planText!=="string")
   return {ok:false,errors:["SOURCE_OR_SCHEMA_MISSING"],completion_certified:false};
 if(portfolio.schema!=="projets-nova-sinjira-portefeuille/v1"||
    portfolio.reference_local_date!=="2026-11-08"||
    portfolio.timezone!=="America/Toronto"||
    portfolio.status!=="BILAN_DOCUMENTAIRE_NON_CERTIFIE_NON_ADOPTE")
   fail("SNAPSHOT_SCOPE_CHANGED");
 const sourceKeys=["nova","nova_sinjira","civic","sinjira"];
 const expectedSourceDates=["2026-11-05","2026-11-03","2026-11-07","2026-11-08"];
 if(sourceKeys.some((k,i)=>portfolio.sources[k]?.path!==paths[i]||
    portfolio.sources[k]?.as_of!==expectedSourceDates[i]))
   fail("SOURCE_PATH_OR_DATE_CHANGED");
 const tracks=portfolio.tracks;
 if(tracks.length!==ids.length||ids.some((id,i)=>tracks[i]?.id!==id)||
    new Set(tracks.map(t=>t?.id)).size!==ids.length)fail("TRACKS_MISSING_DUPLICATED_OR_REORDERED");
 const byId=id=>tracks.find(x=>x?.id===id)||{};
 const a=byId("NOVA_POLITIQUE"), ns=byId("NOVA_SINJIRA_MODELE"),
       c=byId("CIVIC_COMPASS"),p=byId("CIVIC_POLL"),s=byId("SINJIRA_TOTAL");
 if(nova.schema!=="nova-programme-completude-v1"||
    nova.status!=="AUDIT_INTERNE_PROVISOIRE_NON_CERTIFIE"||
    nova.date!==portfolio.sources.nova?.as_of||
    nova.scoring?.earned!==47||nova.scoring?.percentage!==47||
    nova.scoring?.maximum!==100||!Array.isArray(nova.dimensions)||
    nova.dimensions.reduce((n,d)=>n+(integer(d?.points)?d.points:0),0)!==47||
    nova.dimensions.reduce((n,d)=>n+(integer(d?.weight)?d.weight:0),0)!==100||
    nova.decisions?.not_officially_adopted!==true||
    nova.decisions?.independent_review_completed!==false)
   fail("NOVA_AUDIT_NOT_RECONCILED");
 if(a.metric_kind!=="AUDIT_INTERNE_POINTS_SUR_100"||
    a.earned!==47||a.maximum!==100||a.missing_points!==53||
    a.closure_gates_total!==7||a.closure_gates_passed!==0||
    a.planned_target_date!=="2027-12-31"||
    a.target_is_approved!==false||a.target_is_guaranteed!==false||
    a.planning_reference!=="https://github.com/M0rdr3x/BenoitCantin/pull/894")
   fail("NOVA_PUBLIC_STATUS_MISREPRESENTED");
 const sectors=nova.sector_register;
 if(!Array.isArray(sectors)||sectors.length!==14||
    sectors.some(r=>r?.completed_measure_sheets_confirmed!==0||
       r.independent_validation_confirmed!==false))
   fail("NOVA_SECTORS_SOURCE_CHANGED");
 if(ns.metric_kind!=="AUCUN_BAREME_DE_COMPLETUDE_AUTONOME"||
    ns.estimated_percent!==null||ns.measures_sectors_candidate!==14||
    ns.independently_validated_sectors_in_nova_audit!==0||
    !Array.isArray(ns.stage_sequence)||
    ns.stage_sequence.join("|")!==
      "G0_DIAGNOSTIC|G1_COMPARAISON|G2_LEGALITE_FINANCEMENT|G3_PILOTE|G4_GENERALISATION"||
    !planText.includes("G0 : diagnostic")||!planText.includes("G4 : généralisation")||
    !planText.includes("étude non adoptée"))
   fail("NOVA_SINJIRA_IS_NOT_A_SEPARATE_CERTIFIED_SCORE");
 if(civic.schema!=="nova-civic-two-tools-readiness/v1"||
    civic.as_of!==portfolio.sources.civic?.as_of||
    !Array.isArray(civic.compass?.gates)||!Array.isArray(civic.poll?.gates)||
    civic.status!=="NON_HOMOLOGUE"||
    civic.compass?.comparison_enabled!==false||
    civic.poll?.published_in_source!==false||
    civic.decision?.both_tools_100_percent!==false||
    civic.decision?.opening_poll_approved!==false||
    civic.decision?.deployments_verified!==false||
    civic.decision?.party_comparison_approved!==false)
   fail("CIVIC_SOURCE_OR_RELEASE_GATES_CHANGED");
 const compassPassed=civic.compass?.gates?.filter(x=>x?.status==="PASSED").length??null,
       pollPassed=civic.poll?.gates?.filter(x=>x?.status==="PASSED").length??null;
 if(!Array.isArray(civic.compass?.gates)||civic.compass.gates.length!==12||
    compassPassed!==5||c.passed!==5||c.total!==12||
    c.metric_kind!=="COUVERTURE_DES_CRITERES_PAS_COMPLETUDE"||
    !near(c.observed_gate_coverage_pct,100*5/12)||
    c.comparison_parties_approved!==false)
   fail("COMPASS_COVERAGE_IS_NOT_COMPLETION");
 if(!Array.isArray(civic.poll?.gates)||civic.poll.gates.length!==11||
    pollPassed!==6||p.passed!==6||p.total!==11||
    p.metric_kind!=="COUVERTURE_DES_CRITERES_PAS_COMPLETUDE"||
    !near(p.observed_gate_coverage_pct,100*6/11)||
    p.publication_authorized!==false)
   fail("POLL_COVERAGE_IS_NOT_AUTHORIZATION");
 if(sinjira.schema!=="sinjira-programme-readiness/v1"||
    sinjira.scope!=="SINJIRA_ONLY_EXCLUDES_PROJET_NOVA"||
    sinjira.reference_date!==portfolio.sources.sinjira?.as_of||
    !Array.isArray(sinjira.domains)||sinjira.domains.length!==10||
    !Array.isArray(sinjira.gates)||sinjira.gates.length!==13||
    sinjira.estimate_uncertainty_percentage_points!==10||
    sinjira.launch?.approved!==false||
    sinjira.launch?.complete!==false||
    sinjira.forecast?.estimated_completion_date!==null)
   fail("SINJIRA_SOURCE_NOT_COMPARABLE");
 const totalWeight=sinjira.domains?.reduce((n,d)=>n+(integer(d?.weight)?d.weight:0),0)??null;
 const weighted=sinjira.domains?.reduce((n,d)=>n+(typeof d?.maturity==="number"?d.weight*d.maturity/100:0),0)??null;
 const gatesOpen=sinjira.gates?.filter(x=>x?.status==="OPEN").length??null;
 if(totalWeight!==100||!near(weighted,66.5)||
    s.metric_kind!=="ESTIMATION_PONDEREE_DE_MATURITE_PRODUIT"||
    !near(s.estimated_percent,66.5)||
    s.estimate_uncertainty_percentage_points!==10||
    s.exit_gates_total!==13||s.exit_gates_passed!==0||gatesOpen!==13||
    s.launch_approved!==false)fail("SINJIRA_WEIGHTED_MATURITY_NOT_CERTIFIED");
 for(const x of tracks){
  if(!obj(x)||typeof x.label!=="string"||!Array.isArray(x.blockers)||
    x.blockers.length<2||typeof x.next_acceptance!=="string"||
    x.certified!==false||x.completion_date!==null||
    x.target_is_approved!==false||x.target_is_guaranteed!==false||
    (x.id!=="NOVA_POLITIQUE"&&x.planned_target_date!==null))
   fail("UNSUPPORTED_CERTIFICATION_OR_DEADLINE:"+name(x?.id));
 }
 if(portfolio.completion_certified!==false||
    portfolio.expected_decision!=="NO_GO_POUR_ATTESTATION_DE_FIN"||
    Object.keys(portfolio.policies).length!==11||
    Object.values(portfolio.policies).some(value=>value!==true))
   fail("UNAUTHORIZED_COMPLETION_OR_ACTIVATION");
 return {
  ok:errors.length===0,errors:[...new Set(errors)],
  reference_local_date:"2026-11-08",
  nova_programme_score:47,nova_points_missing:53,
  nova_sinjira_percentage:null,
  compass_gates:{passed:compassPassed,total:12,coverage_only_pct:Math.round(10000*5/12)/100},
  poll_gates:{passed:pollPassed,total:11,coverage_only_pct:Math.round(10000*6/11)/100},
  sinjira_product_maturity_estimate:weighted,
  sinjira_uncertainty_percentage_points:10,
  sinjira_exit_gates_open:gatesOpen,
  candidate_nova_target:"2027-12-31",
  verified_project_completion_date:null,
  completion_certified:false,
  publication_or_activation_authorized:false,
  historical_sources_not_mutated:true,
  caveat:"La couverture de critères, la maturité estimée et le score politique utilisent des dénominateurs distincts. Aucun total combiné n'est justifiable."
 };
}

export async function loadPortfolioSources(root=new URL("../",import.meta.url)){
 const [portfolio,nova,planText,civic,sinjira]=await Promise.all([
  readFile(new URL("docs/portefeuille/etat-quatre-chantiers-2026-11-08.json",root),"utf8").then(JSON.parse),
  readFile(new URL(paths[0],root),"utf8").then(JSON.parse),
  readFile(new URL(paths[1],root),"utf8"),
  readFile(new URL(paths[2],root),"utf8").then(JSON.parse),
  readFile(new URL(paths[3],root),"utf8").then(JSON.parse)
 ]);
 return {portfolio,nova,planText,civic,sinjira};
}
if(process.argv[1]&&new URL("file://"+process.argv[1]).pathname===new URL(import.meta.url).pathname){
 loadPortfolioSources().then(({portfolio,nova,civic,sinjira,planText})=>{
  const result=verifierPortefeuille(portfolio,nova,civic,sinjira,planText);
  process.stdout.write(JSON.stringify(result,null,2)+"\n");
  if(!result.ok)process.exitCode=1;
 }).catch(e=>{process.stderr.write(String(e)+"\n");process.exitCode=1;});
}
