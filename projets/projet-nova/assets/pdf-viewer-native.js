// NOVA — lecture PDF native : aucun runtime tiers n'exécute les documents.
// L'iframe n'affiche que les PDF statiques répertoriés sur cette origine.
// La prévisualisation est assurée par le lecteur PDF isolé du navigateur.
(function () {
  'use strict';
  const PATH_RE = /^documents\/([a-z0-9][a-z0-9_-]{0,150}\.pdf)$/i;
  const ID_RE = /^[a-z][a-z0-9-]{0,63}$/;
  const root = document.getElementById('pdfPages');
  const select = document.getElementById('docSelect');
  const title = document.getElementById('viewerTitle');
  const status = document.getElementById('viewerStatus');
  const download = document.getElementById('downloadBtn');
  const pageInfo = document.getElementById('pageInfo');
  const prev = document.getElementById('prevPage');
  const next = document.getElementById('nextPage');
  const zoomIn = document.getElementById('zoomIn');
  const zoomOut = document.getElementById('zoomOut');
  if (![root, select, title, status, download, pageInfo, prev, next, zoomIn, zoomOut].every(Boolean)) return;

  function safeDocument(entry) {
    if (!entry || typeof entry !== 'object') return null;
    const id = typeof entry.id === 'string' ? entry.id : '';
    const path = typeof entry.path === 'string' ? entry.path : '';
    const file = typeof entry.file === 'string' ? entry.file : '';
    const match = PATH_RE.exec(path);
    if (!ID_RE.test(id) || !match || file !== match[1] || path.includes('..')) return null;
    return {
      id, path, file,
      title: typeof entry.title === 'string' ? entry.title.slice(0, 200) : 'Document PDF',
      order: typeof entry.order === 'string' ? entry.order.slice(0, 12) : '',
    };
  }

  const source = Array.isArray(window.NOVA_DOCUMENTS) ? window.NOVA_DOCUMENTS : [];
  const documents = [];
  const ids = new Set();
  for (const entry of source.slice(0, 250)) {
    const doc = safeDocument(entry);
    if (doc && !ids.has(doc.id)) {
      documents.push(doc);
      ids.add(doc.id);
    }
  }

  // DOM sûr : jamais de innerHTML avec du texte du catalogue.
  select.replaceChildren();
  for (const doc of documents) {
    const option = document.createElement('option');
    option.value = doc.id;
    option.textContent = doc.order ? doc.order + ' — ' + doc.title : doc.title;
    select.appendChild(option);
  }

  const search = new URLSearchParams(location.search);
  let current = documents.find(doc => doc.id === search.get('doc')) || documents[0] || null;
  let page = 1;
  let zoom = 120;
  let frame = null;

  function setDisabled(disabled) {
    for (const control of [select, prev, next, zoomIn, zoomOut, download]) {
      control.disabled = disabled;
    }
  }

  function updateFrame() {
    if (!current || !frame) return;
    // Paramètres PDF standards, numéros bornés. Pas de schéma externe,
    // redirection, chemin encodé, requête ou fragment issu du catalogue.
    frame.src = current.path + '#page=' + page + '&zoom=' + zoom;
    pageInfo.textContent = 'Page ' + page + ' · lecteur du navigateur';
    prev.disabled = page <= 1;
    next.disabled = page >= 1000;
    zoomOut.disabled = zoom <= 60;
    zoomIn.disabled = zoom >= 250;
  }

  function setDocument(doc) {
    if (!doc) return;
    current = doc;
    page = 1;
    zoom = 120;
    title.textContent = doc.title;
    select.value = doc.id;
    download.href = doc.path;
    download.setAttribute('download', doc.file);

    // Réduire l'URL aux seuls paramètres approuvés, sans conserver les
    // fragments ou paramètres arbitraires éventuellement reçus.
    const url = new URL(location.href);
    url.search = '';
    url.hash = '';
    url.searchParams.set('doc', doc.id);
    history.replaceState(null, '', url.toString());

    frame = document.createElement('iframe');
    frame.className = 'viewer-native-pdf';
    frame.setAttribute('title', 'Document PDF : ' + doc.title);
    frame.setAttribute('loading', 'eager');
    frame.setAttribute('referrerpolicy', 'no-referrer');
    frame.setAttribute('width', '100%');
    frame.setAttribute('height', '800');
    frame.setAttribute('frameborder', '0');
    // Les lecteurs PDF natifs sont déjà isolés par le navigateur. Ne pas
    // définir sandbox : il bloquerait leur fonctionnement selon le navigateur.
    root.replaceChildren(frame);
    status.textContent = 'Document PDF ouvert avec le lecteur sécurisé du navigateur. '
      + 'Si l’aperçu est indisponible, utilisez Télécharger le PDF. '
      + 'Les commandes de page et zoom peuvent varier selon le navigateur.';
    updateFrame();
  }

  prev.addEventListener('click', () => { if (current && page > 1) { page--; updateFrame(); } });
  next.addEventListener('click', () => { if (current && page < 1000) { page++; updateFrame(); } });
  zoomIn.addEventListener('click', () => { if (current) { zoom = Math.min(zoom + 15, 250); updateFrame(); } });
  zoomOut.addEventListener('click', () => { if (current) { zoom = Math.max(zoom - 15, 60); updateFrame(); } });
  select.addEventListener('change', () => {
    const chosen = documents.find(doc => doc.id === select.value);
    if (chosen) setDocument(chosen);
  });
  if (current) setDocument(current);
  else {
    setDisabled(true);
    title.textContent = 'Visionneuse PDF';
    status.textContent = 'Aucun document PDF public autorisé n’est disponible.';
    pageInfo.textContent = 'Page —';
    download.removeAttribute('href');
    root.replaceChildren();
  }
})();
