import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const load=async path=>JSON.parse(await readFile(new URL(path,import.meta.url),"utf8"));
const [discovery,proofs,audit]=await Promise.all([
 load("../data/reperage-sources-officielles-g0-15-2026-11-07.json"),
 load("../data/matrice-preuves-g0-15-fiscalite.json"),
 load("../data/audit-completude-programme-nova-2026-11-05.json")
]);
const HOSTS=new Set(["cdn-contenu.quebec.ca","www.revenuquebec.ca",
 "www.retraitequebec.gouv.qc.ca","www.quebec.ca","www.ramq.gouv.qc.ca",
 "statistique.quebec.ca"]);
const inspect=doc=>{
 const failures=[];
 if(doc.schema!=="nova-g015-reperage-sources-officielles/v1"||
 doc.statut!=="REPERAGE_PUBLIC_NON_VALIDE"||
 doc.programme_score_unchanged!==47||
 doc.preconditions_confirmed!==0||
 doc.independent_reviews_confirmed!==0||
 doc.proof_scope_count!==15)return ["FAUX_STATUT"];
 const a=doc.entries||[],b=proofs.proofs;
 if(a.length!==15||a.length!==b.length||
    a.some((v,i)=>v.id!==b[i].id||v.group!==b[i].group||
     v.requis!==b[i].required_evidence||
     v.statut_preuve_g015!=="A_DOCUMENTER"||
     v.independently_reviewed!==false||
     !Array.isArray(v.candidats)||!v.prochaine_verification))failures.push("PROOFS_CHANGED");
 const selected=a.filter(v=>v.candidats.length>0).length;
 if(selected!==15||selected!==doc.selected_candidates_count||
    a.reduce((n,v)=>n+v.candidats.length,0)!==24)failures.push("DISCOVERY_COUNTS");
 for(const e of a)for(const s of e.candidats){
  let u;
  try{u=new URL(s.url)}catch{failures.push("INVALID_URL:"+e.id);continue;}
  if(u.protocol!=="https:"||!HOSTS.has(u.hostname)||u.username||u.password||
   /[\x00-\x1f\x7f]/.test(s.url)||s.statut!=="SOURCE_PUBLIQUE_REPEREE_NON_AUDITEE"||
   !s.periode||!s.apport||!s.limite)failures.push("UNSAFE_OR_UNREVIEWED_SOURCE:"+e.id);
 }
 return failures;
};
test("47 % est maintenu : zéro preuve fiscalement validée",()=>{
 assert.equal(audit.scoring.percentage,47);
 assert.ok(proofs.proofs.every(p=>p.status==="A_DOCUMENTER"&&
  p.primary_source===null&&p.reviewed_independently===false));
 assert.deepEqual(inspect(discovery),[]);
});
test("15 entrées G0.15, 15 thèmes repérés, 24 candidatures de sources",()=>{
 assert.equal(discovery.entries.length,15);
 assert.equal(discovery.selected_candidates_count,15);
 assert.equal(discovery.entries.reduce((n,e)=>n+e.candidats.length,0),24);
});
test("une source candidate ne peut devenir une preuve certifiée",()=>{
 const x=structuredClone(discovery);x.entries[6].independently_reviewed=true;
 assert.ok(inspect(x).includes("PROOFS_CHANGED"));
});
test("une entrée fiscale inventée est rejetée",()=>{
 const x=structuredClone(discovery);x.entries[2].id="V99";
 assert.ok(inspect(x).includes("PROOFS_CHANGED"));
});
test("le lien de collecte ne peut être HTTP ou hors gouvernement",()=>{
 for(const url of ["http://www.quebec.ca/foo","https://example.org/fiscal",
    "https://admin:token@www.quebec.ca/foo"]){
  const x=structuredClone(discovery);
  x.entries[6].candidats[0].url=url;
  assert.ok(inspect(x).some(k=>k.startsWith("UNSAFE_OR_UNREVIEWED_SOURCE")));
 }
});
test("aucune statistique historique de contrôle fiscal n'est annoncée comme rendement NOVA",()=>{
 const v11=discovery.entries.find(x=>x.id==="V11");
 assert.ok(v11.candidats.some(x=>x.limite.includes("NI recettes nettes additionnelles")));
 assert.equal(proofs.net_additional_haven_yield_mcad,null);
});
test("les sources de déciles restent distinctes d'une microsimulation",()=>{
 const v12=discovery.entries.find(x=>x.id==="V12");
 assert.ok(v12.candidats.every(x=>/microsimulation|distribution/.test(x.limite)));
 assert.equal(discovery.programme_score_unchanged,47);
});
test("les liens et les limites sont visibles sur la page d'avancement",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 assert.match(html,/id="sources-fiscales-g015"/);
 assert.match(html,/15 exigences sur 15/);
 assert.match(html,/aucune des 15 preuves/);
 assert.match(html,/www.revenuquebec.ca\/fr\/salle-de-presse\/statistiques\/les-resultats/);
 assert.match(html,/statistique.quebec.ca\/fr\/produit\/tableau/);
});

