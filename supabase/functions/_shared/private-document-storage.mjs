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

/**
 * Chemin canonique d'un nouveau document : le projet doit venir de la base,
 * pas de l'indice project_slug fourni par le navigateur.
 * UUID généré par crypto.randomUUID() dans l'Edge Function.
 */
export function privateAdminDocumentUploadPath(bucket, projectSlug, baseName, extension, objectId) {
  if (typeof projectSlug !== 'string' || !/^[a-z0-9][a-z0-9_-]{0,95}$/.test(projectSlug)) return null;
  if (typeof baseName !== 'string' || !/^[a-z0-9][a-z0-9._-]{0,119}$/.test(baseName)) return null;
  if (typeof extension !== 'string' || !/^[a-z0-9]{1,10}$/.test(extension)) return null;
  if (typeof objectId !== 'string' ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(objectId)) return null;
  const path = `${projectSlug}/${objectId}/${baseName}.${extension}`;
  return privateDocumentLocationValid(bucket, path) ? path : null;
}
