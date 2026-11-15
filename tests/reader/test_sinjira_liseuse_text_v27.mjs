import assert from 'node:assert/strict';
import {test} from 'node:test';
import {pdfTextToParagraphs,speechTextChunks} from '../../assets/js/sinjira-liseuse-text-v27.mjs';

const fragment=(str,x,y,width,hasEOL=false,height=12)=>({str,transform:[1,0,0,1,x,y],width,hasEOL,height});

test('le texte de deux lignes du PDF se reformate en lecture continue',()=>{
  const items=[
    fragment('Cette ',10,500,35),fragment('phrase',45,500,40,true),
    fragment('continue',10,485,50),fragment(' normalement.',64,485,74,true),
  ];
  assert.equal(pdfTextToParagraphs(items),'Cette phrase continue normalement.');
});

test('les écarts de mise en page produisent des paragraphes, sans interpréter le contenu comme HTML',()=>{
  const items=[
    fragment('<Un texte>',10,500,70,true),
    fragment('Un autre paragraphe.',10,455,120,true),
  ];
  assert.equal(pdfTextToParagraphs(items),'<Un texte>\n\nUn autre paragraphe.');
});

test('les caractères séparés en segments gardent leur graphie',()=>{
  const items=[
    fragment('B',0,100,7),fragment('o',7,100,7),fragment('n',14,100,7),
    fragment(' ',21,100,3),fragment('jour',24,100,23,true),
  ];
  assert.equal(pdfTextToParagraphs(items),'Bon jour');
});

test('les pages non textuelles sont gérées sans inventer du contenu',()=>{
  assert.equal(pdfTextToParagraphs([]),'');
  assert.equal(pdfTextToParagraphs(null),'');
  assert.equal(pdfTextToParagraphs([{str:'',hasEOL:true}]),'');
});

test('la synthèse vocale découpe les longues phrases sans perdre de mots',()=>{
  const original=('Voici une phrase qui peut être lue. ').repeat(35).trim();
  const chunks=speechTextChunks(original,185);
  assert.ok(chunks.length>2);
  assert.ok(chunks.every(c=>c.length<=185));
  assert.equal(chunks.join(' '),original);
});

test('aucun passage privé n est écrit dans les préférences, et les entrées vides ne sont pas lues',()=>{
  assert.deepEqual(speechTextChunks(''),[]);
  assert.deepEqual(speechTextChunks('  \n '),[]);
  assert.deepEqual(speechTextChunks('Bonjour.'),['Bonjour.']);
});
