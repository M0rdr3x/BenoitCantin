import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectNOVACompletionGate,TEN_YEARS,SCENARIOS,FISCAL_PROOF_IDS}
  from "../assets/closure-gate-programme-core.mjs";

const load=async file=>JSON.parse(await readFile(
  new URL("../data/"+file,import.meta.url),"utf8"));
const [audit,g15,g13,g16e]=await Promise.all([
 load("audit-completude-programme-nova-2026-11-05.json"),
 load("matrice-preuves-g0-15-fiscalite.json"),
 load("cadre-financier-g0-13-2026-2036.json"),
 load("pont-financier-g0-16e-2021-2026.json")
]);
const inspect=(a=audit,b=g15,c=g13,d=g16e)=>
  inspectNOVACompletionGate(a,b,c,d);

test("47/100 et 53 points restant : pas une homologation",()=>{
 const x=inspect();
 assert.equal(x.ok,true,x.errors.join(","));
 assert.equal(x.checked_score,47);
 assert.equal(x.points_remaining,53);
 assert.equal(x.completion_certified,false);
 assert.equal(x.notification_authorized,false);
 assert.equal(x.gates_passed,0);
 assert.equal(x.gates_total,7);
});

test("un seul domaine sur dix est à son plafond : la vision",()=>{
 const x=inspect();
 assert.equal(x.domains_completed,1);
 assert.equal(x.domains_required,10);
 assert.equal(audit.dimensions.find(d=>d.points===d.weight).id,"VISION");
});

test("aucune des 14 fiches sectorielles n'a de mesures validées",()=>{
 const x=inspect();
 assert.equal(x.sectors_required,14);
 assert.equal(x.sectors_validated,0);
 assert.equal(x.sector_measure_sheets_confirmed,0);
});

test("les quinze exigences fiscales sont encore non homologuées",()=>{
 const x=inspect();
 assert.equal(x.fiscal_proofs_validated,0);
 assert.equal(x.fiscal_proofs_required,15);
 assert.equal(FISCAL_PROOF_IDS.length,15);
 assert.deepEqual(g15.proofs.map(p=>p.id),FISCAL_PROOF_IDS);
});

test("deux scénarios sur dix ans donnent vingt exercices-scénarios, zéro certifié",()=>{
 const x=inspect();
 assert.deepEqual(g13.scenarios.map(s=>s.id),SCENARIOS);
 assert.deepEqual(g13.scenarios[0].annual.map(y=>y.year),TEN_YEARS);
 assert.deepEqual(g13.scenarios[1].annual.map(y=>y.year),TEN_YEARS);
 assert.equal(x.audited_scenario_years,0);
 assert.equal(x.scenario_years_required,20);
 assert.equal(x.scenarios_financed,0);
});

test("maturité rédactionnelle 75 % n'est pas un score de programme",()=>{
 const x=inspect();
 assert.equal(audit.scoring.documentation_maturity_estimate_percent,75);
 assert.equal(x.documentation_maturity_is_completion,false);
 assert.equal(x.checked_score,47);
});

test("100 points saisis sans preuves n'autorisent pas la déclaration de fin",()=>{
 const copy=structuredClone(audit);
 for(const row of copy.dimensions)row.points=row.weight;
 copy.scoring.earned=100;copy.scoring.percentage=100;
 const x=inspect(copy);
 assert.equal(x.ok,true,x.errors.join(","));
 assert.equal(x.checked_score,100);
 assert.equal(x.points_remaining,0);
 assert.equal(x.gates.audit_score_100,true);
 assert.equal(x.gates.ten_domains_complete,true);
 assert.equal(x.gates.fifteen_fiscal_proofs_validated,false);
 assert.equal(x.completion_certified,false);
 assert.equal(x.notification_authorized,false);
});

test("données chiffrées inventées dans un budget ne créent aucune certification",()=>{
 const fake=structuredClone(g13);
 fake.scenarios[0].annual[0].net_budgetary_balance=999999;
 const x=inspect(audit,g15,fake);
 assert.equal(x.audited_scenario_years,0);
 assert.equal(x.notification_authorized,false);
});

