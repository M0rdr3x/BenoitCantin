import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readingRatio, ratioFromScroll, scrollTopForRatio, chooseReadingPosition, shouldReplayReadingProgress}
  from '../../assets/js/sinjira-liseuse-position-v31.mjs';

test('la position de défilement demeure bornée et précise',()=>{
  assert.equal(readingRatio(-8),0);
  assert.equal(readingRatio(9),1);
  assert.equal(readingRatio('invalide'),0);
  assert.equal(readingRatio(.34567),.346);
  assert.equal(ratioFromScroll(300,1300,700),.5);
  assert.equal(scrollTopForRatio(.5,1300,700),300);
  assert.equal(ratioFromScroll(100,200,400),0);
});
test('la démo reprend le défilement exact de la page sauvegardée',()=>{
  assert.deepEqual(chooseReadingPosition({
    localPage:16,localRatio:.62,localUpdatedAt:'2026-11-07T13:00:00Z',
    totalPages:82,defaultPage:3
  }),{page:16,ratio:.62,source:'appareil'});
});
test('la progression récente du compte gagne, sans attribuer un défilement d’une autre page',()=>{
  assert.deepEqual(chooseReadingPosition({
    localPage:18,localRatio:.87,localUpdatedAt:'2026-11-07T12:00:00Z',
    serverPage:22,serverUpdatedAt:'2026-11-07T13:00:00Z',
    totalPages:520,defaultPage:4
  }),{page:22,ratio:0,source:'compte'});
});
test('une progression locale plus récente que celle du compte est préservée',()=>{
  assert.deepEqual(chooseReadingPosition({
    localPage:35,localRatio:.22,localUpdatedAt:'2026-11-07T14:00:00Z',
    serverPage:12,serverUpdatedAt:'2026-11-07T12:00:00Z',
    totalPages:520,defaultPage:4
  }),{page:35,ratio:.22,source:'appareil'});
});
test('les anciennes pages sauvegardées et les valeurs corrompues ont un repli sûr',()=>{
  assert.deepEqual(chooseReadingPosition({
    localPage:82,serverPage:900,totalPages:82,defaultPage:3
  }),{page:82,ratio:0,source:'appareil'});
  assert.deepEqual(chooseReadingPosition({
    localPage:'NaN',localRatio:999,serverPage:-1,totalPages:82,defaultPage:3
  }),{page:3,ratio:0,source:'debut'});
});

test('une sauvegarde cloud sur la même page ne doit pas effacer le défilement local',()=>{
  assert.deepEqual(chooseReadingPosition({
    localPage:27,localRatio:.79,localUpdatedAt:'2026-11-07T13:00:00Z',
    serverPage:27,serverUpdatedAt:'2026-11-07T13:00:01Z',
    totalPages:520,defaultPage:4
  }),{page:27,ratio:.79,source:'appareil'});
});

test('la position intrapage du compte plus récente est reprise sur un autre appareil',()=>{
  assert.deepEqual(chooseReadingPosition({
    localPage:18,localRatio:.11,localUpdatedAt:'2026-11-07T13:00:00Z',
    serverPage:22,serverRatio:.674,serverUpdatedAt:'2026-11-07T14:00:00Z',
    totalPages:520,defaultPage:4
  }),{page:22,ratio:.674,source:'compte'});
});
test('le compte plus récent l’emporte même sur la même page quand il a un emplacement précis',()=>{
  assert.deepEqual(chooseReadingPosition({
    localPage:24,localRatio:.8,localUpdatedAt:'2026-11-07T13:00:00Z',
    serverPage:24,serverRatio:.245,serverUpdatedAt:'2026-11-07T14:00:00Z',
    totalPages:520,defaultPage:4
  }),{page:24,ratio:.245,source:'compte'});
});
test('la progression locale la plus récente garde son emplacement sur cette page',()=>{
  assert.deepEqual(chooseReadingPosition({
    localPage:19,localRatio:.9,localUpdatedAt:'2026-11-07T16:00:00Z',
    serverPage:19,serverRatio:.1,serverUpdatedAt:'2026-11-07T13:00:00Z',
    totalPages:520,defaultPage:4
  }),{page:19,ratio:.9,source:'appareil'});
});
test('une ancienne ligne SQL sans scroll_ratio préserve la position locale de la même page',()=>{
  assert.deepEqual(chooseReadingPosition({
    localPage:12,localRatio:.67,localUpdatedAt:'2026-11-07T12:00:00Z',
    serverPage:12,serverRatio:null,serverUpdatedAt:'2026-11-07T14:00:00Z',
    totalPages:520,defaultPage:4
  }),{page:12,ratio:.67,source:'appareil'});
});
test('la position initiale zéro est distinguée du NULL hérité',()=>{
  assert.deepEqual(chooseReadingPosition({
    localPage:12,localRatio:.67,localUpdatedAt:'2026-11-07T12:00:00Z',
    serverPage:12,serverRatio:0,serverUpdatedAt:'2026-11-07T14:00:00Z',
    totalPages:520,defaultPage:4
  }),{page:12,ratio:0,source:'compte'});
});

test('V34 : reprise après coupure seulement si la sauvegarde locale est aussi récente',()=>{
  assert.equal(shouldReplayReadingProgress('2026-11-07T22:00:03Z','2026-11-07T22:00:02Z'),true);
  assert.equal(shouldReplayReadingProgress('2026-11-07T22:00:03Z','2026-11-07T22:00:03Z'),true);
  assert.equal(shouldReplayReadingProgress('2026-11-07T22:00:03Z','2026-11-07T22:00:05Z'),false);
});
test('V34 : ne pas rejouer une sauvegarde locale sans date valide ou contre une date serveur invalide',()=>{
  assert.equal(shouldReplayReadingProgress('invalide',null),false);
  assert.equal(shouldReplayReadingProgress(null,null),false);
  assert.equal(shouldReplayReadingProgress('2026-11-07T22:00:03Z',null),true);
  assert.equal(shouldReplayReadingProgress('2026-11-07T22:00:03Z','invalide'),false);
});
