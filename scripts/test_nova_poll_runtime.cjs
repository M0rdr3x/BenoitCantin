#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const assert=require("node:assert/strict");
const src=fs.readFileSync(path.join(__dirname,"../projets/projet-nova/assets/sondage-citoyen.js"),"utf8");
const html=fs.readFileSync(path.join(__dirname,"../projets/projet-nova/sondage-citoyen.html"),"utf8");
assert.match(html,/<button[^>]+id="poll-send"[^>]*\bdisabled\b/);
const elements=new Map();
const elem=id=>{if(!elements.has(id))elements.set(id,{disabled:false,checked:false,textContent:""});return elements.get(id);};
const selected=new Set();
let voted=false;
const context={
  document:{getElementById:elem,querySelector:selector=>{
    const m=selector.match(/input\[name="([^"]+)"\]:checked/);
    return m&&selected.has(m[1])?{value:"0"}:null;
  },addEventListener:()=>{}},
  localStorage:{getItem:key=>key==="nova_poll_sent_v1"&&voted?"yes":null,setItem:()=>{}},
  window:{},crypto:{getRandomValues:()=>{throw new Error("pas de jeton en test");}},console
};
context.globalThis=context;
const end=src.lastIndexOf("})();");
assert.ok(end>0);
vm.runInNewContext(src.slice(0,end)+';globalThis.__pollTest={updateButton,setOpen:v=>open=v,setCaptcha:v=>captchaToken=v,setSending:v=>sending=v,setQuestions:v=>questions=v};'+src.slice(end),context,{timeout:2000});
const t=context.__pollTest;
elem("poll-adult").checked=true;elem("poll-agree").checked=true;
t.setQuestions([{id:"q02"}]);selected.add("q02");
t.setCaptcha("jeton-de-test");t.setOpen(false);t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Consultation fermée");
t.setOpen(true);t.updateButton();
assert.equal(elem("poll-send").disabled,false,"Ouvert et consentement complet");
selected.clear();t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Aucune réponse");
selected.add("q02");t.setCaptcha("");t.updateButton();
assert.equal(elem("poll-send").disabled,true,"CAPTCHA absent");
t.setCaptcha("jeton-de-test");elem("poll-adult").checked=false;t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Âge non confirmé");
elem("poll-adult").checked=true;voted=true;t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Déjà participé");
voted=false;t.setSending(true);t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Envoi en cours");
t.setSending(false);t.setOpen(false);t.updateButton();
assert.equal(elem("poll-send").disabled,true,"Retour en mode fermé");
console.log("OK sondage : désactivé hors ouverture, âge, anti-robot, choix et doublon.");
