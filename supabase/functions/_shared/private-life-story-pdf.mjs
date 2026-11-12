/**
 * Flux privé Histoire de vie : lire l'objet Storage avec des octets ET une
 * durée bornés, avant toute attribution du quota de téléchargement.
 *
 * Ne jamais créer ni retourner de signed URL. Aucune requête vers une origine
 * fournie par le client ; l'adresse du projet est un secret d'environnement
 * serveur et la sortie est un corps PDF privé, pas une URL.
 */
import { readLimitedBinaryResponse } from './limited-body.mjs';

const STORAGE_BUCKET = 'sinjira-life-story-exports';
const EXPECTED_HOST = 'gpvivleexywljowcqkru.supabase.co';
const MAX_PDF_BYTES = 15 * 1024 * 1024;
const FETCH_TIMEOUT_MS = 15_000;
const LOCAL_HOSTS = new Set(['127.0.0.1', 'localhost', 'kong']);

function trustedProjectUrl(value) {
  if (typeof value !== 'string' || !value || value.length > 256) return null;
  try {
    const url = new URL(value);
    if (url.username || url.password || url.search || url.hash ||
        (url.pathname !== '/' && url.pathname !== '') ||
        (url.protocol !== 'https:' && url.protocol !== 'http:')) return null;
    if (url.protocol === 'https:') {
      if (url.hostname !== EXPECTED_HOST || url.port) return null;
    } else if (!LOCAL_HOSTS.has(url.hostname)) {
      return null;
    }
    return url;
  } catch { return null; }
}

function safePdfObjectPath(value) {
  if (typeof value !== 'string' || !value || value.length > 512 ||
      !value.toLowerCase().endsWith('.pdf') || value.includes('\\')) return null;
  const parts = value.split('/');
  if (parts.length < 2 || parts.length > 8 ||
      parts.some(p => !p || p === '.' || p === '..' ||
        !/^[a-z0-9_.-]+$/i.test(p))) return null;
  // Rejeter explicitement les segments dot-segment et les composants encodés :
  // l'URL ne doit jamais pouvoir cibler un autre bucket ou endpoint.
  return parts.map(encodeURIComponent).join('/');
}

/**
 * Ne pas exposer la clé de service en dehors d'un GET vers la seule origine
 * Supabase autorisée, sans redirection, sans cookies ni référent.
 */
export async function readPrivateLifeStoryPdf({
  projectUrl, serviceKey, objectPath, maxBytes = MAX_PDF_BYTES,
  timeoutMs = FETCH_TIMEOUT_MS, fetchImpl = fetch
}) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 1 ||
      maxBytes > MAX_PDF_BYTES ||
      !Number.isSafeInteger(timeoutMs) || timeoutMs < 1 ||
      timeoutMs > 30_000) throw new TypeError('Invalid private PDF limit');

  const base = trustedProjectUrl(projectUrl);
  const path = safePdfObjectPath(objectPath);
  if (!base || !path || typeof serviceKey !== 'string' ||
      serviceKey.length < 20) return { ok: false };

  const target = new URL(
    '/storage/v1/object/authenticated/' + STORAGE_BUCKET + '/' + path,
    base
  );
  try {
    const response = await fetchImpl(target.toString(), {
      method: 'GET',
      headers: {
        'apikey': serviceKey,
        'Authorization': 'Bearer ' + serviceKey,
        'Accept': 'application/pdf'
      },
      cache: 'no-store',
      credentials: 'omit',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
      signal: AbortSignal.timeout(timeoutMs)
    });
    if (!response.ok) return { ok: false };
    return await readLimitedBinaryResponse(response, maxBytes, timeoutMs);
  } catch {
    // Aucune exception, requête, URL ou clé n'est reflétée dans la réponse.
    return { ok: false };
  }
}
