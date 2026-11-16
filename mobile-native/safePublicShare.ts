import { Share } from 'react-native';

const PUBLIC_SHARE_HOSTS = new Set([
  'www.benoitcantin.com',
  'benoitcantin.com',
  'sinjira.com',
  'www.sinjira.com',
]);

const PRIVATE_PATH_PREFIXES = ['/app/', '/compte/', '/admin/', '/auth/', '/api/'] as const;
const PRIVATE_EXTRA_PREFIXES = ['/histoire-de-vie/', '/supabase/'] as const;
const PRIVATE_EXACT_PATHS = new Set(['/administration.html']);

function canonicalPublicSinjiraUrl(candidate: string): string | null {
  try {
    const parsed = new URL(candidate);
    if (parsed.protocol !== 'https:' || parsed.port || parsed.username || parsed.password || !PUBLIC_SHARE_HOSTS.has(parsed.hostname)) return null;

    const pathname = parsed.pathname || '/';
    let normalizedPath: string;
    // Un séparateur encodé peut être réinterprété après le contrôle du chemin.
    if (/%(?:2f|5c)/i.test(pathname)) return null;
    try { normalizedPath = decodeURIComponent(pathname).toLowerCase(); }
    catch { return null; }
    if (/[\\%\u0000-\u001f\u007f]/.test(normalizedPath) || normalizedPath.startsWith('//')) return null;
    const privatePath = PRIVATE_PATH_PREFIXES.some((prefix) => {
      const root = prefix.slice(0, -1);
      return normalizedPath === root || normalizedPath.startsWith(prefix);
    }) || PRIVATE_EXTRA_PREFIXES.some((prefix) => {
      const root = prefix.slice(0, -1);
      return normalizedPath === root || normalizedPath.startsWith(prefix);
    }) || PRIVATE_EXACT_PATHS.has(normalizedPath);
    if (privatePath) return null;

    return `${parsed.origin}${pathname}`;
  } catch {
    return null;
  }
}

export async function sharePublicSinjiraUrl(candidate: string) {
  const shareUrl = canonicalPublicSinjiraUrl(candidate);
  if (!shareUrl) throw new Error('PUBLIC_SHARE_URL_REQUIRED');

  return Share.share({
    title: 'SINJIRA™',
    message: `SINJIRA™ — ${shareUrl}`,
    url: shareUrl,
  });
}
