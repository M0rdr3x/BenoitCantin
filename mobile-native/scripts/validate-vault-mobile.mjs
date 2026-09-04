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
  "{ key: 'home', label: 'Accueil', path: '/app/' }",
  "{ key: 'messages', label: 'Messages', path: '/compte/messages.html' }",
  "{ key: 'dating', label: 'Rencontres', path: '/compte/rencontres.html' }",
  "{ key: 'employment', label: 'Emploi', path: '/compte/emploi.html' }",
  "{ key: 'world', label: 'Monde', path: '/compte/monde-parallele.html' }",
  "{ label: 'Alertes', path: '/compte/notifications.html' }",
  "{ label: 'Profil', path: '/compte/profil.html' }",
  "{ label: 'Sécurité', path: '/compte/securite.html' }",
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
  "{ key: 'feed', label: 'Fil'",
  "{ key: 'alerts', label: 'Alertes'",
  "{ label: 'Rencontres', path: '/compte/rencontres.html' }",
  '/compte/mon-ia.html',
], 'aucun onglet obsolète ou destination mobile non implémentée');

if (config?.expo?.version !== '25.0.0') throw new Error('app.json: version V25.0.0 requise');
if (config?.expo?.ios?.buildNumber !== '25000') throw new Error('app.json: buildNumber iOS 25000 requis');
if (config?.expo?.android?.versionCode !== 25000) throw new Error('app.json: versionCode Android 25000 requis');
if (config?.expo?.scheme !== 'sinjira') throw new Error('app.json: schéma sinjira requis pour les liens profonds');

console.log('OK mobile V25: Emploi dans la navigation principale, Profil secondaire, Registre personnel protégé et aucun contenu du coffre dans le natif.');
