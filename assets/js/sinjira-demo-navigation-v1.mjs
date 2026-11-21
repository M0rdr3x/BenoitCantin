/**
 * SINJIRA — navigation de la démo PDF gratuite.
 * Aucun accès au compte n'est nécessaire pour tourner une page ou mémoriser
 * localement la position. La synchronisation distante est facultative.
 */
export function normalizeDemoPage(raw, totalPages, fallback = 1) {
  const limit = Number.isSafeInteger(totalPages) && totalPages > 0 ? totalPages : 82;
  if (raw === null || raw === undefined || String(raw).trim() === '') return fallback;
  const number = Number(raw);
  if (!Number.isSafeInteger(number)) return fallback;
  return Math.max(1, Math.min(limit, number));
}

export function startDemoNavigation({
  document: doc,
  frame,
  slug,
  totalPages = 82,
  storageProvider = () => window.localStorage,
  onBookmark = async () => false
}) {
  if (!doc || !frame || !slug) throw new Error('Lecteur de démonstration incomplet');
  const limit = Number.isSafeInteger(totalPages) && totalPages > 0 ? totalPages : 82;
  const key = `sinjira-reader-${slug}`;
  const input = doc.querySelector('[data-reader-page-number]');
  const bar = doc.querySelector('[data-reader-progress-bar]');
  const progress = doc.querySelector('[data-reader-progress-native]');
  const resume = doc.querySelector('[data-reader-resume]');
  const previous = doc.querySelector('[data-reader-prev]');
  const next = doc.querySelector('[data-reader-next]');
  const bookmark = doc.querySelector('[data-reader-bookmark]');
  const controls = doc.querySelector('[data-reader-controls]');
  const pdf = '../documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf';

  function storage() {
    try { return storageProvider(); } catch (_) { return null; }
  }
  function localPage() {
    try { return storage()?.getItem(key) ?? null; } catch (_) { return null; }
  }
  function remember() {
    try {
      const store = storage();
      if (!store) return false;
      store.setItem(key, String(current));
      return true;
    } catch (_) { return false; } // Mode privé : lecture sans stockage.
  }

  const stored = localPage();
  let current = normalizeDemoPage(stored, limit, 1);
  let interacted = false;
  let saving = false;

  function render() {
    const percent = Math.round((current / limit) * 100);
    if (input) { input.max = String(limit); input.value = String(current); }
    if (bar) bar.style.width = `${percent}%`;
    if (progress) {
      progress.max = limit;
      progress.value = current;
      progress.textContent = `${current} sur ${limit}`;
    }
    if (previous) previous.disabled = current <= 1;
    if (next) next.disabled = current >= limit;
    if (resume) resume.textContent = `Page ${current} sur ${limit} · ${percent} %`;
    // Ne pas recharger le PDF si la page demandée est déjà affichée.
    const url = `${pdf}#page=${current}&zoom=page-width&view=FitH`;
    if (frame.getAttribute('src') !== url) frame.setAttribute('src', url);
  }

  function setPage(value, userInitiated = true) {
    if (userInitiated) interacted = true;
    const page = normalizeDemoPage(value, limit, current);
    if (page !== current) {
      current = page;
      remember();
    }
    render();
    return current;
  }

  function restoreRemotePage(value) {
    if (interacted) return false; // Ne jamais écraser une lecture déjà reprise.
    setPage(value, false);
    return true;
  }

  async function saveBookmark() {
    if (saving) return;
    saving = true;
    const page = current;
    interacted = true;
    const retained = remember();
    if (bookmark) bookmark.disabled = true;
    try {
      const synced = await onBookmark(page);
      if (resume && current === page) resume.textContent = synced
        ? `Page ${page} sauvegardée dans votre compte${retained ? ' et sur cet appareil' : ''}.`
        : retained
          ? `Page ${page} sauvegardée sur cet appareil.`
          : `Page ${page} non mémorisée : stockage local indisponible.`;
    } catch (_) {
      if (resume && current === page) resume.textContent = retained
        ? `Page ${page} sauvegardée localement. Synchronisation indisponible.`
        : `Page ${page} non mémorisée : stockage local et synchronisation indisponibles.`;
    } finally {
      saving = false;
      if (bookmark) bookmark.disabled = false;
    }
  }

  previous?.addEventListener('click', () => setPage(current - 1));
  next?.addEventListener('click', () => setPage(current + 1));
  input?.addEventListener('change', () => setPage(input.value));
  bookmark?.addEventListener('click', saveBookmark);
  controls?.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const target = event.target;
    if (target?.closest?.('input,textarea,select,[contenteditable="true"]')) return;
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    setPage(current + (event.key === 'ArrowRight' ? 1 : -1));
  });

  render();
  return { get currentPage() { return current; }, setPage, restoreRemotePage };
}
