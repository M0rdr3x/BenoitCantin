/* Pages publiques de secours : aucun stockage ni accès privé. */
(() => {
  'use strict';
  const kind = document.body?.dataset.errorPage;
  if (kind === '404') {
    (()=>{const p=location.pathname.replace(/\/+$/,'').toLowerCase();const aliases={'/sinjira':'/projets/sinjira/','/sinjira/romans':'/projets/sinjira/romans/','/sinjira/jeux':'/projets/sinjira/jeux/','/sinjira/registre':'/projets/sinjira/registre/','/sinjira/communaute':'/projets/sinjira/communaute/','/sinjira/monde-parallele':'/projets/sinjira/monde-parallele/','/sinjira/marche':'/projets/sinjira/marche/','/sinjira/codex':'/projets/sinjira/codex/','/projets/sinjira/romans.html':'/projets/sinjira/romans/','/projets/sinjira/jeux.html':'/projets/sinjira/jeux/','/projets/sinjira/registre.html':'/projets/sinjira/registre/','/projets/sinjira/communaute.html':'/projets/sinjira/communaute/','/projets/sinjira/monde-parallele.html':'/projets/sinjira/monde-parallele/','/projets/sinjira/marche.html':'/projets/sinjira/marche/','/projets/sinjira/codex.html':'/projets/sinjira/codex/','/admin':'/admin/sinjira/','/admin/sinjira':'/admin/sinjira/','/admin/sinjira.html':'/admin/sinjira/'};if(aliases[p])location.replace(aliases[p]+location.search+location.hash)})();
    return;
  }
  if (kind !== 'offline') return;
  const retry = document.querySelector('[data-error-retry]');
  if (!retry) return;
  retry.addEventListener('click', () => {
    // Une ouverture directe de la page de secours ne doit pas la recharger
    // indéfiniment. Une navigation interrompue reprend son URL d'origine.
    if (location.pathname === '/offline.html') location.assign('/');
    else location.reload();
  });
  retry.hidden = false;
})();
