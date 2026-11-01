'use strict';
// Tests d'exécution du code réel de la boussole, sans API ni données privées.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(
  path.join(__dirname, '../projets/projet-nova/assets/boussole-electorale.js'), 'utf8');
let checks = 0;
function section(start, stop) {
  const i = source.indexOf(start);
  const end = source.indexOf(stop, i + start.length);
  assert.ok(i >= 0 && end > i, 'Segment réel de la boussole introuvable');
  return source.slice(i, end);
}
const escapeLine = source.split('\n').find(s => s.includes('const esc = value =>'));
assert.ok(escapeLine, 'Fonction echappement HTML absente');
const codeUnderTest = [
  escapeLine,
  section('  function safeEvidenceUrl(value){', '\n  function currentQuestion(){'),
  section('  function renderQuestion(question, index){', '\n  function renderCurrentQuestion(){'),
  section('  const DOCUMENTARY_STATUS_LABELS = {', '\n  function renderDocumentaryStatus(')
].join('\n');
const nodes = {};
function node(id, attrs={}) {
  return nodes[id] = {
    value: '', innerHTML:'', textContent:'', hidden:false, checked:false,
    ...attrs, addEventListener(){}, focus(){}
  };
}
const sandbox = {
  URL, console,
  document: {
    createElement: tag => ({
      tagName: tag, dataset:{}, className:'', innerHTML:'',
      addEventListener(){}, querySelector(){return null}
    }),
  },
  nodes,
};
const setup = [
  'const $ = selector => nodes[selector] || null;',
  'const RESPONSES = [{value:-3,label:"Désaccord"},{value:3,label:"Accord"}];',
  'const WEIGHTS = [{value:"normal",label:"Normale"}];',
  'const state = {data:{axes:[{id:"axis",title:"Sujet"}],questions:[]},answers:new Map(),importance:new Map()};'
].join('\n');
vm.runInNewContext(setup+'\n'+codeUnderTest+
  '\nglobalThis.api={renderQuestion,safeEvidenceUrl,renderEvidenceExplorer};',
  sandbox, {timeout:3000});
const api = sandbox.api;

for (const malformed of [
  'javascript:alert(1)', 'data:text/html,<script>alert(1)</script>',
  'vbscript:msgbox(1)', 'blob:https://example.org/abc',
  'file:///etc/passwd', 'http://example.org/unencrypted',
  '//example.org/', '/relative-source', 'https://user:pass@example.org/a',
  'https://example.org/\n<script>', 'https://example.org\\@evil.example/path',
  null, undefined, '', 42, 'https://example.org/'+('x'.repeat(3000))
]) {
  assert.equal(api.safeEvidenceUrl(malformed), '', 'Unsafe evidence URL accepted: '+String(malformed).slice(0,70));
  checks++;
}
const legitimate = [
  'https://www.electionsquebec.qc.ca/elections/',
  'https://example.org/communique?mode=public&lang=fr',
  'https://pq.org/nouvelles/', 'https://quebecsolidaire.net/theme/logement',
];
for (const uri of legitimate) {
  assert.equal(api.safeEvidenceUrl(uri), uri);
  checks++;
}

// Verifier la vraie interpolation des boutons radio (id provenant du JSON).
for (const attack of [
  'q1" autofocus onfocus="alert(1)',
  'q"><img src=x onerror=alert(1)>',
  "' onclick='alert(1)",
]) {
  const html = api.renderQuestion({id:attack,axis:'axis',text:'Question',title:'Test'},0).innerHTML;
  assert.ok(html.includes('name="'), 'La question n’a plus de groupe radio');
  assert.ok(!html.includes('name="'+attack+'"'), 'Identifiant non echappe');
  assert.ok(!html.includes('autofocus onfocus="'), 'Attribut injecte');
  assert.ok(!html.includes('<img'), 'Balise injectee');
  assert.equal((html.match(/name="/g)||[]).length,3,'Réponses radio cassées');
  checks+=5;
}
const normal = api.renderQuestion({id:'q17',axis:'axis',text:'Sujet normal'},0).innerHTML;
assert.equal((normal.match(/name="q17"/g)||[]).length,3);
checks++;

function renderOneEvidence(url) {
  Object.keys(nodes).forEach(k => delete nodes[k]);
  node('#compass-evidence-question');
  node('#compass-evidence-only-documented',{checked:false});
  const output = node('#compass-evidence-question-results');
  node('#compass-evidence-question-status');
  node('#compass-evidence-selected-question');
  node('#compass-evidence-priorities');
  node('#compass-evidence-priority-links');
  api.renderEvidenceExplorer(
    {questions:[{id:'q1',text:'Texte officiel',axis:'axis'}],
      axes:[{id:'axis',title:'Thème'}]},
    {parties:[{id:'parti',name:'Formation'}]},
    {questions:[{questionId:'q1',statuses:{parti:'documented_support'}}],
      evidenceRecords:[{questionId:'q1',partyId:'parti',finalizable:true,
        secondIndependentReview:{status:'completed',reviewedAt:'2026-10-20'},
        proposedStatus:'documented_support',confidence:'high',
        sourceUrl:url,evidenceSummary:'Résumé',rationale:'Explication'}]}
  );
  return output.innerHTML;
}
for (const evil of [
  'javascript:alert(1)', 'data:text/html,alert(1)',
  'http://example.org/insecure', 'https://user@evil.example/p',
  'https://example.org/\ninvalid', 'https://example.org\\@evil.example/'
]) {
  const html=renderOneEvidence(evil);
  assert.ok(!html.includes('href='), 'Lien non sûr présent dans le HTML final');
  assert.ok(html.includes('Lien source non sécurisé ou indisponible'));
  checks+=2;
}
const good=renderOneEvidence('https://example.org/source?a=1&b=2');
assert.ok(good.includes('href="https://example.org/source?a=1&amp;b=2"'));
assert.ok(good.includes('rel="noopener noreferrer"'));
assert.ok(!good.includes('Lien source non sécurisé'));
checks+=3;

console.log('PASS: '+checks+' assertions du rendu HTML réel et des protocoles de sources NOVA.');
