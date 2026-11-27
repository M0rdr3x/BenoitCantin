// Tests isolés des deux clients réels, aucun compte ni appel réseau.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
function deferred(){let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};}
function fixture(mode){
  const source=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-messages-'+mode+'.js'),'utf8');
  const boot=source.indexOf('\n(async()=>{');
  assert.ok(boot>0);
  const body=source.slice(0,boot).replace(/^import [^\n]+\n/gm,'');
  const draft={value:''};
  const log={textContent:'',innerHTML:'',scrollHeight:500,scrollTop:450,clientHeight:50,querySelectorAll(){return [];}};
  const form={hidden:true,querySelector(){return draft;},reset(){draft.value='';}};
  const contacts={innerHTML:'',querySelectorAll(){return [];}};
  const title={innerHTML:'',querySelector(){return null;}};
  const requests=[];
  const document={querySelector(key){return ({
    '[data-contact-list]':contacts,'[data-contact-search]':{value:''},
    '[data-chat-log]':log,'[data-chat-form]':form,'[data-chat-title]':title
  })[key]||null;}};
  const state={confirm:false};
  const context={document,history:{replaceState(){}},confirm:()=>state.confirm,
    escapeHtml:x=>String(x??''),avatarUrl:()=>'/fixture.png',formatDate:()=>'',markConversationRead:async()=>{},
    getSupabase:()=>({from(table){
      assert.equal(table,mode==='real'?'social_real_messages':'social_character_messages');
      return {select(){return this;},or(filter){this.filter=filter;return this;},order(){
        const d=deferred();requests.push({filter:this.filter,...d});return d.promise;
      }};
    }})};
  const setup=mode==='real'?"user={id:'me'};all=[{user_id:'a',pseudo:'A'},{user_id:'b',pseudo:'B'}];":"user={id:'me'};me={character_id:'mychar'};all=[{user_id:'a',character_id:'ca',public_name:'A'},{user_id:'b',character_id:'cb',public_name:'B'}];";
  const api=vm.runInNewContext(body+'\n'+setup+'\n({openPeer,messages,setSending(v){sending=v;},peerId(){return peer?.'+(mode==='real'?'user_id':'character_id')+';}})',context);
  return {api,requests,state,draft,log,contacts,form};
}
function row(body){return {data:[{id:'fixture',sender_user_id:'me',recipient_user_id:'other',body}],error:null};}
(async()=>{
  for(const mode of ['real','character']){
    const f=fixture(mode),a=mode==='real'?'a':'ca',b=mode==='real'?'b':'cb';
    const first=f.api.openPeer(a);
    const second=f.api.openPeer(b);
    assert.equal(f.requests.length,2);
    f.requests[1].resolve(row('Conversation B'));
    await second;
    f.requests[0].resolve(row('Conversation A'));
    await first;
    assert.match(f.log.innerHTML,/Conversation B/);
    assert.ok(!f.log.innerHTML.includes('Conversation A'),'réponse obsolète affichée');
    f.draft.value='Brouillon fictif';
    await f.api.openPeer(a);
    assert.equal(f.api.peerId(),b);
    assert.equal(f.draft.value,'Brouillon fictif');
    f.state.confirm=true;
    f.api.setSending(true);
    await f.api.openPeer(a);
    assert.equal(f.api.peerId(),b);
    f.api.setSending(false);
    const change=f.api.openPeer(a);
    assert.equal(f.draft.value,'');
    f.requests[2].resolve({error:new Error('fixture')});
    await assert.rejects(change,/fixture/);
    assert.match(f.log.textContent,/Chargement impossible/);
    const retry=f.api.openPeer(a);
    assert.equal(f.requests.length,4);
    f.requests[3].resolve(row('Historique restauré'));
    await retry;
    assert.match(f.log.innerHTML,/Historique restauré/);
    f.log.scrollTop=20;
    const refresh=f.api.messages();
    f.requests[4].resolve(row('Actualisé'));
    await refresh;
    assert.equal(f.log.scrollTop,20,'lecture ancienne interrompue');
  }
  console.log('OK messageries: réponses obsolètes, brouillons, verrou envoi, nouvelle tentative et position de lecture.');
})().catch(error=>{console.error(error);process.exitCode=1;});
