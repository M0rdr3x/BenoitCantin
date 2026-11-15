/**
 * Fail-closed: les documents personnels Histoire de vie ne peuvent ni être
 * générés, ni être distribués depuis un bucket rendu public par erreur.
 * Le SDK Storage est fourni uniquement côté serveur (service role).
 * Aucun identifiant client, jeton de remise ou clé service n'est journalisé.
 */
export const LIFE_STORY_PRIVATE_BUCKET = 'sinjira-life-story-exports';

export function isVerifiedPrivateLifeStoryBucket(metadata) {
  return metadata !== null &&
    typeof metadata === 'object' &&
    !Array.isArray(metadata) &&
    metadata.id === LIFE_STORY_PRIVATE_BUCKET &&
    metadata.public === false;
}

export async function hasVerifiedPrivateLifeStoryBucket(storage) {
  if (!storage || typeof storage.getBucket !== 'function') return false;
  try {
    const {data, error} = await storage.getBucket(LIFE_STORY_PRIVATE_BUCKET);
    return !error && isVerifiedPrivateLifeStoryBucket(data);
  } catch {
    // Toute erreur réseau, permission ou métadonnée inconnue bloque la remise.
    return false;
  }
}