test("V04 V06 V13 trouvent les sociétés 2021 sans ouvrir les portes G0.15",()=>{
 const url="https://www.quebec.ca/gouvernement/finances-publiques/revenus/donnees-fiscales/statistiques-fiscales-societes";
 for(const id of ["V04","V06","V13"]){
   const e=discovery.entries.find(x=>x.id===id);
   assert.ok(e.candidats.some(x=>x.url===url&&x.statut==="SOURCE_PUBLIQUE_REPEREE_NON_AUDITEE"));
   assert.equal(e.statut_preuve_g015,"A_DOCUMENTER");
 }
 assert.equal(discovery.preconditions_confirmed,0);
 assert.equal(discovery.programme_score_unchanged,47);
});

test("V02, V03, V10 et V14 : sources publiques repérées, non certifiées",()=>{
 const expected={V01:2,V02:2,V03:3,V10:2,V14:1};
 for(const [id,count] of Object.entries(expected)){
   const entry=discovery.entries.find(e=>e.id===id);
   assert.equal(entry.candidats.length,count,id);
   assert.equal(entry.statut_preuve_g015,"A_DOCUMENTER",id);
   assert.equal(entry.independently_reviewed,false,id);
   assert.ok(entry.candidats.every(source=>
     source.statut==="SOURCE_PUBLIQUE_REPEREE_NON_AUDITEE"&&source.limite.length>40),id);
   assert.equal(proofs.proofs.find(e=>e.id===id).primary_source,null,id);
 }
 assert.equal(discovery.updated_at,"2026-11-08");
 assert.equal(discovery.programme_score_unchanged,47);
 assert.deepEqual(inspect(discovery),[]);
});

test("la page publique reflète chaque piste G0.15 sans déclarer de validation",async()=>{
 const html=await readFile(new URL("../avancement-programme-nova.html",import.meta.url),"utf8");
 const start=html.indexOf('id="sources-fiscales-g015"');
 const end=html.indexOf("</section>",start);
 assert.ok(start>=0&&end>start);
 const excerpt=html.slice(start,end);
 const ids=[...excerpt.matchAll(/<tr><th scope="row">(V\d\d) /g)].map(m=>m[1]);
 assert.deepEqual(ids,proofs.proofs.map(p=>p.id));
 assert.match(excerpt,/24 candidatures de sources/);
 assert.match(excerpt,/0 sur 15 sont validées/);
 assert.match(excerpt,/47 % inchangé/);
 for(const id of ["V01","V02","V03","V10","V14"]){
   assert.ok(ids.includes(id));
   for(const source of discovery.entries.find(e=>e.id===id).candidats){
     assert.ok(excerpt.includes(source.url),"Source visible pour "+id);
   }
 }
});

test("les comptes publics réalisés 2025-2026 sont reliés à V02 et V03 sans certification",()=>{
 const sourceUrl="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Comptes-publics/FR/CPTFR_vol1-2025-2026.pdf";
 for(const id of ["V02","V03"]){
   const row=discovery.entries.find(e=>e.id===id);
   assert.ok(row.candidats.some(c=>c.url===sourceUrl&&
      c.statut==="SOURCE_PUBLIQUE_REPEREE_NON_AUDITEE"));
   assert.equal(row.statut_preuve_g015,"A_DOCUMENTER");
   assert.equal(row.independently_reviewed,false);
 }
 assert.equal(discovery.preconditions_confirmed,0);
 assert.deepEqual(inspect(discovery),[]);
});

test("la note 4 officielle complète les trois volets sans changer leur statut",()=>{
 const url="https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Comptes-publics/FR/CPTFR_vol1-2025-2026.pdf";
 for(const id of ["V01","V02","V03"]){
  const e=discovery.entries.find(x=>x.id===id);
  assert.ok(e.candidats.some(x=>x.url===url&&x.statut==="SOURCE_PUBLIQUE_REPEREE_NON_AUDITEE"),id);
  assert.equal(proofs.proofs.find(x=>x.id===id).reviewed_independently,false);
 }
 assert.equal(discovery.preconditions_confirmed,0);
 assert.equal(discovery.independent_reviews_confirmed,0);
 assert.deepEqual(inspect(discovery),[]);
});
