import assert from 'node:assert/strict';
import test from 'node:test';
import { createReaderCompanion } from '../../assets/js/sinjira-liseuse-companion-v28.mjs';

class FakeElement {
  constructor() {
    this.children=[];
    this.textContent='';
    this.value='';
    this.hidden=false;
    this.disabled=false;
    this.dataset={};
    this.style={};
    this.listeners=new Map();
    this.classList={add(){},remove(){},toggle(){}};
  }
  addEventListener(event, callback) { this.listeners.set(event, callback); }
  click() { this.listeners.get('click')?.({ preventDefault() {} }); }
  replaceChildren(...children) { this.children=children; this.textContent=''; }
  append(...children) { this.children.push(...children); }
  setAttribute(name, value) { this[name]=value; }
  getAttribute(name) { return this[name] ?? null; }
  querySelectorAll() { return []; }
  querySelector() { return null; }
  scrollTo() {}
  focus() {}
}

function deferred() {
  let resolve;
  const promise=new Promise(accept=>{resolve=accept});
  return { promise, resolve };
}
function setup({user='alpha',novel='novel-one'}={}) {
  const elements=new Map();
  const getElement=id=>{
    if(!elements.has(id))elements.set(id,new FakeElement());
    return elements.get(id);
  };
  globalThis.document={
    body:{classList:{add(){},remove(){},toggle(){}}},
    getElementById:getElement,
    createElement(){return new FakeElement()},
    createTextNode(text){return {textContent:text}},
    addEventListener(){},
  };
  globalThis.window={getSelection:()=>null,confirm:()=>true};
  globalThis.localStorage={getItem:()=>null,setItem(){}};
  globalThis.requestAnimationFrame=cb=>cb();
  const request=deferred();
  let currentUser={id:user}, currentNovel=novel;
  const query={
    select(){return this},
    eq(){return this},
    order(){return this},
    limit(){return request.promise},
    insert(){return this},
    delete(){return this},
    single(){return request.promise},
  };
  const controller=createReaderCompanion({
    isFull:true,
    getPdf:()=>({numPages:520}),
    getPage:()=>4,
    goToPage(){},
    getChapters:()=>[[1,'Couverture'],[5,'Chapitre suivant']],
    getUser:()=>currentUser,
    getNovelId:()=>currentNovel,
    getSupabase:()=>({from:()=>query}),
    getTextAtPage:async()=> 'Contenu de test',
    setReadingPage(){},
    invalidateRender(){},
    renderSinglePage(){},
    onEnterContinuous(){},
  });
  return {
    controller,
    elements,
    getElement,
    request,
    changeUser:newUser=>{currentUser={id:newUser}},
    changeNovel:newNovel=>{currentNovel=newNovel},
  };
}

const privateMark={
  id:'mark-private', page:4,kind:'note',quote:'',
  note:'Une note privée qui ne doit pas réapparaître',
  created_at:'2026-11-07T00:00:00Z',
};

test('déconnexion durant les notes : la réponse en attente ne réaffiche aucune note',async()=>{
  const a=setup();
  const pending=a.controller.ready();
  a.controller.close();
  a.request.resolve({data:[privateMark],error:null});
  await pending;
  assert.equal(a.getElement('reader-marks-list').children.length,0);
  assert.equal(a.getElement('reader-note-input').value,'');
  assert.equal(a.getElement('reader-search-results').children.length,0);
  assert.equal(a.getElement('reader-selection-preview').textContent,'');
  a.controller.onTextRendered();
  a.controller.onPageChange();
  assert.equal(a.getElement('reader-marks-list').children.length,0);
});

test('changement de compte pendant la synchronisation : aucune note de l ancien compte',async()=>{
  const a=setup();
  const pending=a.controller.ready();
  a.changeUser('beta');
  a.request.resolve({data:[privateMark],error:null});
  await pending;
  assert.equal(a.getElement('reader-marks-list').children.length,0);
});

test('changement de roman pendant la synchronisation : notes ignorées',async()=>{
  const a=setup();
  const pending=a.controller.ready();
  a.changeNovel('novel-two');
  a.request.resolve({data:[privateMark],error:null});
  await pending;
  assert.equal(a.getElement('reader-marks-list').children.length,0);
});

test('fermeture de chapitre continu : aucun contenu mémorisé dans le DOM',async()=>{
  const a=setup();
  const button=a.getElement('reader-continuous');
  button.click();
  const chapter=a.getElement('reader-chapter-scroll');
  assert.equal(chapter.hidden,false);
  a.controller.close();
  assert.equal(chapter.hidden,true);
  assert.equal(chapter.children.length,0);
  assert.equal(a.getElement('reader-continuous')['aria-pressed'],'false');
  // Les événements tardifs de l'ancienne liseuse sont sans effet.
  button.click();
  assert.equal(chapter.children.length,0);
});
