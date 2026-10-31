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
    consentEpoch:0,
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


/**
 * Simule la future collecte uniquement DANS LE VM Node : aucun navigateur,
 * aucune clé, aucune authentification réelle, aucune requête réseau.
 * Les handlers de soumission testés proviennent du vrai code de production.
 */
function liveSubmissionFixture(spec) {
  const source = fs.readFileSync(path.join(nova, "assets", spec.filename), "utf8");
  const consentClear = sliceFunction(source,"clearLocalDemo","resetSurvey");
  assert.match(consentClear,/consentEpoch \+= 1;/,
    spec.id+" : une purge doit invalider toute transmission en attente");
  assert.match(source,/submissionConsentEpoch !== consentEpoch \|\| !eligible\(\)/,
    spec.id+" : absence de contrôle de révocation");

  const scriptStart = spec.count === 40
    ? source.indexOf("    $('sondage-submit').addEventListener('click', async () => {")
    : source.indexOf("  function payload() {");
  const scriptEnd = spec.count === 40
    ? source.indexOf("\n    });",scriptStart) + "\n    });".length
    : source.indexOf("\n  function clearLocalDemo()",scriptStart);
  assert.ok(scriptStart >= 0 && scriptEnd > scriptStart, "Soumission officielle introuvable");
  const program = source.slice(scriptStart,scriptEnd)
    .replace("await import('../../../assets/js/sinjira-supabase.js')", "await loadApi()")
    + (spec.count === 64 ? "\nthis.liveSubmit = submit;" : "");
  assert.ok(!program.includes("await import("), "Module réel interdit dans le test");

  const nodes = Object.create(null);
  for(const id of ["sondage-age","sondage-consent","sondage-submit",
                   "sondage-submit-status"]) {
    nodes[id] = {checked:id !== "sondage-submit" && id !== "sondage-submit-status",
                 disabled:false,textContent:"",
                 addEventListener(event,handler) {
                   if(event === "click") this.callback = handler;
                 }};
  }
  const choices = Array.from({length:spec.count},(_,i) =>
    ["q"+String(i+1).padStart(2,"0"),spec.count===40?"pour":"skip"]);
  let resolveAuth;
  let resolveInvoke;
  let authRequested = 0;
  let requests = 0;
  const authResult = new Promise(resolve => {resolveAuth=resolve;});
  const invokeResult = new Promise(resolve => {resolveInvoke=resolve;});
  const client = {
    auth:{getUser:()=>{authRequested++;return authResult;}},
    functions:{invoke:()=>{requests++;return invokeResult;}}
  };
  const state = {
    COLLECTION_OPEN:true, LIVE_OPINION_CONSENT_GRANTED:true,
    SURVEY_ID:spec.count===40?"nova-orientations-40-v1":"nova-consultation-64-v1",
    consentEpoch:0, submitting:false, recorded:false,
    answers:new Map(choices), selections:new Map(choices),
    questions:choices.map(([id])=>({id})),
    ANSWERS:[["skip","Sans opinion"]],
    allowed:new Set(["pour","contre","sans_opinion"]),
    $:id=>nodes[id],
    eligible:()=>nodes["sondage-age"].checked && nodes["sondage-consent"].checked,
    setStatus:(value,id="sondage-submit-status")=>{nodes[id].textContent=value;},
    loadApi:async()=>({getSupabase:()=>client})
  };
  new vm.Script(program,{filename:spec.filename+":submit-revocation"})
    .runInNewContext(state,{timeout:1000});
  const submit = spec.count===40
    ? ()=>nodes["sondage-submit"].callback()
    : ()=>state.liveSubmit();

  return {
    state,nodes,submit,
    get authRequested(){return authRequested;},
    get requests(){return requests;},
    resolveAuth:()=>resolveAuth({data:{user:{id:"compte-fictif"}},error:null}),
    resolveInvoke:()=>resolveInvoke({
      data:{ok:true,code:"RECORDED",survey:state.SURVEY_ID},error:null
    }),
    revoke:()=>{
      nodes["sondage-consent"].checked=false;
      nodes["sondage-age"].checked=false;
      state.consentEpoch+=1;
      state.answers.clear();
      state.selections.clear();
      nodes["sondage-submit-status"].textContent="";
    }
  };
}
async function awaitMicrotaskCondition(predicate) {
  for(let i=0;i<100;i++) {
    if(predicate()) return;
    await Promise.resolve();
  }
  assert.fail("La transition asynchrone fictive attendue n'a pas eu lieu");
}

for(const spec of cases) {
  test(spec.id+" : révocation pendant authentification interdit tout POST", async()=>{
    const f=liveSubmissionFixture(spec);
    const done=f.submit();
    await awaitMicrotaskCondition(()=>f.authRequested===1);
    f.revoke();
    f.resolveAuth();
    await done;
    assert.equal(f.requests,0,"Aucun envoi ne doit démarrer après la révocation");
    assert.equal(f.state.recorded,false);
    assert.equal(f.state.submitting,false);
    assert.equal(f.nodes["sondage-submit-status"].textContent,"");
  });

  test(spec.id+" : révocation pendant réponse réseau n'affiche aucun faux succès",async()=>{
    const f=liveSubmissionFixture(spec);
    const done=f.submit();
    await awaitMicrotaskCondition(()=>f.authRequested===1);
    f.resolveAuth();
    await awaitMicrotaskCondition(()=>f.requests===1);
    f.revoke();
    f.resolveInvoke();
    await done;
    assert.equal(f.requests,1,"Une requête déjà expédiée ne peut être reprise");
    assert.equal(f.state.recorded,false,"Ne pas restaurer un succès après révocation");
    assert.equal(f.state.submitting,false);
    assert.equal(f.nodes["sondage-submit-status"].textContent,"");
  });

  test(spec.id+" : sans révocation le succès fictif reste possible",async()=>{
    const f=liveSubmissionFixture(spec);
    const done=f.submit();
    await awaitMicrotaskCondition(()=>f.authRequested===1);
    f.resolveAuth();
    await awaitMicrotaskCondition(()=>f.requests===1);
    f.resolveInvoke();
    await done;
    assert.equal(f.requests,1);
    assert.equal(f.state.recorded,true);
    assert.equal(f.state.submitting,false);
    assert.match(f.nodes["sondage-submit-status"].textContent,/enregistrée/i);
  });
}
