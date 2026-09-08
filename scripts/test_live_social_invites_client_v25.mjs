import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source=await readFile(new URL('../assets/js/sinjira-live-invites-model-v25.js',import.meta.url),'utf8');
const mod=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const {
  normalizeLiveInviteCreate,
  normalizeLiveInviteResponse,
  normalizeLiveInvites
}=mod;

const inviteId='11111111-2222-4333-8444-555555555555';
const roomId='aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';

const created=normalizeLiveInviteCreate({
  ok:true,
  invite_id:inviteId,
  room_id:roomId,
  expires_at:'2026-09-15T12:00:00Z',
  inviter_user_id:'secret-inviter',
  invitee_user_id:'secret-invitee',
  owner_user_id:'secret-owner'
});
assert.deepEqual(created,{
  inviteId,
  roomId,
  expiresAt:'2026-09-15T12:00:00Z'
});
for(const forbidden of ['inviter_user_id','invitee_user_id','owner_user_id','user_id']){
  assert.equal(Object.hasOwn(created,forbidden),false);
}
assert.equal(normalizeLiveInviteCreate({ok:false,invite_id:inviteId,room_id:roomId,expires_at:'x'}),null);
assert.equal(normalizeLiveInviteCreate({ok:true,invite_id:'bad',room_id:roomId,expires_at:'x'}),null);

const invites=normalizeLiveInvites({
  ok:true,
  invites:[
    {
      invite_id:inviteId,
      room_id:roomId,
      room_slug:'salon-prive',
      room_name:'  Salon privé  ',
      inviter_label:'  Alice  ',
      created_at:'2026-09-08T12:00:00Z',
      expires_at:'2026-09-15T12:00:00Z',
      inviter_user_id:'secret-inviter',
      invitee_user_id:'secret-invitee',
      responded_at:'secret-metadata'
    },
    {
      invite_id:inviteId,
      room_id:roomId,
      room_slug:'doublon',
      room_name:'Doublon',
      inviter_label:'Doublon',
      created_at:'2026-09-08T12:01:00Z',
      expires_at:'2026-09-15T12:00:00Z'
    },
    {
      invite_id:'bad',
      room_id:roomId,
      room_slug:'invalide',
      room_name:'Ignoré',
      inviter_label:'Ignoré',
      created_at:'2026-09-08T12:00:00Z',
      expires_at:'2026-09-15T12:00:00Z'
    }
  ]
});
assert.equal(invites.length,1);
assert.deepEqual(invites[0],{
  inviteId,
  roomId,
  roomSlug:'salon-prive',
  roomName:'Salon privé',
  inviterLabel:'Alice',
  createdAt:'2026-09-08T12:00:00Z',
  expiresAt:'2026-09-15T12:00:00Z'
});
for(const forbidden of ['inviter_user_id','invitee_user_id','owner_user_id','user_id','responded_at']){
  assert.equal(Object.hasOwn(invites[0],forbidden),false);
}

const fallback=normalizeLiveInvites({
  ok:true,
  invites:[{
    invite_id:'22222222-3333-4444-8555-666666666666',
    room_id:roomId,
    room_slug:'autre-salon',
    room_name:'Autre salon',
    inviter_label:'   ',
    created_at:'2026-09-08T12:00:00Z',
    expires_at:'2026-09-15T12:00:00Z'
  }]
});
assert.equal(fallback[0].inviterLabel,'Membre SINJIRA™');
assert.deepEqual(normalizeLiveInvites({ok:false,invites:[]}),[]);

assert.deepEqual(normalizeLiveInviteResponse({
  ok:true,
  status:'accepted',
  room_id:roomId,
  inviter_user_id:'secret-inviter',
  invitee_user_id:'secret-invitee'
}),{status:'accepted',roomId});
assert.deepEqual(normalizeLiveInviteResponse({ok:true,status:'declined'}),{status:'declined'});
assert.deepEqual(normalizeLiveInviteResponse({ok:false,status:'expired'}),{status:'expired'});
assert.deepEqual(normalizeLiveInviteResponse({ok:false,status:'unavailable'}),{status:'unavailable'});
assert.equal(normalizeLiveInviteResponse({ok:true,status:'expired'}),null);
assert.equal(normalizeLiveInviteResponse({ok:true,status:'accepted',room_id:'bad'}),null);

console.log('OK client invitations privées En direct V25: réponses minimisées, dédoublonnées et aucune identité serveur privée conservée.');
