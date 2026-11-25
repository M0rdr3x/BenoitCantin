/**
 * Contrôle fail-closed de toute URL Storage générée par get-document-url.
 * Une URL « signée » ne rend pas privé un objet situé dans un bucket public.
 * Ne remplace jamais la vérification d'identité et du rang d'accès.
 */
export function privateDocumentLocationValid(bucket, storagePath) {
  if (typeof bucket !== 'string' || bucket !== bucket.trim() || !/^[a-z0-9][a-z0-9._-]{0,62}$/.test(bucket)) return false;
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
  if (typeof baseName !== 'string' || !/^[a-z0-9][a-z0-9._-]{0,119}$/.test(baseName) || baseName.endsWith('.')) return null;
  if (typeof extension !== 'string' || !/^[a-z0-9]{1,10}$/.test(extension)) return null;
  if (typeof objectId !== 'string' ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(objectId)) return null;
  const path = `${projectSlug}/${objectId}/${baseName}.${extension}`;
  return privateDocumentLocationValid(bucket, path) ? path : null;
}

/**
 * Une réponse du fournisseur n'est pas une autorisation de redirection.
 * Vérifier l'origine HTTPS configurée côté serveur, la route de signature,
 * le bucket et chaque composante du chemin exact, et les paramètres attendus.
 * La signature cryptographique du jeton reste vérifiée par Storage.
 */
export function privateSignedDownloadUrlValid(value, baseUrl, bucket, storagePath, downloadName = null) {
  if (!privateDocumentLocationValid(bucket, storagePath) ||
      typeof value !== 'string' || value.length > 16384 ||
      !value.startsWith('https://') || /[\u0000-\u0020\u007f\\#]/u.test(value) ||
      typeof baseUrl !== 'string' || !baseUrl.startsWith('https://') ||
      /[\u0000-\u0020\u007f\\?#]/u.test(baseUrl)) return false;
  try {
    const base = new URL(baseUrl);
    const parsed = new URL(value);
    if (base.protocol !== 'https:' || base.username || base.password ||
        base.pathname !== '/' || base.search || base.hash ||
        parsed.origin !== base.origin || parsed.username || parsed.password ||
        parsed.hash) return false;
    const rawPath = value.slice('https://'.length).split('?')[0];
    const slash = rawPath.indexOf('/');
    // Empêcher toute normalisation silencieuse du chemin par URL.
    if (slash < 0 || rawPath.slice(slash) !== parsed.pathname) return false;
    const prefix = '/storage/v1/object/sign/';
    if (!parsed.pathname.startsWith(prefix)) return false;
    const actual = parsed.pathname.slice(prefix.length).split('/').map(decodeURIComponent);
    const expected = [bucket, ...storagePath.split('/')];
    if (actual.length !== expected.length || actual.some((part, i) => part !== expected[i])) return false;
    const params = parsed.searchParams;
    const tokens = params.getAll('token');
    if (tokens.length !== 1 || !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(tokens[0]) ||
        tokens[0] !== tokens[0].trim()) return false;
    const downloads = params.getAll('download');
    if (downloadName === null ? downloads.length !== 0 :
        typeof downloadName !== 'string' || downloads.length !== 1 || downloads[0] !== downloadName) return false;
    return [...params.keys()].every(key => key === 'token' || key === 'download');
  } catch {
    return false;
  }
}
