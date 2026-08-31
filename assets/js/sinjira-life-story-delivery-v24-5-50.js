(() => {
  const ENDPOINT = 'https://gpvivleexywljowcqkru.supabase.co/functions/v1/life-story-delivery';
  const MAX_PDF_BYTES = 15 * 1024 * 1024;
  const TOKEN_RE = /^[a-f0-9]{64}$/;
  const statusNode = document.querySelector('[data-delivery-status]');
  const downloadNode = document.querySelector('[data-delivery-download]');
  let objectUrl = '';

  function setStatus(message, kind = '') {
    if (!statusNode) return;
    statusNode.textContent = message;
    statusNode.dataset.kind = kind;
  }

  function safeFilename(disposition) {
    const match = /filename="?([^";]+)"?/i.exec(disposition || '');
    const raw = match?.[1] || 'histoire-de-vie-sinjira.pdf';
    const cleaned = raw.replace(/[^a-z0-9._-]/gi, '-').replace(/-+/g, '-').slice(0, 120);
    return cleaned.toLowerCase().endsWith('.pdf') ? cleaned : `${cleaned}.pdf`;
  }

  async function hasPdfSignature(blob) {
    if (blob.size < 5) return false;
    const head = new Uint8Array(await blob.slice(0, 5).arrayBuffer());
    return String.fromCharCode(...head) === '%PDF-';
  }

  async function start() {
    const fragment = location.hash.startsWith('#') ? location.hash.slice(1) : '';
    let token = '';
    try { token = decodeURIComponent(fragment); } catch { token = fragment; }

    history.replaceState(null, document.title, location.pathname + location.search);

    if (!TOKEN_RE.test(token)) {
      setStatus('Ce lien de remise est invalide ou incomplet.', 'error');
      return;
    }

    setStatus('Vérification sécurisée du lien…');
    try {
      const response = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
        cache: 'no-store',
        credentials: 'omit',
        mode: 'cors',
        referrerPolicy: 'no-referrer',
      });
      token = '';

      if (!response.ok) throw new Error('DELIVERY_UNAVAILABLE');
      const type = (response.headers.get('content-type') || '').toLowerCase();
      if (!type.startsWith('application/pdf')) throw new Error('INVALID_CONTENT_TYPE');

      const blob = await response.blob();
      if (blob.size <= 0 || blob.size > MAX_PDF_BYTES || !(await hasPdfSignature(blob))) throw new Error('INVALID_PDF');

      objectUrl = URL.createObjectURL(blob);
      if (!downloadNode) throw new Error('DOWNLOAD_UI_MISSING');
      downloadNode.href = objectUrl;
      downloadNode.download = safeFilename(response.headers.get('content-disposition'));
      downloadNode.hidden = false;
      setStatus('Le PDF est prêt. Si le téléchargement ne démarre pas automatiquement, utilisez le bouton ci-dessous.', 'success');
      downloadNode.click();
    } catch {
      token = '';
      setStatus('Ce lien de remise n’est pas disponible. Il peut être expiré, révoqué ou avoir atteint sa limite de téléchargements.', 'error');
    }
  }

  window.addEventListener('pagehide', () => {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
  }, { once: true });

  void start();
})();
