/**
 * Contrôle fail-closed de toute URL Storage générée par get-document-url.
 * Une URL « signée » ne rend pas privé un objet situé dans un bucket public.
 * Ne remplace jamais la vérification d'identité et du rang d'accès.
 */
export function privateDocumentLocationValid(bucket, storagePath) {
  if (typeof bucket !== 'string' || !/^[a-z0-9][a-z0-9._-]{0,62}$/.test(bucket)) return false;
  if (typeof storagePath !== 'string' || !storagePath || storagePath.length > 1024 ||
      storagePath !== storagePath.trim()) return false;
  // Aucune traversée, double interprétation d'URL ou fragment dans les chemins.
  // Contrairement aux romans, les documents peuvent être de plusieurs formats.
  if (/[\u0000-\u001f\u007f\\?#%]/u.test(storagePath)) return false;
  return storagePath.split('/').every(segment =>
    segment !== '' && segment !== '.' && segment !== '..' &&
    segment === segment.trim()
  );
}

export function isVerifiedPrivateDocumentBucket(metadata, expectedBucketId) {
  return typeof expectedBucketId === 'string' &&
    metadata !== null && typeof metadata === 'object' &&
    !Array.isArray(metadata) &&
    metadata.id === expectedBucketId &&
    metadata.public === false;
}
