// Les chemins de portrait proviennent de métadonnées et restent non fiables.
// Refuser les requêtes d'images vers des domaines tiers et les URLs ambiguës.
export function safeCharacterPortraitPath(value) {
  if (typeof value !== 'string' || !value || value.length > 2048 ||
      value !== value.trim() || !value.startsWith('/') ||
      value.startsWith('//') ||
      /[\u0000-\u0020\u007f\\?#]/.test(value)) return '';

  // Ne conserver que les images publiques du site : aucun compte, API ou
  // document privé ne doit être requis pour afficher un portrait.
  if (!value.startsWith('/assets/') && !value.startsWith('/projets/sinjira/')) return '';
  if (!/\.(?:png|jpe?g|webp|gif|avif|svg)$/i.test(value)) return '';

  // La normalisation ne doit pas réécrire les segments de chemin.
  // Elle détecte /../, les encodages de points et autres formes ambiguës.
  if (/%(?:2f|5c|0[0-9a-f]|1[0-9a-f]|7f)/i.test(value)) return '';
  try {
    const url = new URL(value, 'https://portrait.invalid');
    if (url.origin !== 'https://portrait.invalid' ||
        url.pathname !== value || url.username || url.password ||
        url.search || url.hash) return '';
    return url.pathname;
  } catch {
    return '';
  }
}
