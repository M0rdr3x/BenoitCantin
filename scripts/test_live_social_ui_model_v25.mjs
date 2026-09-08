import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source=await readFile(new URL('../assets/js/sinjira-live-ui-model-v25.js',import.meta.url),'utf8');
const mod=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const {
  liveCommandHelp,
  livePresenceLabel,
  liveRoomAccessLabel,
  liveUiErrorMessage,
  normalizeLiveMe,
  normalizeLiveRooms
}=mod;

const roomId='11111111-2222-4333-8444-555555555555';
const otherId='aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';

assert.deepEqual(normalizeLiveMe({
  profile_label:'  Alex  ',owned_rooms:2,joined_rooms:4,user_id:'secret'
}),{profileLabel:'Alex',ownedRooms:2,joinedRooms:4});
assert.deepEqual(normalizeLiveMe({owned_rooms:-5,joined_rooms:'oops'}),{
  profileLabel:'Membre SINJIRA',ownedRooms:0,joinedRooms:0
});

const rooms=normalizeLiveRooms({rooms:[
  {room_id:roomId,slug:'salon-test',name:'Salon test',description:'Bonjour',visibility:'public',owned:false,joined:true,owner_user_id:'secret'},
  {room_id:roomId,slug:'doublon',name:'Doublon',visibility:'public'},
  {room_id:otherId,slug:'salon-prive',name:'Privé',visibility:'private',owned:true,joined:true,user_id:'secret'},
  {room_id:'bad',slug:'invalide',name:'Ignoré'}
]});
assert.equal(rooms.length,2);
assert.deepEqual(rooms[0],{
  roomId,slug:'salon-test',name:'Salon test',description:'Bonjour',visibility:'public',owned:false,joined:true
});
assert.equal(Object.hasOwn(rooms[0],'owner_user_id'),false);
assert.equal(Object.hasOwn(rooms[1],'user_id'),false);
assert.equal(rooms[1].visibility,'private');

assert.equal(livePresenceLabel(0),'Personne en ligne dans ce salon');
assert.equal(livePresenceLabel(1),'1 présence active');
assert.equal(livePresenceLabel(4),'4 présences actives');
assert.equal(livePresenceLabel(-1),'Personne en ligne dans ce salon');

assert.equal(liveRoomAccessLabel(null),'Aucun salon sélectionné');
assert.equal(liveRoomAccessLabel({visibility:'public',joined:false,owned:false}),'Salon public · rejoindre pour écrire');
assert.equal(liveRoomAccessLabel({visibility:'public',joined:true,owned:false}),'Salon public · rejoint');
assert.equal(liveRoomAccessLabel({visibility:'private',joined:false}),'Salon privé · invitation requise');
assert.equal(liveRoomAccessLabel({visibility:'private',joined:true}),'Salon privé · membre');

assert.equal(liveCommandHelp(),'/join <salon> · /rooms · /me');
assert.match(liveUiErrorMessage(new Error('LIVE_COMMAND_UNKNOWN')),/Commande inconnue/);
assert.match(liveUiErrorMessage(new Error('SOCIAL_LIVE_ROOM_UNAVAILABLE')),/pas disponible/);
assert.equal(liveUiErrorMessage(new Error('AUTRE_ERREUR')),null);

console.log('OK modèle UI En direct V25: données bornées, UUID utilisateurs ignorés, présence agrégée et commandes explicites.');
