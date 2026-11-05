#!/usr/bin/env node
"use strict";
// Simulation des affichages NOVA : aucune requête réseau ni donnée privée.
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const assert=require("node:assert/strict");

const root=path.resolve(__dirname,"..");
const script=fs.readFileSync(path.join(root,"projets/projet-nova/script.js"),"utf8");

const compassSource=fs.readFileSync(path.join(root,"projets/projet-nova/assets/boussole-electorale.js"),"utf8");
function testCompassEvidenceLinks(){
  const start=compassSource.indexOf("  const safeSourceUrl = value => {");
  const end=compassSource.indexOf("\n  };",start);
  assert.ok(start>=0&&end>start,"compass HTTPS-only source helper missing");
  const source=compassSource.slice(start,end+5);
  const safeSourceUrl=vm.runInNewContext(source+"\nsafeSourceUrl",{URL});
  for(const payload of [
    "javascript:alert(1)","data:text/html,<svg>","http://evil.invalid/",
    "//evil.invalid/path","https://user:password@evil.invalid/",
    'https://evil.invalid/" onmouseover="alert(1)',
    "not-a-url"
  ]){
    const result=safeSourceUrl(payload);
    if(payload.startsWith('https://evil.invalid/"')){
      assert.ok(!result.includes('"'),"external URL must be normalized and non-executable");
    }else{
      assert.equal(result,"","compass unsafe evidence source accepted: "+payload);
    }
  }
  assert.equal(safeSourceUrl("https://www.quebec.ca/ressources"),"https://www.quebec.ca/ressources");
  assert.equal((compassSource.match(/name="\$\{esc\(question\.id\)\}"/g)||[]).length,2,
    "compass radio input names must escape untrusted question IDs");
  const data=JSON.parse(fs.readFileSync(path.join(root,"projets/projet-nova/data/boussole-preuves-2026.json"),"utf8"));
  for(const item of data.evidenceRecords||[]){
    if(item.sourceUrl)assert.ok(safeSourceUrl(item.sourceUrl),
      "existing documentary HTTPS source must remain reachable");
  }
}


async function render({documents=[],finance=[],meetings=[],updates=[]}={}){
  const elements={
    docs:{innerHTML:""},finance:{innerHTML:""},
    meetings:{innerHTML:""},updates:{innerHTML:""},stamp:{textContent:""}
  };
  const selectors={
    "[data-doc-list]":documents.length?elements.docs:null,
    "[data-finance-table]":elements.finance,
    "[data-meetings-table]":elements.meetings,
    "[data-public-updates]":elements.updates,
    "[data-updates-date]":elements.stamp,
    "link[data-nova-institutionnel]":{},
    "link[data-nova-maturite]":{}
  };
  const data={
    "data/comptabilite.json":{entries:finance},
    "data/rencontres.json":{entries:meetings},
    "data/actualites.json":{updated:"2026-08-26",entries:updates}
  };
  const context=vm.createContext({
    window:{NOVA_DOCUMENTS:documents},
    document:{
      readyState:"complete",
      body:{getAttribute(){return ""}},
      documentElement:{getAttribute(){return "true"}},
      querySelector(selector){return selectors[selector]??null},
      querySelectorAll(){return []},
      createElement(){throw Error("unexpected DOM creation")},
      addEventListener(){throw Error("unexpected DOM listener")}
    },
    fetch(url){
      assert.ok(Object.hasOwn(data,url),"Unexpected fetch: "+url);
      return Promise.resolve({json:()=>Promise.resolve(data[url])});
    },
    console
  });
  vm.runInContext(script,context,{filename:"nova-script.js",timeout:1000});
  await new Promise(resolve=>setImmediate(resolve));
  await new Promise(resolve=>setImmediate(resolve));
  return {elements,context};
}

(async()=>{
  testCompassEvidenceLinks();
  const payload='<img src=x onerror="alert(1)">';
  const malicious={
    documents:[
      {id:"safe",section:payload,title:payload,description:"<script>alert(1)</script>",
       path:"javascript:alert(1)"},
      {id:"valid",section:"Documents",title:"Public",description:"PDF permis",
       path:"documents/01_Resume_Officiel_1_Page_Projet_Nova.pdf"},
      {id:"escape",section:"Documents",title:"X",description:"Document bloqué",
       path:"documents/../secret.pdf"}
    ],
    finance:[{date:"2026-08-26",type:"dépense",categorie:payload,
      description:'<svg/onload=alert(1)>',fournisseur_ou_source:'</td><script>alert(1)</script>',
      montant:100,statut:'"<iframe src="https://evil.invalid">'}],
    meetings:[{date:"2026-08-26",type:"réunion",sujet:payload,
      participants_resume:"<iframe>",resume_public:"</td><script>",
      suivi:"<svg/onload=alert(1)>",statut_publication:'<a href="javascript:alert(1)">'}],
    updates:[{date:'2026-08-26" onmouseover="alert(1)',type:payload,
      title:"<script>alert(1)</script>",summary:payload,
      link:'javascript:alert(1)',link_label:"<svg/onload=alert(1)>"}]
  };
  const {elements,context}=await render(malicious);
  for(const name of ["docs","finance","meetings","updates"]){
    const html=elements[name].innerHTML;
    assert.ok(html.length>20,name+": test output missing");
    for(const forbidden of ["<script", "<svg", "<iframe", "<img", 'href="javascript:']){
      assert.ok(!html.includes(forbidden),name+": dangerous DOM token "+forbidden);
    }
    assert.ok(html.includes("&lt;"),name+": text was not escaped");
  }
  assert.ok(elements.docs.innerHTML.includes('href="documents/01_Resume_Officiel_1_Page_Projet_Nova.pdf"'));
  assert.ok(!elements.docs.innerHTML.includes('href="documents/../secret.pdf"'));
  assert.ok(elements.updates.innerHTML.includes("&quot; onmouseover=&quot;"));
  assert.ok(!elements.updates.innerHTML.includes('<a class="text-link" href='));
  const safe=vm.runInContext("NOVA_SAFE_DOM",context);
  assert.equal(safe.escape('<&"\''),'&lt;&amp;&quot;&#39;');
  for(const bad of ["javascript:alert(1)","data:text/html,<svg>","//evil.invalid","../admin.html",
    "/admin.html","https://evil.invalid/x.html",'foo.html" onclick="alert(1)']){
    assert.equal(safe.pageHref(bad),"","unsafe news href accepted: "+bad);
  }
  for(const bad of ["javascript:alert(1)","documents/../secret.pdf","/private.pdf",
    "documents/malicious.svg","documents/evil.pdf?download=1"]){
    assert.equal(safe.pdfHref(bad),"","unsafe PDF href accepted: "+bad);
  }
  const good=await render({updates:[{date:"2026-08-26",type:"NOVA",
    title:"Actualités",summary:"Résumé public",link:"finances.html",link_label:"Détails"}]});
  assert.ok(good.elements.updates.innerHTML.includes('href="finances.html"'),
    "public news links must stay usable");
  console.log("OK: NOVA JSON DOM, documents and news links reject synthetic XSS payloads.");
})().catch(error=>{console.error(error);process.exitCode=1});
