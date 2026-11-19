/** V51.6 — banc JS isolé : aucun vrai compte, PDF ni appel Supabase.
 * Exécute les fonctions originales V26 dans un contexte DOM simulé. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

const source=readFileSync(new URL('../../assets/js/sinjira-liseuse-v26.js',import.meta.url),'utf8');
const extract=(start,end)=>{
  const from=source.indexOf(start),to=source.indexOf(end,from+start.length);
  assert.ok(from>=0&&to>from,'missing section '+start);
  return source.slice(from,to);
};
const rpcCode=extract('function syncProgress(){','/** V51.5 :');
const lockCode=extract('function lockPrivateReader(', 'function watchPrivateSession(){');

function setup(status){
  let destroyed=0,aborted=0,stopped=0,closed=0,sends=0;
  const messages=[],positions=[],removed=[];
  const nodes=new Map();
  const node=id=>{
    if(!nodes.has(id))nodes.set(id,{
      textContent:'extrait privé',value:'annotation privée',width:280,height:320,
      hidden:false,replaceChildren(){this.textContent=''}
    });
    return nodes.get(id);
  };
  const pdf={numPages:50,destroy(){destroyed++;return Promise.resolve()}};
  const state={
    pdf,user:{id:'user-test-01'},novelId:'roman-test-01',page:12,
    progressRevision:4,positionRatio:0.3,progressQueue:Promise.resolve(),
    accessInvalidated:false,accessEpoch:2,cloudDirty:true,
    cloudRetrying:false,cloudRevision:2,cloudRevisionReady:true,
    cloudConflict:false,renderVersion:5,saveTimer:123,scrollTimer:456,
    loadController:{abort(){aborted++}}
  };
  const sandbox={
    state,isFull:true,$:node,companion:{close(){closed++}},
    stopNarration(){stopped++},
    clearTimeout(){},
    message(message,type){messages.push({message,type})},
    positionNotice(message,type){positions.push({message,type})},
    readingRatio:value=>value,
    pageStorageKey:()=> 'local:demo:',
    safeLocalRemove:key=>{removed.push(key);return true},
    getSupabase:()=>({
      rpc:()=>({
        async single(){
          sends++;
          return {data:status==='saved'
            ?{result_status:'saved',result_revision:3}
            :{result_status:status},error:null};
        }
      })
    })
  };
  const sync=runInNewContext(rpcCode+'\n'+lockCode+'\nsyncProgress;',sandbox);
  return {
    sync,state,node,messages,positions,removed,
    counts:()=>({destroyed,aborted,stopped,closed,sends})
  };
}

test('V51.6 : refus explicite des droits ferme vraiment le PDF et le texte',async ()=>{
  const ctx=setup('unavailable');
  assert.equal(await ctx.sync(),false);
  assert.equal(ctx.state.accessInvalidated,true);
  assert.equal(ctx.state.accessEpoch,3);
  assert.equal(ctx.state.pdf,null);
  assert.equal(ctx.state.user,null);
  assert.equal(ctx.state.novelId,null);
  assert.equal(ctx.state.cloudRevisionReady,false);
  assert.equal(ctx.state.cloudDirty,false);
  assert.equal(ctx.node('reader-content').hidden,true);
  assert.equal(ctx.node('reader-loading').hidden,true);
  assert.equal(ctx.node('reader-error').hidden,false);
  assert.equal(ctx.node('reader-text').textContent,'');
  assert.equal(ctx.node('reader-selection-preview').textContent,'');
  assert.equal(ctx.node('reader-note-input').value,'');
  assert.equal(ctx.node('reader-search-field').value,'');
  assert.equal(ctx.node('reader-canvas').width,0);
  assert.equal(ctx.node('reader-canvas').height,0);
  assert.deepEqual(ctx.counts(),{
    destroyed:1,aborted:1,stopped:1,closed:1,sends:1
  });
  assert.match(ctx.messages.at(-1).message,/droit d’accès.*n’est plus disponible/);
  assert.equal(ctx.messages.at(-1).type,'error');
  assert.equal(ctx.removed.length,0,'la progression locale ne doit pas être effacée');
  assert.equal(await ctx.sync(),false,'aucun nouvel appel après révocation');
  assert.equal(ctx.counts().sends,1);
});

test('V51.6 : conflit CAS ne détruit jamais le livre autorisé',async ()=>{
  const ctx=setup('conflict');
  assert.equal(await ctx.sync(),false);
  assert.equal(ctx.state.accessInvalidated,false);
  assert.equal(ctx.node('reader-content').hidden,false);
  assert.equal(ctx.state.cloudConflict,true);
  assert.equal(ctx.state.cloudDirty,true);
  assert.equal(ctx.counts().destroyed,0);
  assert.equal(ctx.messages.length,0);
  assert.equal(ctx.removed.length,0);
});

test('V51.6 : sauvegarde CAS valide conserve la lecture et incrémente sa révision',async ()=>{
  const ctx=setup('saved');
  assert.equal(await ctx.sync(),true);
  assert.equal(ctx.state.accessInvalidated,false);
  assert.equal(ctx.state.cloudRevision,3);
  assert.equal(ctx.state.cloudDirty,false);
  assert.equal(ctx.counts().destroyed,0);
  assert.equal(ctx.removed.length,1);
});

test('V51.6 : changement de session masque le roman avec message distinct',()=>{
  const ctx=setup('unavailable');
  const lock=runInNewContext(lockCode+'\nlockPrivateReader;',{
    state:ctx.state,isFull:true,$:ctx.node,companion:null,
    stopNarration(){},clearTimeout(){},message:(message,type)=>ctx.messages.push({message,type})
  });
  lock();
  assert.equal(ctx.state.accessInvalidated,true);
  assert.match(ctx.messages.at(-1).message,/session a changé/);
  assert.doesNotMatch(ctx.messages.at(-1).message,/droit d’accès/);
});
