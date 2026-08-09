// SINJIRA — configuration publique
export const SINJIRA_CONFIG = Object.freeze({
  supabaseUrl: 'https://VOTRE-PROJET.supabase.co',
  supabasePublishableKey: 'VOTRE_CLE_PUBLIQUE_SUPABASE',
  siteUrl: 'https://www.benoitcantin.com',
  contributionConsentVersion: 'sinjira-gameplay-v2',
  privateDocumentBucket: 'sinjira-private-documents'
});
export function isSinjiraBackendConfigured() {
  return SINJIRA_CONFIG.supabaseUrl.startsWith('https://')
    && !SINJIRA_CONFIG.supabaseUrl.includes('VOTRE-PROJET')
    && SINJIRA_CONFIG.supabasePublishableKey.length > 20
    && !SINJIRA_CONFIG.supabasePublishableKey.includes('VOTRE_CLE');
}
