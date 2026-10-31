#!/usr/bin/env node
"use strict";
/**
 * Contrat exécutable des deux vrais clients politiques Nova.
 * Éprouve les handlers de retrait d'accord, sans DOM externe ni réseau.
 * Ni compte, ni réponses réelles, ni publication.
 */
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const nova = path.resolve(__dirname, "../projets/projet-nova");
const cases = [
  {id:"consultation-40",filename:"consultation-40.js",count:40,
   answers:"answers",refresh:"refresh",next:"render",show:true},
  {id:"sondage-64",filename:"sondage.js",count:64,
   answers:"selections",refresh:"refreshStart",next:"renderQuestion",show:false}
];

function sliceFunction(source, first, next) {
  const start = source.indexOf("  function " + first + "(");
  const stop = source.indexOf("  function " + next + "(", start + 3);
  assert.ok(start >= 0 && stop > start,
    "Fonction officielle absente ou modifiée : " + first);
  return source.slice(start, stop);
}

function makeFixture(spec, stage, revoked, futureCollectionOpen = false) {
  const source = fs.readFileSync(path.join(nova,"assets",spec.filename),"utf8");
  assert.match(source, /const COLLECTION_OPEN = false;/);
  assert.match(source, /const LIVE_OPINION_CONSENT_GRANTED = false;/);
  assert.ok(source.includes("addEventListener('change', " + spec.refresh + ")"),
    "L'accord n'est pas relié au contrôle immédiat de la démonstration");
  const programText = [
    spec.show ? sliceFunction(source,"show","refresh") : "",
    sliceFunction(source,spec.refresh,spec.next),
    sliceFunction(source,"clearLocalDemo","resetSurvey"),
    spec.refresh + "();"
  ].join("\n");
  const script = new vm.Script(programText,{filename:spec.filename+":revocation"});
  const elements = Object.create(null);
  for (const id of [
    "sondage-introduction","sondage-questionnaire","sondage-finish",
    "sondage-age","sondage-consent","sondage-review-list",
    "sondage-status","sondage-submit-status","sondage-choices",
    "sondage-next","sondage-start","sondage-titre"
  ]) {
    elements[id] = {
      hidden: false, disabled: false, checked: false,
      cleared: false, textContent: "initial",
      replaceChildren(){this.cleared = true;},
      focus(){this.focused = true;}
    };
  }
  elements["sondage-introduction"].hidden = true;
  elements["sondage-questionnaire"].hidden = stage !== "questionnaire";
  elements["sondage-finish"].hidden = stage !== "finish";
  elements["sondage-age"].checked = revoked !== "age";
  elements["sondage-consent"].checked = revoked !== "consent";

  const selections = new Map([["q01","opinion-fictive"]]);
  const sandbox = {
    COLLECTION_OPEN:futureCollectionOpen, LIVE_OPINION_CONSENT_GRANTED:futureCollectionOpen,
    questions:Array.from({length:spec.count},(_,i)=>({id:"q"+i})),
    [spec.answers]:selections, step:7, editingReview:true, submitting:false,
    $:id=>elements[id],
    eligible:()=>elements["sondage-age"].checked && elements["sondage-consent"].checked,
    setStatus:(message,target="sondage-status")=>{elements[target].textContent=message;}
  };
  script.runInNewContext(sandbox,{timeout:1000});
  return {elements,selections,sandbox};
}

