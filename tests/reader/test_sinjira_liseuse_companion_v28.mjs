import {test} from 'node:test';
import assert from 'node:assert/strict';
import {normalizeSearch,findMatches,makeExcerpt,safeReaderMark} from '../../assets/js/sinjira-liseuse-companion-v28.mjs';

test('la recherche est insensible aux accents et à la casse en français',()=>{
  assert.equal(normalizeSearch('Étrange RÉSEAU'), 'etrange reseau');
  assert.deepEqual(findMatches('Le Réseau-Mère rejoint le réseau.', 'RESEAU'),[3,26]);
});
test('recherche vide, trop courte ou trop longue : aucun résultat',()=>{
  assert.deepEqual(findMatches('Bonjour',''),[]);
  assert.deepEqual(findMatches('Bonjour','b'),[]);
  assert.deepEqual(findMatches('Bonjour','a'.repeat(101)),[]);
});
test('la recherche trouve plusieurs occurrences sans boucle infinie',()=>{
  assert.deepEqual(findMatches('abc abc abc','abc'),[0,4,8]);
  assert.deepEqual(findMatches('aaaaaa','aa',2),[0,2]);
});
test('les extraits sont tronqués et ne sortent pas des limites du document',()=>{
  const text='Un début. '+('Texte avec des accents. '.repeat(30))+'Une fin.';
  const excerpt=makeExcerpt(text,10,5,90);
  assert.ok(excerpt.length<=130);
  assert.ok(excerpt.includes('Texte'));
  assert.equal(makeExcerpt('Bonjour',0,2),'Bonjour');
});
test('les repères inconnus et les pages hors borne sont rejetés',()=>{
  assert.equal(safeReaderMark({page:0,kind:'bookmark'}),null);
  assert.equal(safeReaderMark({page:521,kind:'bookmark'}),null);
  assert.equal(safeReaderMark({page:1,kind:'html'}),null);
  assert.equal(safeReaderMark(null),null);
});
test('les notes et citations sont bornées sans rendu HTML',()=>{
  const mark=safeReaderMark({id:'a',page:11,kind:'note',
    quote:'<img src=x onerror=alert(1)>'.repeat(100),note:'a'.repeat(2500),created_at:'ok'});
  assert.equal(mark.page,11);
  assert.equal(mark.quote.length,280);
  assert.equal(mark.note.length,1500);
  assert.ok(mark.quote.startsWith('<img'));
});
