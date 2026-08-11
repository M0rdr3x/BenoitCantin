const count=document.querySelector('[data-setup-count]');
const panel=document.querySelector('[data-generated-panel]');
const list=document.querySelector('[data-player-list]');
const title=document.querySelector('[data-generated-title]');
const intro=document.querySelector('[data-generated-intro]');
const endgame=document.querySelector('[data-endgame-link]');

function makePartyCode(){
  return `FRM-${Math.random().toString(36).slice(2,8).toUpperCase()}`;
}

function linkFor({humanNo, humans, role, partyCode, name=''}){
  const q=new URLSearchParams({
    joueur:String(humanNo),
    players:String(humans),
    effective:'3',
    role,
    sheet:role==='invisible3'?`p${humanNo}_invisible_3`:`p${humanNo}_self`,
    party:partyCode
  });
  if(name)q.set('nom',name);
  return `fiche-web.html?${q.toString()}`;
}

function playerCard(no,humans,partyCode){
  const hasInvisible=humans===2;
  return `<article class="fracture-player-card" data-player-card="${no}">
    <span class="eyebrow">Joueur humain ${no}</span>
    <h3>Dossier privé du Joueur ${no}</h3>
    <input data-name="${no}" placeholder="Nom / pseudo local (facultatif)">
    <div class="fracture-subcard">
      <strong>Ma fiche personnelle</strong>
      <p class="fracture-note">Cette fiche appartient uniquement au Joueur ${no}.</p>
      <div class="fracture-toolbar">
        <a class="btn btn-primary" data-player-link="${no}" data-role="self" target="_blank" rel="noopener" href="${linkFor({humanNo:no,humans,role:'self',partyCode})}">Ouvrir ma fiche</a>
        <a class="btn btn-secondary" href="documents/SINJIRA_Fiche_Joueur_1_Copie_Interactive.pdf" download>Télécharger une fiche vierge</a>
      </div>
    </div>
    ${hasInvisible?`<div class="fracture-subcard fracture-subcard--invisible">
      <strong>Ma fiche séparée - Joueur invisible 3</strong>
      <p class="fracture-note">Cette copie du Joueur invisible 3 appartient uniquement au Joueur ${no}. Le Joueur ${no===1?2:1} possède sa propre copie indépendante.</p>
      <div class="fracture-toolbar">
        <a class="btn btn-secondary" data-player-link="${no}" data-role="invisible3" target="_blank" rel="noopener" href="${linkFor({humanNo:no,humans,role:'invisible3',partyCode})}">Ouvrir ma fiche du Joueur invisible 3</a>
        <a class="btn btn-secondary" href="documents/SINJIRA_Fiche_Joueur_1_Copie_Interactive.pdf" download>Télécharger une fiche vierge</a>
      </div>
    </div>`:''}
  </article>`;
}

function generate(){
  const humans=Math.max(1,Math.min(3,Number(count.value)||1));
  count.value=humans;
  const solo=humans===1;
  const effective=3;
  const partyCode=makePartyCode();
  const setup={
    human_player_count:humans,
    effective_player_count:effective,
    invisible_player_count:humans===1?2:(humans===2?1:0),
    play_mode:solo?'solo':'multiplayer',
    party_code:partyCode,
    created_at:new Date().toISOString()
  };
  sessionStorage.setItem('sinjira_fracture_setup',JSON.stringify(setup));

  if(solo){
    title.textContent='Mode solo - une seule fiche pour trois participants';
    intro.innerHTML=`Vous jouez seul. Une seule fiche regroupe <strong>vous + Joueur invisible 2 + Joueur invisible 3</strong>. Les trois sections sont privées et restent séparées de la Feuille de fin de partie.`;
    list.innerHTML=`<article class="fracture-player-card fracture-player-card--solo">
      <span class="eyebrow">Mode solo</span>
      <h3>Vous + Invisible 2 + Invisible 3</h3>
      <p class="fracture-note">Une seule interface, trois sections de résultats. Aucune de ces données n'est transmise à SINJIRA pour l'équilibrage.</p>
      <div class="fracture-toolbar">
        <a class="btn btn-primary" href="fiche-solo.html?party=${encodeURIComponent(partyCode)}">Ouvrir ma fiche solo</a>
        <a class="btn btn-secondary" href="documents/SINJIRA_Mode_Solo_3_Joueurs_Interactive.pdf" download>Télécharger le PDF solo</a>
      </div>
    </article>`;
  }else if(humans===2){
    title.textContent='2 dossiers privés - 2 fiches par joueur';
    intro.innerHTML=`La partie utilise <strong>2 joueurs humains + le Joueur invisible 3</strong>. Chaque humain possède deux fiches privées séparées : <strong>sa fiche personnelle</strong> et <strong>sa propre copie du Joueur invisible 3</strong>. Les copies du Joueur invisible 3 du Joueur 1 et du Joueur 2 sont indépendantes et ne sont jamais fusionnées.`;
    list.innerHTML=[1,2].map(no=>playerCard(no,humans,partyCode)).join('');
  }else{
    title.textContent='3 fiches privées séparées';
    intro.innerHTML=`La partie utilise <strong>3 joueurs humains</strong>. Chaque joueur possède uniquement sa propre fiche privée. Il n'y a aucun joueur invisible dans ce mode.`;
    list.innerHTML=[1,2,3].map(no=>playerCard(no,humans,partyCode)).join('');
  }

  list.querySelectorAll('[data-name]').forEach(inp=>inp.addEventListener('input',()=>{
    const no=Number(inp.dataset.name);
    list.querySelectorAll(`[data-player-link="${no}"]`).forEach(link=>{
      link.href=linkFor({humanNo:no,humans,role:link.dataset.role,partyCode,name:inp.value});
    });
  }));

  endgame.href=`fin-de-partie.html?humans=${humans}&effective=3&mode=${solo?'solo':'multiplayer'}&party=${encodeURIComponent(partyCode)}`;
  panel.hidden=false;
  panel.scrollIntoView({behavior:'smooth',block:'start'});
}

document.querySelector('[data-generate-players]').addEventListener('click',generate);
