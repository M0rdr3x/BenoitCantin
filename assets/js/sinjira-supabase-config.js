// SINJIRA — configuration publique Supabase
export const SINJIRA_CONFIG = Object.freeze({
  supabaseUrl: 'https://gpvivleexywljowcqkru.supabase.co',
  supabasePublishableKey: 'sb_publishable_NVG-HUspfsZt2ESeEVTQ5Q_viDhOGNZ',
  siteUrl: 'https://www.benoitcantin.com',
  contributionConsentVersion: 'sinjira-gameplay-v3-endgame-only',
  privateDocumentBucket: 'sinjira-private-documents',
  avatarBucket: 'sinjira-avatars',
  freeOnlyMode: true,
  paidFeaturesEnabled: false,
  paidExternalServicesEnabled: false,
  remoteAiEnabled: false,
  externalEmailDeliveryEnabled: false,
  commercePublishingEnabled: false,
  tokenPurchasesEnabled: false,
  nativeStorePublishingEnabled: false
});
export function isSinjiraBackendConfigured() {
  return SINJIRA_CONFIG.supabaseUrl.startsWith('https://')
    && !SINJIRA_CONFIG.supabaseUrl.includes('VOTRE-PROJET')
    && SINJIRA_CONFIG.supabasePublishableKey.length > 20
    && !SINJIRA_CONFIG.supabasePublishableKey.includes('VOTRE_CLE');
}
export function isSinjiraFreeOnlyMode(){
  return SINJIRA_CONFIG.freeOnlyMode === true
    && SINJIRA_CONFIG.paidFeaturesEnabled === false
    && SINJIRA_CONFIG.paidExternalServicesEnabled === false
    && SINJIRA_CONFIG.remoteAiEnabled === false
    && SINJIRA_CONFIG.externalEmailDeliveryEnabled === false
    && SINJIRA_CONFIG.commercePublishingEnabled === false
    && SINJIRA_CONFIG.tokenPurchasesEnabled === false
    && SINJIRA_CONFIG.nativeStorePublishingEnabled === false;
}
