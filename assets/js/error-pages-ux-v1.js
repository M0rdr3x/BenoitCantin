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
  const status = document.querySelector('[data-error-status]');
  if (!retry || !status) return;
  const direct = location.pathname === '/offline.html';
  const updateStatus = () => {
    // onLine est un indice local, pas une preuve que le serveur répond.
    const network = navigator.onLine === false
      ? 'Votre appareil semble déconnecté. Vérifiez votre réseau.'
      : 'Votre appareil signale une connexion possible. Le site peut encore être indisponible.';
    const action = direct
      ? ' Revenez à l’accueil pour reprendre la navigation.'
      : ' Réessayez la connexion pour retrouver la page demandée.';
    const message = network + action;
    if (status.textContent !== message) status.textContent = message;
  };
  // Ne pas afficher deux commandes qui mènent toutes deux à l’accueil.
  if (!direct) {
    retry.addEventListener('click', () => location.reload());
    retry.hidden = false;
  }
  window.addEventListener('online', updateStatus);
  window.addEventListener('offline', updateStatus);
  updateStatus();
})();
