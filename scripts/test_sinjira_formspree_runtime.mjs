import test from 'node:test';
import assert from 'node:assert/strict';
import {sendFormspreeNotice} from '../supabase/functions/_shared/sinjira-formspree.ts';

// Mocks locaux uniquement : aucun appel réseau et aucune donnée réelle.
const SOURCE_ID='00000000-0000-4000-8000-000000000001';
const EVENT_ID='33333333-3333-4333-8333-333333333333';

function fakeDatabase({duplicate=false,prior='sent',writeThrows=false,readThrows=false}={}){
  const changes=[];
  const client={
    from(table){
      assert.equal(table,'sinjira_formspree_events');
      return {
        insert(){
          return {select(){
            return {single:async()=>{
              if(writeThrows)throw new Error('Simulated database outage');
              return duplicate ? {data:null,error:{code:'23505'}} : {data:{id:EVENT_ID},error:null};
            }};
          }};
        },
        select(){
          return {eq(){
            return {eq(){
              return {maybeSingle:async()=>{
                if(readThrows)throw new Error('Simulated status outage');
                return {data:{delivery_status:prior},error:null};
              }};
            }};
          }};
        },
        update(data){
          changes.push(data);
          return {eq:async()=>({error:null})};
        }
      };
    }
  };
  return {client,changes};
}

test('SINJIRA Formspree : canal secondaire, anti-doublons et filtrage',async()=>{
  const originalFetch=globalThis.fetch;
  const originalWarn=console.warn;
  const sent=[];
  const warnings=[];
  globalThis.fetch=async(url,options)=>{
    sent.push({url:String(url),data:JSON.parse(String(options.body))});
    return new Response(JSON.stringify({ok:true}),{status:200});
  };
  console.warn=(...args)=>warnings.push(args);
  try{
    const first=fakeDatabase();
    const result=await sendFormspreeNotice(first.client,'registre_enregistre',SOURCE_ID,{
      email:'VISITEUR@example.com',
      answers:{
        appearance_hair:'Bruns',
        strengths:['Loyal','Calme'],
        password:'SECRET_NE_JAMAIS_ENVOYER',
        parent_telephone:'PRIVE_NE_JAMAIS_ENVOYER',
        compte_courriel:'hidden@example.org'
      }
    });
    assert.equal(result.accepted,true);
    assert.equal(result.already,false);
    assert.equal(sent.length,1);
    assert.equal(sent[0].url,'https://formspree.io/f/mrppvrwa');
    assert.equal(sent[0].data.email,'visiteur@example.com');
    assert.match(sent[0].data.questionnaire,/Apparence — cheveux : Bruns/);
    assert.match(sent[0].data.questionnaire,/Forces : Loyal, Calme/);
    assert.doesNotMatch(JSON.stringify(sent[0]),/SECRET_NE_JAMAIS_ENVOYER|PRIVE_NE_JAMAIS_ENVOYER|hidden@example.org/);
    assert.equal(first.changes[0].delivery_status,'sent');

    const existing=fakeDatabase({duplicate:true,prior:'sent'});
    const duplicateResult=await sendFormspreeNotice(existing.client,'registre_enregistre',SOURCE_ID,{
      email:'visiteur@example.com',answers:{appearance_hair:'Bruns'}
    });
    assert.deepEqual([duplicateResult.accepted,duplicateResult.already],[true,true]);
    assert.equal(sent.length,1,'aucun second envoi');

    const previouslyFailed=fakeDatabase({duplicate:true,prior:'failed'});
    const failedResult=await sendFormspreeNotice(previouslyFailed.client,'registre_enregistre',SOURCE_ID,{
      email:'visiteur@example.com',answers:{appearance_hair:'Bruns'}
    });
    assert.deepEqual([failedResult.accepted,failedResult.already],[false,true]);
    assert.equal(sent.length,1,'aucun retry implicite ambigu');

    const brokenDb=fakeDatabase({writeThrows:true});
    const dbResult=await sendFormspreeNotice(brokenDb.client,'compte_confirme',SOURCE_ID,{
      email:'visiteur@example.com'
    });
    assert.equal(dbResult.accepted,false,'une panne du tiers ne doit pas devenir un succès');
    assert.equal(dbResult.reason,'SECONDARY_CHANNEL_UNAVAILABLE');
    assert.equal(sent.length,1);

    const invalidAddress=await sendFormspreeNotice(fakeDatabase().client,'compte_confirme',SOURCE_ID,{
      email:'invalid-email'
    });
    assert.equal(invalidAddress.accepted,false);
    assert.equal(sent.length,1,'ne jamais envoyer vers une adresse non valide');

    const huge=await sendFormspreeNotice(fakeDatabase().client,'registre_enregistre',SOURCE_ID,{
      email:'visiteur@example.com',answers:{personality_notes:'x'.repeat(29000)}
    });
    assert.equal(huge.accepted,false);
    assert.equal(sent.length,1,'refuser un questionnaire dont la copie serait tronquée');

    const confirmation=fakeDatabase();
    const confirmationResult=await sendFormspreeNotice(confirmation.client,'compte_confirme',SOURCE_ID,{
      email:'visiteur@example.com'
    });
    assert.equal(confirmationResult.accepted,true);
    assert.equal(sent.length,2);
    assert.equal(sent[1].url,'https://formspree.io/f/xzeeqynp');
    assert.equal(sent[1].data.email,'visiteur@example.com');
    assert.equal('questionnaire' in sent[1].data,false,'une confirmation de compte ne transmet jamais de questionnaire');

    globalThis.fetch=async()=>{throw new Error('Simulated network failure')};
    const failingExternal=fakeDatabase();
    const offlineResult=await sendFormspreeNotice(failingExternal.client,'compte_confirme',SOURCE_ID,{
      email:'visiteur@example.com'
    });
    assert.equal(offlineResult.accepted,false);
    assert.equal(failingExternal.changes[0].delivery_status,'failed');

    assert.ok(warnings.length>0,'journaliser uniquement des codes techniques');
  } finally {
    globalThis.fetch=originalFetch;
    console.warn=originalWarn;
  }
});
