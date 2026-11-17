/**
 * The account deletion Edge Function acts with service_role permissions.
 * Database paths are not authorizations: profiles.avatar_path is mutable by
 * the account holder. Validate ALL paths for ALL buckets before the first
 * privileged Storage removal, so an invalid later row cannot cause a partial
 * deletion.
 *
 * Storage policies use the first path segment as owner auth.uid(). Keep the
 * same boundary when deleting with service_role (which bypasses RLS).
 */
const USER_ID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const PATH_SEGMENT_RE = /^[A-Za-z0-9_.-]{1,128}$/;
const MAX_BUCKET_PATHS = 2000;
const MAX_PATH_CHARS = 512;
const BUCKETS = Object.freeze([
  'sinjira-avatars',
  'sinjira-character-sources',
  'sinjira-character-submissions',
]);

function validOwnedPath(path, userId) {
  if (typeof path !== 'string' || !path.startsWith(userId + '/') ||
      path.length > MAX_PATH_CHARS) return false;
  const segments = path.split('/');
  if (segments.length < 2 || segments.length > 7 ||
      segments[0] !== userId) return false;
  return segments.slice(1).every(segment =>
    segment !== '.' && segment !== '..' && PATH_SEGMENT_RE.test(segment)
  );
}

/**
 * Inputs: explicit bucket allowlist -> arrays of nullable database text paths.
 * Null/empty means "no photo". No URL decoding, trimming, coercion, basename
 * inference, or path normalization is permitted for deletion paths.
 */
export function planOwnedAccountStorageDeletes(userId, pathsByBucket) {
  if (typeof userId !== 'string' || !USER_ID_RE.test(userId)) {
    throw new Error('STORAGE_PATH_OWNERSHIP_FAILED');
  }
  if (!pathsByBucket || typeof pathsByBucket !== 'object' ||
      Array.isArray(pathsByBucket) ||
      Object.keys(pathsByBucket).length !== BUCKETS.length ||
      Object.keys(pathsByBucket).some(bucket => !BUCKETS.includes(bucket))) {
    throw new Error('STORAGE_PATH_OWNERSHIP_FAILED');
  }

  const planned = {};
  for (const bucket of BUCKETS) {
    const input = pathsByBucket[bucket];
    if (!Array.isArray(input) || input.length > MAX_BUCKET_PATHS) {
      throw new Error('STORAGE_PATH_OWNERSHIP_FAILED');
    }
    const unique = new Set();
    for (const path of input) {
      if (path === null || path === undefined || path === '') continue;
      if (!validOwnedPath(path, userId)) {
        throw new Error('STORAGE_PATH_OWNERSHIP_FAILED');
      }
      unique.add(path);
    }
    planned[bucket] = [...unique];
  }
  return planned;
}
