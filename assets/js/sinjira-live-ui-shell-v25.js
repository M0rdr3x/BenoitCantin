import {getSupabase} from './sinjira-supabase.js';
import {createLiveUi} from './sinjira-live-ui-v25.js';
import {createLiveShareCodesUi} from './sinjira-live-share-codes-ui-v25.js';
import {createLiveInvitesUi} from './sinjira-live-invites-ui-v25.js';

export function createLiveUiShell(root,{supabase=getSupabase()}={}){
  if(!(root instanceof Element))throw new Error('SOCIAL_LIVE_UI_SHELL_ROOT_REQUIRED');

  const liveRoot=document.createElement('div');
  liveRoot.className='v25-live-shell-main';
  const shareRoot=document.createElement('div');
  shareRoot.className='v25-live-shell-share';
  const invitesRoot=document.createElement('div');
  invitesRoot.className='v25-live-shell-invites';
  root.replaceChildren(liveRoot,invitesRoot,shareRoot);

  const live=createLiveUi(liveRoot,{supabase});
  const share=createLiveShareCodesUi(shareRoot,{
    supabase,
    onJoined:async()=>{
      await live.refresh();
    }
  });
  const invites=createLiveInvitesUi(invitesRoot,{
    supabase,
    onAccepted:async()=>{
      await live.refresh();
    }
  });

  return {
    ready:Promise.all([live.ready,share.ready,invites.ready]),
    refresh:async()=>Promise.all([live.refresh(),share.refresh(),invites.refresh()]),
    destroy:async()=>{
      await Promise.all([live.destroy(),share.destroy(),invites.destroy()]);
      root.replaceChildren();
    }
  };
}