for (const spec of cases) {
  for (const stage of ["questionnaire","finish"]) {
    for (const revoked of ["age","consent"]) {
      test(spec.id+" : retirer "+revoked+" en "+stage+" efface immédiatement",()=>{
        const {elements:e,selections,sandbox:s} = makeFixture(spec,stage,revoked);
        assert.equal(selections.size,0,"opinion persistante après retrait");
        assert.equal(s.step,0,"index du parcours non réinitialisé");
        assert.equal(s.editingReview,false,"révision encore active");
        assert.equal(e["sondage-introduction"].hidden,false);
        assert.equal(e["sondage-questionnaire"].hidden,true);
        assert.equal(e["sondage-finish"].hidden,true);
        assert.equal(e["sondage-age"].checked,false);
        assert.equal(e["sondage-consent"].checked,false);
        assert.equal(e["sondage-review-list"].cleared,true);
        assert.equal(e["sondage-choices"].cleared,true);
        assert.equal(e["sondage-start"].disabled,true);
        assert.equal(e["sondage-next"].disabled,true);
        assert.equal(e["sondage-titre"].focused,true);
      });
    }
    test(spec.id+" : accord valide en "+stage+" ne purge pas prématurément",()=>{
      const {elements:e,selections,sandbox:s} = makeFixture(spec,stage,null);
      assert.equal(selections.size,1);
      assert.equal(s.step,7);
      assert.equal(s.editingReview,true);
      assert.equal(e["sondage-introduction"].hidden,true);
      assert.equal(e["sondage-questionnaire"].hidden,stage!=="questionnaire");
      assert.equal(e["sondage-finish"].hidden,stage!=="finish");
      assert.equal(e["sondage-age"].checked,true);
      assert.equal(e["sondage-consent"].checked,true);
      assert.equal(e["sondage-choices"].cleared,false);
    });
  }
}

/** Ces garde-fous doivent aussi rester actifs si un jour la collecte est autorisée.
 * Le consentement de démonstration n'ouvre toujours aucune collecte en CI.
 */
for (const spec of cases) {
  for (const stage of ["questionnaire", "finish"]) {
    for (const revoked of ["age", "consent"]) {
      test(spec.id + " : retrait " + revoked +
           " efface les opinions même avec les drapeaux futurs en " + stage, () => {
        const {elements:e,selections,sandbox:s} =
          makeFixture(spec, stage, revoked, true);
        assert.equal(selections.size, 0, "les opinions seraient retenues après retrait");
        assert.equal(s.step, 0);
        assert.equal(e["sondage-introduction"].hidden, false);
        assert.equal(e["sondage-questionnaire"].hidden, true);
        assert.equal(e["sondage-finish"].hidden, true);
        assert.equal(e["sondage-age"].checked, false);
        assert.equal(e["sondage-consent"].checked, false);
      });
    }
  }
  test(spec.id + " : purge inconditionnelle au départ et au retour bfcache", () => {
    const source = fs.readFileSync(path.join(nova, "assets", spec.filename), "utf8");
    assert.match(source,
      /window\.addEventListener\('pagehide', \(\) => \{\s*clearLocalDemo\(\);\s*\}\);/);
    assert.match(source,
      /if \(event\.persisted\) clearLocalDemo\(\);/);
    assert.ok(!source.includes("if (event.persisted && !COLLECTION_OPEN"),
      "le retour d'historique ne doit jamais contourner la purge");
    assert.equal((source.match(/if \(recorded \|\| submitting \|\| !eligible\(\)\) return;/g) || []).length, 2,
      "impossible de modifier les choix locaux pendant ou après un envoi");
  });
}

for (const spec of cases) {
  test(spec.id + " : retrait du consentement pendant un envoi garde le verrou réseau", () => {
    const {elements:e,selections,sandbox:s} =
      makeFixture(spec, "questionnaire", null);
    s.submitting = true;
    e["sondage-consent"].checked = false;
    s[spec.refresh]();
    assert.equal(selections.size, 0, "l'opinion locale doit être effacée");
    assert.equal(s.submitting, true, "l'absence de données locales ne clôt pas une requête en cours");
    assert.equal(e["sondage-introduction"].hidden, false);
  });
}

test("consultation-40 : aucun reset concurrent pendant une transmission", () => {
  const source = fs.readFileSync(path.join(nova, "assets", "consultation-40.js"), "utf8");
  const reset = sliceFunction(source, "resetSurvey", "init");
  let confirmationCalled = false;
  const sandbox = {
    submitting: true,
    window: {confirm: () => { confirmationCalled = true; return true; }},
    clearLocalDemo: () => {throw Error("purge concurrente");},
    $: () => ({focus: () => {throw Error("focus concurrent");}})
  };
  new vm.Script(reset + "\nresetSurvey();").runInNewContext(sandbox, {timeout: 1000});
  assert.equal(confirmationCalled, false);
});
