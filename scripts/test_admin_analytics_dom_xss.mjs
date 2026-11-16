#!/usr/bin/env node
// Exécute le VRAI script administrateur sous un DOM factice qui interdit
// toute affectation innerHTML / outerHTML, même avec un payload malveillant.
// Aucun réseau, compte, navigateur ou service Supabase réel.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const source=readFileSync(resolve(ROOT,'assets/js/sinjira-admin.js'),'utf8');
const START="const status = document.querySelector('[data-admin-status]');";
const start=source.indexOf(START);
assert.ok(start>=0,'Script admin réel non trouvé');
const suffix=source.slice(start);
assert.ok(suffix.trimEnd().endsWith('init();'),'L’entrée admin a changé');
const body=suffix.slice(0,suffix.lastIndexOf('init();'))+'await init();';
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
const executeRealScript=new AsyncFunction(
  'document','getSupabase','requireUser','setStatus','isSinjiraBackendConfigured',body
);

class SafeNode {
  constructor(tagName='div') {
    this.tagName=tagName.toUpperCase();
    this.children=[];
    this._text='';
    this.colSpan=1;
    this.sinkCalls=0;
  }
  set textContent(value){this._text=String(value);this.children=[];}
  get textContent(){
    return this.children.length
      ? this.children.map(child=>child.textContent).join('')
      : this._text;
  }
  set innerHTML(value){
    this.sinkCalls++;
    throw new Error('INSÉCURITÉ : affectation de innerHTML ('+String(value).slice(0,25)+')');
  }
  set outerHTML(value){
    this.sinkCalls++;
    throw new Error('INSÉCURITÉ : affectation de outerHTML');
  }
  appendChild(child){
    assert.ok(child instanceof SafeNode);
    this.children.push(child);
    return child;
  }
  replaceChildren(...children){
    assert.ok(children.every(child=>child instanceof SafeNode));
    this.children=children;
    this._text='';
  }
}

function fakeDocument(){
  const nodes=new Map();
  for(const selector of [
    '[data-admin-status]','[data-total-contributions]',
    '[data-average-players]','[data-average-duration]',
    '[data-average-rating]','[data-result-table]',
    '[data-difficulty-table]','[data-card-table]'
  ]) nodes.set(selector,new SafeNode(selector.includes('table')?'tbody':'span'));
  return {
    nodes,
    document:{
      querySelector(selector){return nodes.get(selector)??null;},
      createElement(tag){
        assert.ok(['td','tr'].includes(tag),'Seul le DOM de tableaux est nécessaire');
        return new SafeNode(tag);
      },
    },
  };
}

async function execute(analytics, {dataOk=true, backendConfigured=true}={}){
  const {document,nodes}=fakeDocument();
  let invocations=0;
  let status=null;
  const data=dataOk?{ok:true,analytics}:{ok:false,error:'ACCESS_DENIED'};
  await executeRealScript(document,
    ()=>({functions:{async invoke(name,options){
      invocations++;
      assert.equal(name,'admin-analytics');
      assert.equal(options.body.game_slug,'fracture-du-reseau-mere');
      return {data,error:null};
    }}}),
    async pathname=>assert.equal(pathname,'/compte/connexion.html'),
    (_,message,kind)=>{status={message,kind};},
    ()=>backendConfigured
  );
  return {nodes,invocations,status};
}
function getCells(nodes,selector){
  const tbody=nodes.get(selector);
  assert.ok(tbody);
  assert.equal(tbody.sinkCalls,0,'Le conteneur ne doit pas être écrit en HTML');
  assert.ok(tbody.children.every(row=>row.tagName==='TR'));
  assert.ok(tbody.children.every(row=>row.children.every(cell=>cell.tagName==='TD')));
  return tbody.children.map(row=>row.children.map(cell=>cell.textContent));
}
function allNodes(nodes) {
  const found=[];
  function visit(node){found.push(node);node.children.forEach(visit);}
  nodes.forEach(visit);
  return found;
}
const payloads=[
  '<img src=x onerror=alert(1)>',
  '</td><script>globalThis.pwned=true</script><td>',
  '<svg/onload=alert(document.cookie)>',
  '<a href="javascript:alert(1)">Ouvrir</a>',
  '"><iframe srcdoc="<script>alert(1)</script>"></iframe>',
  'constructor',
  '__proto__',
  'toString'
];

