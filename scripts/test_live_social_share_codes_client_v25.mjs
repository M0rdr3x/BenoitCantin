import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source=await readFile(new URL('../assets/js/sinjira-live-share-codes-model-v25.js',import.meta.url),'utf8');
const mod=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const {
  normalizeLiveShareCode,
  normalizeLiveShareCodeCreate,
  normalizeLiveShareCodeRedeem,
  normalizeLiveShareCodes
}=mod;

const code='a'.repeat(64);
const codeId='11111111-2222-4333-8444-555555555555';
const roomId='aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';

assert.equal(normalizeLiveShareCode(`  ${code.toUpperCase()}  `),code);
assert.equal(normalizeLiveShareCode('a'.repeat(63)),null);
assert.equal(normalizeLiveShareCode('g'.repeat(64)),null);
assert.equal(normalizeLiveShareCode(''),null);

const created=normalizeLiveShareCodeCreate({
  ok:true,
  code_id:codeId,
  code,
  display_once:true,
  expires_at:'2026-09-09T12:00:00Z',
  creator_user_id:'secret-user',
  code_hash:'secret-hash'
});
assert.deepEqual(created,{
  codeId,
  code,
  displayOnce:true,
  expiresAt:'2026-09-09T12:00:00Z'
});
assert.equal(Object.hasOwn(created,'creator_user_id'),false);
assert.equal(Object.hasOwn(created,'code_hash'),false);
assert.equal(normalizeLiveShareCodeCreate({code_id:codeId,code,display_once:false}),null);

const codes=normalizeLiveShareCodes({codes:[
  {
    code_id:codeId,
    room_id:roomId,
    room_slug:'salon-prive',
    room_name:'Salon privé',
    status:'active',
    created_at:'2026-09-08T12:00:00Z',
    expires_at:'2026-09-09T12:00:00Z',
    closed_at:null,
    code,
    code_hash:'secret-hash',
    creator_user_id:'secret-user',
    redeemed_by_user_id:'secret-redeemer'
  },
  {
    code_id:codeId,
    room_id:roomId,
    room_slug:'doublon',
    room_name:'Doublon',
    status:'used'
  },
  {code_id:'bad',room_id:roomId,room_slug:'invalide',room_name:'Ignoré'}
]});
assert.equal(codes.length,1);
assert.deepEqual(codes[0],{
  codeId,
  roomId,
  roomSlug:'salon-prive',
  roomName:'Salon privé',
  status:'active',
  createdAt:'2026-09-08T12:00:00Z',
  expiresAt:'2026-09-09T12:00:00Z',
  closedAt:''
});
for(const forbidden of ['code','code_hash','creator_user_id','redeemed_by_user_id','user_id']){
  assert.equal(Object.hasOwn(codes[0],forbidden),false);
}

assert.deepEqual(normalizeLiveShareCodeRedeem({
  ok:true,
  status:'joined',
  room_id:roomId,
  room_slug:'salon-prive',
  creator_user_id:'secret-user'
}),{roomId,roomSlug:'salon-prive',status:'joined'});
assert.deepEqual(normalizeLiveShareCodeRedeem({
  status:'already_member',room_id:roomId,room_slug:'salon-prive'
}),{roomId,roomSlug:'salon-prive',status:'already_member'});
assert.equal(normalizeLiveShareCodeRedeem({status:'joined',room_id:'bad',room_slug:'salon-prive'}),null);

console.log('OK client codes privés En direct V25: secret 64 hex validé, réponses minimisées et aucun identifiant utilisateur/hash conservé.');
