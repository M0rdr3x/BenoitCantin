'use strict';
// Garde de confidentialité: chemins de portrait réellement consommés par
// trois modules SINJIRA. Aucune requête réseau, aucun compte ou secret.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {pathToFileURL}=require('node:url');

const ROOT=path.resolve(__dirname,'..');
const read=file=>fs.readFileSync(path.join(ROOT,file),'utf8');
const FILES=[
  ['assets/js/sinjira-community-character.js','compte/reseau-personnage.html',
    'sinjira-community-character.js?v=24.4.79-portrait-guard'],
  ['assets/js/sinjira-messages-character.js','compte/messages-personnage.html',
    'sinjira-messages-character.js?v=24.4.71-portrait-guard'],
  ['assets/js/sinjira-mon-personnage.js','compte/mon-personnage.html',
    'sinjira-mon-personnage.js?v=24.4.85-portrait-guard']
];
const GOOD=[
  '/assets/media/characters/abysstime.webp',
  '/assets/media/sinjira-emblem.webp',
  '/assets/media/characters/personnage_2.png',
  '/projets/sinjira/media/cover-01.jpeg',
  '/assets/images/portrait.avif'
];
const BAD=[
  null,undefined,42,{},[],true,'',' /assets/media/characters/a.png',
  '/assets/media/characters/a.png ','//evil.invalid/track.png',
  '///evil.invalid/track.png','/\\evil.invalid/track.png',
  'http://evil.invalid/track.png','https://evil.invalid/track.png',
  'javascript:alert(1)','data:image/svg+xml,<svg/>',
  '/assets/media/characters/a.svg',
  '/assets/media/characters/a.html',
  '/assets/media/characters/a.pdf',
  '/compte/notifications.png','/admin/sinjira/portrait.webp',
  '/assets/media/characters/a.png?token=private',
  '/assets/media/characters/a.png#private',
  '/assets/media/characters/a.png&evil=1',
  '/assets/media/characters/a.png%3fsecret',
  '/assets/media/characters/%2e%2e/secret.png',
  '/assets/media/characters/../secret.png',
  '/assets/media/./characters/secret.png',
  '/assets/media//characters/secret.png',
  '/assets/media/characters/a\\b.png',
  '/assets/media/characters/a\n.png',
  '/assets/media/characters/a\t.png',
  '/assets/media/characters/a\r.png',
  '/assets/media/characters/a\u007f.png',
  '/assets/media/characters/<svg>.png',
  '/assets/media/characters/a".png',
  '/assets/media/characters/a'.padEnd(2050,'x')+'.png'
];
const escapeHtml=v=>String(v).replace(/[&<>"']/g,c=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'
})[c]);
let checks=0;

async function main(){
  const url=pathToFileURL(path.join(ROOT,'assets/js/sinjira-character-portrait-url.mjs')).href;
  const {safeCharacterPortraitPath:guard}=await import(url);
  for(const p of GOOD){assert.equal(guard(p),p);checks++;}
  for(const p of BAD){assert.equal(guard(p),'','Image suspecte acceptée: '+String(p));checks++;}
  const fallback='/assets/media/sinjira-emblem.webp';
  for(const [script,html,version] of FILES){
    const content=read(script),page=read(html);
    assert.match(content,/import \{safeCharacterPortraitPath\} from '\.\/sinjira-character-portrait-url\.mjs';/);
    assert.ok(page.includes(version),script+': nouvelle version absente du HTML');
    checks+=2;
    const start=content.indexOf('function portrait(');
    const next=content.indexOf(script.endsWith('sinjira-mon-personnage.js')?'\nfunction timeline(':'\nfunction fail(',start);
    assert.ok(start>=0&&next>start,script+': fonction portrait introuvable');
    const body=content.slice(start,next);
    const context=vm.createContext({safeCharacterPortraitPath:guard,escapeHtml});
    vm.runInContext(body+'\nthis.actualPortrait=portrait;',context,{timeout:1200});
    const fn=context.actualPortrait;
    for(const image of GOOD){
      const actual=script.endsWith('sinjira-mon-personnage.js')?fn(image,'AbyssTime'):fn({portrait_path:image});
      assert.ok(actual.includes(image),script+': portrait local légitime supprimé');
      checks++;
    }
    for(const image of BAD){
      const actual=script.endsWith('sinjira-mon-personnage.js')?fn(image,'Test'):fn({portrait_path:image});
      if(script.endsWith('sinjira-mon-personnage.js')){
        assert.equal(actual,'',script+': portrait externe/ambigu affiché '+String(image));
      }else{
        assert.equal(actual,fallback,script+': image externe/ambigu affichée '+String(image));
      }
      checks++;
    }
  }
  console.log('PASS: '+checks+' contrôles : 3 parcours personnages, images locales, refus de tiers, SVG, traversées et cache.');
}
main().catch(error=>{console.error('FAIL: frontière des portraits',error);process.exitCode=1;});
