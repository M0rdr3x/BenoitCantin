import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {canTurnReaderScreen} from '../../assets/js/sinjira-liseuse-screen-turn-v54.mjs';

const can=(page,direction,top=0,mode='texte',height=2500,view=500,total=10)=>
  canTurnReaderScreen({direction,mode,scrollTop:top,scrollHeight:height,
    clientHeight:view,page,totalPages:total});

test('page PDF initiale: le bouton retour est désactivé uniquement en haut de la première page',()=>{
  assert.equal(can(1,-1,0),false);
  assert.equal(can(1,-1,600),true);
  assert.equal(can(1,1,0),true);
});

test('dernière page PDF: le bouton suivant reste disponible tant que le texte continue',()=>{
  assert.equal(can(10,1,200),true);
  assert.equal(can(10,1,2000),false);
  assert.equal(can(10,-1,0),true);
});

test('page intérieure courte et mode PDF: commandes bornées à la première et dernière page',()=>{
  assert.equal(can(1,-1,0,'texte',450,500),false);
  assert.equal(can(1,1,0,'texte',450,500),true);
  assert.equal(can(10,1,0,'texte',450,500),false);
  assert.equal(can(1,-1,300,'page'),false);
  assert.equal(can(10,1,300,'page'),false);
  assert.equal(can(5,-1,300,'page'),true);
  assert.equal(can(5,1,300,'page'),true);
});

test('valeurs incorrectes: aucun bouton n’est activé par une page invalide',()=>{
  for(const page of [0,-1,11,1.5,NaN]){
    assert.equal(can(page,1,2000,'texte'),false);
  }
  assert.equal(can(5,0,2000),false);
  assert.equal(can(5,1,0,'page',1000,500,0),false);
});

test('contrat UI: boutons, swipe et clavier partagent la même action',()=>{
  const js=readFileSync(new URL('../../assets/js/sinjira-liseuse-v26.js',import.meta.url),'utf8');
  const html=readFileSync(new URL('../../compte/liseuse.html',import.meta.url),'utf8');
  const checks=[
    /previous\.disabled=!canTurnReaderScreen\(/,
    /next\.disabled=!canTurnReaderScreen\(/,
    /\$\('reader-previous'\)\.addEventListener\('click',\(\)=>turnVisibleReadingScreen\(-1\)\)/,
    /\$\('reader-next'\)\.addEventListener\('click',\(\)=>turnVisibleReadingScreen\(1\)\)/,
    /turnVisibleReadingScreen\(dx<0\?1:-1\)/,
    /swipeViewer\.addEventListener\('keydown'/,
    /updateScreenControls\(\)/,
    /state\.restorePending=end\?1:0/
  ];
  for(const pattern of checks)assert.match(js,pattern);
  assert.match(html,/aria-controls="reader-viewer"/);
  assert.match(html,/id="reader-turn-help"/);
  assert.match(html,/Les champs Page et Progression/);
  assert.doesNotMatch(js,/localStorage\.setItem\([^;]*reader-text/);
});

test('V56 : les cinq commandes typographiques préservent la position et rafraîchissent les flèches',()=>{
  const js=readFileSync(new URL('../../assets/js/sinjira-liseuse-v26.js',import.meta.url),'utf8');
  const html=readFileSync(new URL('../../compte/liseuse.html',import.meta.url),'utf8');
  assert.match(js,/function updateReaderTypography\(applySetting\)/);
  assert.match(js,/pendingTextRelayout===transaction/);
  assert.match(js,/state\.pdf!==transaction\.pdf\|\|state\.page!==transaction\.page/);
  assert.match(js,/viewer\.scrollTop=scrollTopForRatio\(transaction\.ratio/);
  assert.match(js,/state\.positionRatio=ratioFromScroll\(viewer\.scrollTop/);
  assert.match(js,/updateScreenControls\(\);\s*persist\(\);/);
  for(const name of ['reader-size','reader-font','reader-line-height',
    'reader-text-width','reader-letter-spacing']){
    const marker=name==='reader-size'?'input':'change';
    assert.ok(js.includes("'"+name+"').addEventListener('"+marker+"'"),name+' événement absent');
  }
  assert.equal((js.match(/updateReaderTypography\(\(\)=>/g)||[]).length,5);
  assert.match(html,/sinjira-liseuse-v26\.js\?v=34\.11\.22\.1/);
});
