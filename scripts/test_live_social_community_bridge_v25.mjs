import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';

const modulePath=process.argv[2];
if(!modulePath)throw new Error('MODULE_PATH_REQUIRED');
const bridge=await import(pathToFileURL(modulePath));

const VIEWER='11111111-1111-4111-8111-111111111111';
const TARGET='22222222-2222-4222-8222-222222222222';

const context=bridge.normalizeCommunityLiveInviteContext({
  viewerUserId:`  ${VIEWER.toUpperCase()}  `,
  targetUserId:TARGET.toUpperCase(),
  targetLabel:'  Alice   SINJIRA  '
});
assert.equal(context.targetUserId,TARGET,'UUID cible normalisé attendu');
assert.equal(context.targetLabel,'Alice SINJIRA','libellé public normalisé attendu');
assert.equal(Object.isFrozen(context),true,'contexte doit être figé');

const fallback=bridge.normalizeCommunityLiveInviteContext({
  viewerUserId:VIEWER,
  targetUserId:TARGET,
  targetLabel:'   '
});
assert.equal(fallback.targetLabel,'Membre SINJIRA™','libellé de repli attendu');

assert.throws(
  ()=>bridge.normalizeCommunityLiveInviteContext({viewerUserId:'invalide',targetUserId:TARGET,targetLabel:'Alice'}),
  /SOCIAL_LIVE_COMMUNITY_CONTEXT_UNAVAILABLE/,
  'viewer invalide doit être refusé'
);
assert.throws(
  ()=>bridge.normalizeCommunityLiveInviteContext({viewerUserId:VIEWER,targetUserId:'invalide',targetLabel:'Alice'}),
  /SOCIAL_LIVE_COMMUNITY_CONTEXT_UNAVAILABLE/,
  'cible invalide doit être refusée'
);
assert.throws(
  ()=>bridge.normalizeCommunityLiveInviteContext({viewerUserId:VIEWER,targetUserId:VIEWER,targetLabel:'Moi'}),
  /SOCIAL_LIVE_COMMUNITY_SELF_INVITE_FORBIDDEN/,
  'auto-invitation doit être refusée'
);

console.log('OK pont Communauté → invitation En direct V25: contexte borné, UUID validés, auto-invitation refusée et libellé public normalisé.');
