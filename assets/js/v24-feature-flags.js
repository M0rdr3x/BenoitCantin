// SINJIRA™ V24 — fonctionnalités pouvant être activées sans reconstruire l'interface.
export const V24_FEATURES = Object.freeze({
  ai: false,
  market: false,
  marketPayments: false,
  tokenPurchases: false,
  parallelWorld: true,
  community: true,
  realtimeChannels: false,
  voiceVideo: false,
  fractureOnlineLicensing: false,
  codex: true
});
export function featureEnabled(name){ return V24_FEATURES[name] === true; }