test('les trois tableaux échappent les charges HTML en les rendant comme texte',async()=>{
  const results=Object.fromEntries(payloads.map((name,i)=>[name,payloads.length-i]));
  const difficulty=Object.fromEntries(payloads.slice().reverse().map((name,i)=>[name,i+1]));
  const top_cards=payloads.map((card,i)=>({card,count:i+1}));
  const r=await execute({
    total_contributions:88,average_player_count:3,
    average_duration_minutes:25,average_rating:4,
    results,difficulty,top_cards
  });
  assert.equal(r.invocations,1);
  assert.equal(r.status.kind,'success');
  assert.equal(r.nodes.get('[data-total-contributions]').textContent,'88');
  assert.equal(r.nodes.get('[data-average-duration]').textContent,'25 min');
  for(const [selector,expected] of [
    ['[data-result-table]',results],
    ['[data-difficulty-table]',difficulty]
  ]){
    const rows=getCells(r.nodes,selector);
    assert.equal(rows.length,payloads.length);
    assert.deepEqual(new Set(rows.map(row=>row[0])),new Set(Object.keys(expected)));
    for(const [label,count] of rows) assert.equal(count,String(expected[label]));
  }
  const cards=getCells(r.nodes,'[data-card-table]');
  assert.deepEqual(cards,top_cards.map(x=>[x.card,String(x.count)]));
  assert.ok(allNodes(r.nodes).every(node=>node.sinkCalls===0));
  assert.ok(allNodes(r.nodes).every(node=>['SPAN','TR','TD'].includes(node.tagName)));
  assert.equal(globalThis.pwned,undefined);
});

test('comptages et ordre décroissant préservés',async()=>{
  const r=await execute({
    total_contributions:3,
    results:{faible:1,fort:9,moyen:3},
    difficulty:{simple:4,complexe:1},
    top_cards:[{card:'Une carte',count:12}],
  });
  assert.deepEqual(getCells(r.nodes,'[data-result-table]'),
    [['fort','9'],['moyen','3'],['faible','1']]);
  assert.deepEqual(getCells(r.nodes,'[data-difficulty-table]'),
    [['simple','4'],['complexe','1']]);
  assert.deepEqual(getCells(r.nodes,'[data-card-table]'),
    [['Une carte','12']]);
});

test('absence de données : un seul TD avec colspan=2 et message texte',async()=>{
  const r=await execute({total_contributions:0,results:{},difficulty:{},top_cards:[]});
  for(const selector of ['[data-result-table]','[data-difficulty-table]','[data-card-table]']){
    assert.deepEqual(getCells(r.nodes,selector),[['Aucune donnée']]);
    const row=r.nodes.get(selector).children[0];
    assert.equal(row.children[0].colSpan,2);
  }
});

test('réponse partielle ou cartes de type incorrect : aucun sink HTML',async()=>{
  for(const analytics of [
    {results:null,difficulty:null,top_cards:null},
    {results:{},difficulty:{},top_cards:{card:'injecté'}},
    {results:{"":1},difficulty:{"":2},top_cards:[null,undefined,{}, {card:payloads[0],count:payloads[2]}]},
  ]){
    const r=await execute(analytics);
    assert.ok(getCells(r.nodes,'[data-card-table]').length>=1);
    assert.ok(getCells(r.nodes,'[data-result-table]').length>=1);
    assert.ok(allNodes(r.nodes).every(node=>node.sinkCalls===0));
  }
});

test('un refus du serveur ne rend aucun tableau admin',async()=>{
  const r=await execute({}, {dataOk:false});
  assert.equal(r.status.kind,'error');
  assert.equal(r.invocations,1);
  assert.equal(r.nodes.get('[data-result-table]').children.length,0);
});

test('sans backend configuré, aucune requête analytique n’est lancée',async()=>{
  const r=await execute({}, {backendConfigured:false});
  assert.equal(r.invocations,0);
  assert.equal(r.status.kind,'error');
});

test('aucune interpolation HTML de métriques n’est encore présente dans la source',()=>{
  assert.doesNotMatch(source,/\.(?:innerHTML|outerHTML)\s*=/);
  assert.doesNotMatch(source,/insertAdjacentHTML\s*\(/);
  assert.equal((source.match(/renderSafeAnalyticsTable\((?:results|difficulty|cards),/g)||[]).length,3);
  assert.match(source,/node\.replaceChildren\(\.\.\.elements\)/);
  assert.match(source,/name\.textContent\s*=/);
  assert.match(source,/value\.textContent\s*=/);
});
