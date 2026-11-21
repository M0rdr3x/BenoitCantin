import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {planReaderScreenTurn} from '../../assets/js/sinjira-liseuse-screen-turn-v54.mjs';

const turn=(direction,top=0,height=3000,view=600,mode='texte')=>
  planReaderScreenTurn({direction,mode,scrollTop:top,scrollHeight:height,clientHeight:view});

test('mode texte : un balayage parcourt un écran visible sans sauter du contenu',()=>{
  assert.deepEqual(turn(1,200),{kind:'scroll',top:728});
  assert.deepEqual(turn(-1,900),{kind:'scroll',top:372});
  assert.deepEqual(turn(1,2350),{kind:'scroll',top:2400});
  assert.deepEqual(turn(-1,20),{kind:'scroll',top:0});
});

test('mode texte : le changement de page PDF n’arrive qu’aux extrémités',()=>{
  assert.deepEqual(turn(1,2400),{kind:'page',delta:1,end:false});
  assert.deepEqual(turn(-1,0),{kind:'page',delta:-1,end:true});
  assert.deepEqual(turn(1,2399.2),{kind:'page',delta:1,end:false});
  assert.deepEqual(turn(-1,1),{kind:'page',delta:-1,end:true});
});

test('mode texte court : pas de scroll inutile ni boucle de pagination',()=>{
  assert.deepEqual(turn(1,0,550,600),{kind:'page',delta:1,end:false});
  assert.deepEqual(turn(-1,0,550,600),{kind:'page',delta:-1,end:true});
  assert.deepEqual(turn(1,100,600,600),{kind:'page',delta:1,end:false});
});

test('mode PDF : conserver le passage par page, sans naviguer en fin de page arrière',()=>{
  assert.deepEqual(turn(1,600,3000,600,'page'),{kind:'page',delta:1,end:false});
  assert.deepEqual(turn(-1,600,3000,600,'page'),{kind:'page',delta:-1,end:false});
});

test('paramètres invalides et tailles hors norme ne cassent pas le lecteur',()=>{
  assert.deepEqual(turn(0),{kind:'none'});
  assert.deepEqual(turn(2),{kind:'none'});
  assert.deepEqual(turn(1,NaN,3000,600),{kind:'page',delta:1,end:false});
  assert.deepEqual(turn(-1,100,NaN,600),{kind:'page',delta:-1,end:true});
  assert.deepEqual(turn(1,100,3000,0),{kind:'page',delta:1,end:false});
  const result=turn(1,-999,1200,320);
  assert.equal(result.kind,'scroll');
  assert.ok(result.top>=0&&result.top<=880);
});

test('contrat intégration : clavier limité au lecteur, reprise ratio V31 et sélection préservée',()=>{
  const js=readFileSync(new URL('../../assets/js/sinjira-liseuse-v26.js',import.meta.url),'utf8');
  const html=readFileSync(new URL('../../compte/liseuse.html',import.meta.url),'utf8');
  const css=readFileSync(new URL('../../assets/css/sinjira-liseuse-v26.css',import.meta.url),'utf8');
  assert.match(js,/planReaderScreenTurn\(/);
  assert.match(js,/turnVisibleReadingScreen\(dx<0\?1:-1\)/);
  assert.match(js,/swipeViewer\.addEventListener\('keydown'/);
  assert.doesNotMatch(js,/document\.addEventListener\('keydown'/);
  assert.match(js,/state\.restorePending=end\?1:0/);
  assert.match(js,/window\.getSelection\(\)\?\.toString\(\)/);
  assert.match(js,/ratioFromScroll\(viewer\.scrollTop/);
  assert.match(html,/aria-describedby="reader-turn-help"/);
  assert.match(html,/aria-keyshortcuts="ArrowLeft ArrowRight PageUp PageDown"/);
  assert.match(css,/\.reader-viewer:focus-visible/);
  assert.match(html,/glissez vers la gauche pour avancer/);
  assert.match(html,/vers la droite pour revenir en arrière/);
});
