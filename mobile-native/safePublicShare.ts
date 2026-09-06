import { Share } from 'react-native';

const PUBLIC_SHARE_HOSTS = new Set([
  'www.benoitcantin.com',
  'benoitcantin.com',
  'sinjira.com',
  'www.sinjira.com',
]);

const PRIVATE_PATH_PREFIXES = ['/app/', '/compte/', '/admin/', '/auth/', '/api/'] as const;

function canonicalPublicSinjiraUrl(candidate: string): string | null {
  try {
    const parsed = new URL(candidate);
    if (parsed.protocol !== 'https:' || !PUBLIC_SHARE_HOSTS.has(parsed.hostname)) return null;

    const pathname = parsed.pathname || '/';
    const normalizedPath = pathname.toLowerCase();
    const privatePath = PRIVATE_PATH_PREFIXES.some((prefix) => {
      const root = prefix.slice(0, -1);
      return normalizedPath === root || normalizedPath.startsWith(prefix);
    });
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
