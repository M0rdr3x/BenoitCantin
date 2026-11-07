import {test} from 'node:test';
import assert from 'node:assert/strict';
import {normalizeSearch,findMatches,makeExcerpt,findQuoteRange,safeReaderMark,findMatchRanges} from '../../assets/js/sinjira-liseuse-companion-v28.mjs';

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

test('une sélection sur plusieurs lignes PDF conserve son surlignage',()=>{
  const text='Le récit\n    traverse les frontières.';
  const result=findQuoteRange(text,'Le récit traverse les frontières.');
  assert.ok(result);
  assert.equal(text.slice(result.start,result.end),text);
  assert.equal(findQuoteRange(text,'introuvable'),null);
});

test('la recherche retrouve les indices exacts après les accents décomposés',()=>{
  const source='Cafe\u0301 au soleil. Un ÉTÉ réussi.';
  const accent=findMatchRanges(source,'CAFÉ');
  assert.equal(accent.length,1);
  assert.equal(source.slice(accent[0].start,accent[0].end),'Cafe\u0301');
  const summer=findMatchRanges(source,'ete');
  assert.equal(summer.length,1);
  assert.equal(source.slice(summer[0].start,summer[0].end),'ÉTÉ');
  assert.deepEqual(findMatches(source,'ete'),[source.indexOf('ÉTÉ')]);
});
test('la recherche respecte les indices UTF-16 après les emojis et évite les faux résultats',()=>{
  const source='📖 Une étonnante découverte. Étonnante encore.';
  const hits=findMatchRanges(source,'ETONNANTE');
  assert.equal(hits.length,2);
  assert.equal(source.slice(hits[0].start,hits[0].end),'étonnante');
  assert.equal(source.slice(hits[1].start,hits[1].end),'Étonnante');
  assert.deepEqual(findMatchRanges(source,'x'),[]);
});
test('la recherche plafonne les occurrences pour éviter un rendu bloquant',()=>{
  const source='roman '.repeat(5000);
  assert.equal(findMatchRanges(source,'roman',25).length,25);
  assert.equal(findMatchRanges(source,'roman',100000).length,1000);
});
