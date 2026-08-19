const targetId=String(new URLSearchParams(location.search).get('post')||'').trim();
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

if(targetId&&UUID_RE.test(targetId)){
  const locate=()=>[...document.querySelectorAll('[data-post]')].find(node=>node.dataset.post===targetId)||null;
  const focus=()=>{
    const card=locate();
    if(!card)return false;
    card.setAttribute('tabindex','-1');
    card.setAttribute('aria-label','Publication ouverte depuis une notification');
    card.dataset.notificationTarget='true';
    card.scrollIntoView({behavior:'smooth',block:'center'});
    try{card.focus({preventScroll:true});}catch(_){card.focus();}
    return true;
  };

  if(!focus()){
    const observer=new MutationObserver(()=>{
      if(focus())observer.disconnect();
    });
    const root=document.querySelector('[data-real-feed],[data-character-feed]')||document.body;
    observer.observe(root,{childList:true,subtree:true});
    setTimeout(()=>observer.disconnect(),10000);
  }
}
