/**
 * Source photos are private, per-account Storage objects. Do not use a path
 * copied from a database row for service-role signing/deletion until that
 * path has been matched to the database-owned user_id.
 *
 * Contract matches the Registry's public upload validator:
 *   <account UUID>/<crypto.randomUUID()>.(jpg|png|webp|avif|gif)
 *
 * Fail closed for legacy/invalid rows. Never attempt to normalize or decode
 * suspicious paths and never include rejected paths in logs.
 */
export function isCanonicalRegistrySourcePhotoPath(raw, userId) {
  if (typeof userId !== 'string' ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(userId)) {
    return false;
  }
  if (typeof raw !== 'string') return false;
  const prefix = `${userId}/`;
  if (!raw.startsWith(prefix) || raw.length > prefix.length + 41) return false;
  return /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.(?:jpg|png|webp|avif|gif)$/.test(raw.slice(prefix.length));
}
