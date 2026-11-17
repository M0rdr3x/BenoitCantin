/**
 * Refuse les chemins privés ambigus et les buckets Supabase publics.
 * Cette vérification ne remplace jamais les droits du compte.
 */
export function privateBookLocationValid(bucket, storagePath) {
  if (typeof bucket !== 'string' || !/^[a-z0-9][a-z0-9._-]{0,62}$/.test(bucket)) return false;
  if (typeof storagePath !== 'string' || !storagePath || storagePath.length > 1024 ||
      storagePath !== storagePath.trim()) return false;
  // Empêcher traversée, double encodage et fragments/paramètres dans l'objet PDF.
  if (!/\.pdf$/i.test(storagePath) || /[\u0000-\u001f\u007f\\?#%]/u.test(storagePath)) return false;
  return storagePath.split('/').every(segment =>
    segment !== '' && segment !== '.' && segment !== '..' && segment === segment.trim()
  );
}

export function isVerifiedPrivateBucket(metadata, expectedBucketId) {
  return typeof expectedBucketId === 'string' &&
    metadata !== null && typeof metadata === 'object' &&
    !Array.isArray(metadata) &&
    metadata.id === expectedBucketId &&
    metadata.public === false;
}
