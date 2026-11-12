import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspecterMatriceJuridique,CONTEXTES,DOSSIERS,PIECES}
  from "../assets/matrice-juridique-p0-core.mjs";

const matrice=JSON.parse(await readFile(
  new URL("../data/matrice-juridique-p0-2026-11-08.json",import.meta.url),"utf8"
));
const inspecter=(m=matrice)=>inspecterMatriceJuridique(m);

test("matrice P0 : 12 dossiers et 24 contextes sans avis inventé",()=>{
  const x=inspecter();
  assert.equal(x.ok,true,x.erreurs.join(","));
  assert.deepEqual(matrice.cases.map(d=>d.id),DOSSIERS);
  assert.deepEqual(matrice.jurisdictions,CONTEXTES);
  assert.equal(x.dossiers,12);
  assert.equal(x.contextes_attendus,24);
  assert.equal(x.contextes_examens_declares,0);
  for(const row of matrice.cases)for(const contexte of CONTEXTES){
    assert.equal(row[contexte].legal_status,"NON_VERIFIE");
    assert.ok(row[contexte].question.length>30);
    assert.deepEqual(row[contexte].review_evidence,
      Object.fromEntries(PIECES.map(k=>[k,null])));
  }
});

test("le score politique et la certification ne changent pas",()=>{
  const x=inspecter();
  assert.equal(matrice.baseline_points,47);
  assert.equal(matrice.increment_at_creation,0);
  assert.equal(x.points_supplementaires_autorises,0);
  assert.equal(x.certification_automatique_autorisee,false);
  assert.equal(x.evaluation_humaine_requise,true);
});

test("une conclusion favorable sans pièces est rejetée",()=>{
  const copie=structuredClone(matrice);
  copie.cases[0].statut="EN_INSTRUCTION";
  copie.cases[0][CONTEXTES[0]].legal_status="AVIS_FAVORABLE";
  const x=inspecter(copie);
  assert.equal(x.ok,false);
  assert.ok(x.erreurs.includes("AVIS_SANS_PIECES_EXIGIBLES:J01:"+CONTEXTES[0]));
});

test("une conclusion défavorable sans pièces est également rejetée",()=>{
  const copie=structuredClone(matrice);
  copie.cases[0].statut="EN_INSTRUCTION";
  copie.cases[0][CONTEXTES[1]].legal_status="AVIS_DEFAVORABLE";
  assert.equal(inspecter(copie).ok,false);
});

test("une seule opinion documentée ne valide pas le second contexte",()=>{
  const copie=structuredClone(matrice);
  const dossier=copie.cases[0];
  dossier.statut="EN_INSTRUCTION";
  const c=dossier[CONTEXTES[0]];
  c.legal_status="AVIS_FAVORABLE";
  for(const k of PIECES.filter(v=>v.endsWith("_url")))
    c.review_evidence[k]="https://exemple.invalid/fichier/"+k;
  c.review_evidence.opinion_date="2026-11-08";
  c.review_evidence.reviewer_independence_checked=true;
  const x=inspecter(copie);
  assert.equal(x.ok,true,x.erreurs.join(","));
  assert.equal(x.contextes_examens_declares,1);
  assert.equal(dossier[CONTEXTES[1]].legal_status,"NON_VERIFIE");
  // Les URI de cette fixture sont fictives : la conformité reste non certifiée.
  assert.equal(x.certification_automatique_autorisee,false);
  assert.equal(x.points_supplementaires_autorises,0);
});

test("date juridiquement inexistante rejetée",()=>{
  const copie=structuredClone(matrice);
  copie.cases[0][CONTEXTES[0]].review_evidence.opinion_date="2026-02-30";
  assert.ok(inspecter(copie).erreurs.includes("DATE_OPINION_INVALIDE:J01:"+CONTEXTES[0]));
});

test("référence score artificiellement améliorée refusée",()=>{
  const copie=structuredClone(matrice);
  copie.baseline_points=100;
  copie.increment_at_creation=53;
  assert.ok(inspecter(copie).erreurs.includes("REFERENCE_SCORE_ALTEREE"));
});

test("dossier absent, dupliqué ou contexte non isolé : refus",()=>{
  const a=structuredClone(matrice);a.cases.pop();
  const b=structuredClone(matrice);b.cases[1].id="J01";
  const c=structuredClone(matrice);c.jurisdictions=[CONTEXTES[0],CONTEXTES[0]];
  assert.ok(inspecter(a).erreurs.includes("DOUZE_DOSSIERS_INCOMPLETS"));
  assert.ok(inspecter(b).erreurs.includes("DOUZE_DOSSIERS_INCOMPLETS"));
  assert.ok(inspecter(c).erreurs.includes("CONTEXTES_INCORRECTS"));
});

test("décision d'adoption non appuyée par audit : refus",()=>{
  const copie=structuredClone(matrice);
  copie.cases[0].adoption_decision="adopté";
  assert.ok(inspecter(copie).erreurs.includes("ADOPTION_NON_PROUVEE:J01"));
});

test("une déclaration d'audit global sans pièces ne vaut pas preuve",()=>{
  const copie=structuredClone(matrice);
  copie.independent_juridical_audit_completed=true;
  assert.ok(inspecter(copie).erreurs.includes("AUDIT_EXTERNE_NON_ETABLI"));
});

test("entrée absente ou corrompue échoue sans exception",()=>{
  assert.equal(inspecter(null).ok,false);
  assert.equal(inspecter([]).ok,false);
});
