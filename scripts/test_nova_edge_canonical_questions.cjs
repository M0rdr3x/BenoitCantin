#!/usr/bin/env node
"use strict";
// Vérification SANS réseau de la fonction Edge réelle : aucune publication ni
// aucun bulletin ne peut utiliser un questionnaire de base modifié.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const edge=fs.readFileSync(path.join(root,"supabase/functions/nova-civic-poll/index.ts"),"utf8");
const poll=JSON.parse(fs.readFileSync(path.join(root,
  "projets/projet-nova/data/sondage-citoyen-v1.json"),"utf8"));
assert.equal(poll.published,false,"Le corpus candidat ne peut pas être ouvert par ces tests");
assert.equal(poll.questions.length,8);
const definition=edge.match(/const CANONICAL_QUESTIONS = Object\.freeze\((\[[\s\S]*?\])\);\nfunction matchesApprovedQuestions\(rows: unknown\): boolean \{([\s\S]*?)\n\}/);
assert.ok(definition,"Verrou serveur immuable du questionnaire introuvable");
const fnSource="const CANONICAL_QUESTIONS = Object.freeze("+definition[1]+");\n"+
  "function matchesApprovedQuestions(rows) {"+definition[2]+"\n}\n"+
  "globalThis.check=matchesApprovedQuestions; globalThis.canonical=CANONICAL_QUESTIONS;";
const ctx={};
vm.runInNewContext(fnSource,ctx,{timeout:2000});
const expected=poll.questions.map(q=>({question_id:q.id,ordinal:q.ordinal,question_text:q.text}));
assert.deepEqual(JSON.parse(JSON.stringify(ctx.canonical)),expected,
  "Les huit textes côté serveur doivent être identiques au JSON canonique public");
const fresh=()=>JSON.parse(JSON.stringify(expected));
assert.equal(ctx.check(expected),true,"Huit questions officielles acceptées");

const invalid=[
  null,undefined,{},[],fresh().slice(0,7),[...fresh(),fresh()[0]],
  (()=>{const x=fresh();x.reverse();return x;})(),
  (()=>{const x=fresh();x[0].question_id="q99";return x;})(),
  (()=>{const x=fresh();x[0].question_id=x[1].question_id;return x;})(),
  (()=>{const x=fresh();x[0].ordinal=2;return x;})(),
  (()=>{const x=fresh();x[0].ordinal="1";return x;})(),
  (()=>{const x=fresh();x[0].question_text+=" ";return x;})(),
  (()=>{const x=fresh();x[0].question_text="Message de campagne";return x;})(),
  (()=>{const x=fresh();x[0].question_text=null;return x;})(),
  (()=>{const x=fresh();x[0]=null;return x;})()
];
for(const example of invalid)assert.equal(ctx.check(example),false,
  "Jamais accepter un corpus serveur partiel, modifié, réordonné ou dupliqué");

const getSection=edge.slice(edge.indexOf("async function publicResults()"),
  edge.indexOf("async function confirmCaptcha("));
const postSection=edge.slice(edge.indexOf("Deno.serve(async"),
  edge.lastIndexOf("});"));
assert.match(getSection,/!matchesApprovedQuestions\(questions\)/,
  "Toute publication GET exige le corpus officiel, pas seulement huit lignes");
assert.match(postSection,/!matchesApprovedQuestions\(questions\)/,
  "Tout envoi POST exige le corpus officiel avant la procédure SQL");
assert.match(postSection,/&select=question_id,ordinal,question_text&order=ordinal.asc/,
  "Le POST doit lire les textes et leur ordre avant de valider");
assert.match(postSection,/questionnaire_non_approuve/,
  "Dérive serveur : réponse 503 sans écriture dans la base");
assert.ok(postSection.indexOf("!matchesApprovedQuestions(questions)") <
  postSection.indexOf('db("rpc/nova_poll_submit"'),
  "Aucune écriture avant validation du questionnaire serveur");
assert.match(edge,/NOVA_POLL_APPROVED_VERSION/);
assert.match(edge,/NOVA_POLL_ENABLED/);
console.log("OK NOVA : huit textes, ordre et identifiants liés au questionnaire officiel; mutations rejetées; publication et votes bloqués si dérive.");
