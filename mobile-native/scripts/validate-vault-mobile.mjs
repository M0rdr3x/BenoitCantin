import { readFileSync } from 'node:fs';

function read(path) {
  return readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
}

function requireMarkers(text, markers, label) {
  const missing = markers.filter((marker) => !text.includes(marker));
  if (missing.length) throw new Error(`${label}: marqueurs absents: ${missing.join(', ')}`);
}

function forbidMarkers(text, markers, label) {
  const found = markers.filter((marker) => text.includes(marker));
  if (found.length) throw new Error(`${label}: marqueurs interdits: ${found.join(', ')}`);
}

const app = read('App.tsx');
const config = JSON.parse(read('app.json'));

requireMarkers(app, [
  "const VAULT_PATH = '/compte/registre-personnel.html';",
  'const VAULT_LOCAL_GATE_MS = 90_000;',
  "{ label: 'Registre perso', path: VAULT_PATH }",
  'const vaultLocalGateUntilRef = useRef(0);',
  'const requestVaultLocalGate = async () => {',
  "promptMessage: 'Ouvrir mon Registre personnel'",
  'LocalAuthentication.hasHardwareAsync()',
  'LocalAuthentication.isEnrolledAsync()',
  'vaultLocalGateUntilRef.current = Date.now() + VAULT_LOCAL_GATE_MS;',
  'if (isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current)',
  'void navigate(VAULT_PATH);',
  "if (isVaultUrl(currentUrl)) {",
  'setCurrentUrl(`${ORIGIN}${ACCOUNT_HOME_PATH}`);',
  'setWebViewKey((value) => value + 1);',
  "Registre personnel verrouillé automatiquement lorsque SINJIRA a quitté le premier plan.",
  'injectedJavaScriptBeforeContentLoaded={injectedSecurityScript}',
  "const DEVICE_KEY_STORAGE = 'sinjira_native_device_key_v1';",
  'SecureStore.getItemAsync(DEVICE_KEY_STORAGE)',
  'SecureStore.setItemAsync(DEVICE_KEY_STORAGE, key)',
  'Application mobile · V25.0',
], 'contrat mobile V25 du Registre personnel');

requireMarkers(app, [
  "const PERSONAL_AI_PATH = '/compte/mon-ia.html';",
  "{ key: 'ai', label: 'Mon IA', path: PERSONAL_AI_PATH }",
  'function isPersonalAiUrl(url: string)',
  "if (isPersonalAiUrl(currentUrl)) {",
  "setActiveTab('home');",
  "Mon IA privée a été fermée automatiquement lorsque SINJIRA a quitté le premier plan.",
], 'contrat mobile V25 de Mon IA privée');

requireMarkers(app, [
  "{ key: 'home', label: 'Accueil', path: '/app/' }",
  "{ key: 'messages', label: 'Messages', path: '/compte/messages.html' }",
  "{ key: 'dating', label: 'Rencontres', path: '/compte/rencontres.html' }",
  "{ key: 'employment', label: 'Emploi', path: '/compte/emploi.html' }",
  "{ key: 'world', label: 'Monde', path: '/compte/monde-parallele.html' }",
  "{ key: 'ai', label: 'Mon IA', path: PERSONAL_AI_PATH }",
  "{ label: 'Alertes', path: '/compte/notifications.html' }",
  "{ label: 'Profil', path: '/compte/profil.html' }",
  "{ label: 'Sécurité', path: '/compte/securite.html' }",
  "{ label: 'Mode Voyage', path: '/compte/securite.html#travel-title' }",
  "const [activeTab, setActiveTab] = useState<TabKey>('home');",
], 'navigation mobile V25 limitée aux modules réellement disponibles');

forbidMarkers(app, [
  "{ key: 'profile', label: 'Profil', path: '/compte/profil.html' }",
  "{ label: 'Registre',",
  'conscience-vault',
  'vault_session_id',
  'content_payload',
  'service_conscience_',
  'conscience_entries',
  'conscience_vault_sessions',
  'conscience_vault_audit',
  'AsyncStorage',
  'expo-file-system',
  'FileSystem.',
  'Clipboard.',
  'Share.share(',
  'downloadAsync(',
], 'le natif ne reçoit, ne stocke et n’exporte jamais le contenu du coffre');

forbidMarkers(app, [
  "functions.invoke('personal-ai'",
  'service_personal_ai_',
  'personal_ai_settings',
  'personal_ai_source_permissions',
  'personal_ai_audit',
  'source_permissions',
  'conversation_enabled',
  'memory_enabled',
  'source_retrieval_enabled',
  'provider_configured',
], 'le natif ne reçoit ni ne stocke l’état de Mon IA et ne contourne jamais l Edge Web sécurisée');

forbidMarkers(app, [
  'security_travel_windows',
  'security_travel_plans',
  'travel_destinations',
  'travel_starts_at',
  'travel_ends_at',
  'travel_multi_country',
  "destinations:",
  "starts_at:",
  "ends_at:",
  "multi_country:",
], 'Mode Voyage reste géré côté Web/serveur; le natif ne stocke ni destination ni période de voyage');

forbidMarkers(app, [
  "{ key: 'feed', label: 'Fil'",
  "{ key: 'alerts', label: 'Alertes'",
  "{ label: 'Rencontres', path: '/compte/rencontres.html' }",
], 'aucun onglet obsolète ou doublon secondaire');

if (config?.expo?.version !== '25.0.0') throw new Error('app.json: version V25.0.0 requise');
if (config?.expo?.ios?.buildNumber !== '25000') throw new Error('app.json: buildNumber iOS 25000 requis');
if (config?.expo?.android?.versionCode !== 25000) throw new Error('app.json: versionCode Android 25000 requis');
if (config?.expo?.scheme !== 'sinjira') throw new Error('app.json: schéma sinjira requis pour les liens profonds');

console.log('OK mobile V25: Emploi, Mon IA et accès direct Mode Voyage présents; Registre personnel protégé; aucune donnée privée du coffre, de l IA ou du voyage dans le natif.');