test("un zéro financier est différent d'une preuve absente",()=>{
 const fake=structuredClone(g13);
 fake.scenarios[0].annual[0].net_budgetary_balance=0;
 assert.equal(inspect(audit,g15,fake).audited_scenario_years,0);
 assert.equal(g13.scenarios[0].annual[0].net_budgetary_balance,null);
});

test("les transferts fédéraux ne sont pas automatiquement garantis",()=>{
 const future=structuredClone(g16e);
 future.scenarios[1].federal_transfers_assumed_retained=true;
 // Le programme ne certifie rien : l'existence d'une hypothèse ne vaut pas audit.
 assert.equal(inspect(audit,g15,g13,future).notification_authorized,false);
 assert.equal(g16e.scenarios[1].federal_transfers_assumed_retained,false);
});

test("le même score ne peut devenir un avis indépendant",()=>{
 const copy=structuredClone(audit);
 copy.decisions.independent_review_completed=true;
 const x=inspect(copy);
 assert.equal(x.ok,false);
 assert.ok(x.errors.includes("AUDIT_INTERNE_INVALIDE"));
 assert.equal(x.notification_authorized,false);
});

test("un registre de preuves fiscales tronqué est refusé (échec contrôlé)",()=>{
 const copy=structuredClone(g15);copy.proofs.pop();
 const x=inspect(audit,copy);
 assert.equal(x.ok,false);
 assert.ok(x.errors.includes("PREUVES_FISCALES_NON_CONFORMES"));
 assert.equal(x.notification_authorized,false);
});

test("un nom de scénario manquant ou dupliqué bloque la clôture",()=>{
 const fake=structuredClone(g13);
 fake.scenarios[1].id="QUEBEC_CANADA";
 const x=inspect(audit,g15,fake);
 assert.equal(x.ok,false);
 assert.ok(x.errors.includes("SCENARIOS_G013_NON_CONFORMES"));
});

test("une année de budget 2040 hors horizon est rejetée",()=>{
 const fake=structuredClone(g13);
 fake.scenarios[1].annual[7].year="2040-2041";
 const x=inspect(audit,g15,fake);
 assert.equal(x.ok,false);
 assert.ok(x.errors.includes("EXERCICE_INCOHERENT:QUEBEC_SOUVERAIN:7"));
});

test("un scénario incomplet n'est pas remplacé par un total inventé",()=>{
 const fake=structuredClone(g16e);
 fake.scenarios[1].annual.pop();
 const x=inspect(audit,g15,g13,fake);
 assert.equal(x.ok,false);
 assert.ok(x.errors.includes("EXERCICES_DIX_ANS_INCOMPLETS:QUEBEC_SOUVERAIN"));
});

test("aucune adoption politique ou juridique n'est autorisée par un test de code",()=>{
 const x=inspect();
 assert.equal(x.gates.formal_adoption,false);
 assert.equal(x.gates.independent_review,false);
 assert.equal(audit.decisions.not_officially_adopted,true);
 assert.equal(x.notification_authorized,false);
});

test("une entrée corrompue doit échouer sans exception",()=>{
 const x=inspect(null,null,null,null);
 assert.equal(x.ok,false);
 assert.equal(x.notification_authorized,false);
 assert.equal(x.checked_score,null);
});

test("la page publique indique le vrai seuil de fin et les blocages mesurés",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 const start=html.indexOf('id="porte-fin-programme-nova"');
 const end=html.indexOf("</section>",start);
 assert.ok(start>=0&&end>start);
 const section=html.slice(start,end);
 for(const str of ["47 %","53 points","1 sur 10","0 sur 14",
                  "0 sur 15","0 sur 20","indépendante","pas encore terminé"]){
    assert.ok(section.includes(str),str);
 }
 assert.ok(section.includes("matrice-preuves-g0-15-fiscalite.json"));
 assert.ok(section.includes("cadre-financier-g0-13-2026-2036.json"));
});
