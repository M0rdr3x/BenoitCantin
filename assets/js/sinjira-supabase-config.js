// SINJIRA — configuration publique
export const SINJIRA_CONFIG = Object.freeze({
  supabaseUrl: 'https://gpvivleexywljowcqkru.supabase.co',
  supabasePublishableKey: 'sb_publishable_NVG-HUspfsZt2ESeEVTQ5Q_viDhOGNZ',
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
