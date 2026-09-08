import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const parserUrl=new URL('../assets/js/sinjira-live-command-parser-v25.js',import.meta.url);
const parserSource=await readFile(parserUrl,'utf8');
const parserModule=await import(`data:text/javascript;base64,${Buffer.from(parserSource).toString('base64')}`);
const {
  liveCommandRpcSpec,
  liveTopic,
  normalizeLiveRoomId,
  parseLiveInput
}=parserModule;

const room='11111111-2222-4333-8444-555555555555';

assert.deepEqual(parseLiveInput(''),{kind:'empty'});
assert.deepEqual(parseLiveInput('Bonjour le salon'),{kind:'message',body:'Bonjour le salon'});
assert.deepEqual(parseLiveInput('  /join salon-test  '),{kind:'join',slug:'salon-test'});
assert.deepEqual(parseLiveInput('/JOIN Salon-Test'),{kind:'join',slug:'salon-test'});
assert.deepEqual(parseLiveInput('/join'),{kind:'error',code:'LIVE_COMMAND_JOIN_USAGE'});
assert.deepEqual(parseLiveInput('/join privé!'),{kind:'error',code:'LIVE_COMMAND_JOIN_USAGE'});
assert.deepEqual(parseLiveInput('/join salon test'),{kind:'error',code:'LIVE_COMMAND_JOIN_USAGE'});
assert.deepEqual(parseLiveInput('/rooms'),{kind:'rooms'});
assert.deepEqual(parseLiveInput('/rooms 10'),{kind:'error',code:'LIVE_COMMAND_ROOMS_USAGE'});
assert.deepEqual(parseLiveInput('/me'),{kind:'me'});
assert.deepEqual(parseLiveInput('/me autre'),{kind:'error',code:'LIVE_COMMAND_ME_USAGE'});
assert.deepEqual(parseLiveInput('/admin'),{kind:'error',code:'LIVE_COMMAND_UNKNOWN',command:'admin'});
assert.deepEqual(parseLiveInput('/drop table users'),{kind:'error',code:'LIVE_COMMAND_UNKNOWN',command:'drop'});

assert.deepEqual(
  liveCommandRpcSpec(parseLiveInput('/join salon-test')),
  {rpc:'social_live_join_public_room',args:{p_slug:'salon-test'}}
);
assert.deepEqual(
  liveCommandRpcSpec(parseLiveInput('/rooms')),
  {rpc:'social_live_list_rooms',args:{p_limit:50}}
);
assert.deepEqual(
  liveCommandRpcSpec(parseLiveInput('/me')),
  {rpc:'social_live_me',args:{}}
);
assert.equal(liveCommandRpcSpec(parseLiveInput('/whoami')),null);

assert.equal(normalizeLiveRoomId(room.toUpperCase()),room);
assert.equal(liveTopic(room),`sinjira-live:${room}`);
assert.throws(()=>normalizeLiveRoomId('not-a-room'),/SOCIAL_LIVE_ROOM_ID_INVALID/);

// Même une chaîne ressemblant à une instruction ne devient jamais un nom de RPC.
for(const malicious of [
  '/rpc evil_function',
  '/join salon-test;select',
  '/rooms;drop',
  '/me()'
]){
  const parsed=parseLiveInput(malicious);
  const spec=liveCommandRpcSpec(parsed);
  assert.equal(spec,null);
}

console.log('OK parseur En direct V25: mapping fermé /join /rooms /me, aucun nom de RPC contrôlé par l’utilisateur.');
