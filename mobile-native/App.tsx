import Constants from 'expo-constants';
import * as LocalAuthentication from 'expo-local-authentication';
import * as Notifications from 'expo-notifications';
import * as SecureStore from 'expo-secure-store';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  AppState,
  AppStateStatus,
  BackHandler,
  Linking,
  Platform,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { WebView, WebViewNavigation } from 'react-native-webview';

const DEFAULT_ORIGIN = 'https://www.benoitcantin.com';
const ALLOWED_WEB_HOSTS = new Set(['www.benoitcantin.com', 'benoitcantin.com', 'sinjira.com', 'www.sinjira.com']);
const VAULT_PATH = '/compte/registre-personnel.html';
const PERSONAL_AI_PATH = '/compte/mon-ia.html';
const ACCOUNT_HOME_PATH = '/compte/index.html';
const VAULT_LOCAL_GATE_MS = 90_000;

function configuredWebOrigin() {
  const raw = String(Constants.expoConfig?.extra?.webOrigin || DEFAULT_ORIGIN).replace(/\/+$/, '');
  try {
    const parsed = new URL(raw);
    if (parsed.protocol === 'https:' && ALLOWED_WEB_HOSTS.has(parsed.hostname)) return parsed.origin;
  } catch {}
  return DEFAULT_ORIGIN;
}

const ORIGIN = configuredWebOrigin();
const HOME_URL = `${ORIGIN}/app/`;
const DEVICE_KEY_STORAGE = 'sinjira_native_device_key_v1';
const BIOMETRIC_LOCK_STORAGE = 'sinjira_biometric_lock_v1';
const PUSH_OPT_IN_STORAGE = 'sinjira_security_push_opt_in_v1';
const PUSH_TOKEN_STORAGE = 'sinjira_security_push_token_v1';
const WEB_DEVICE_KEY_STORAGE = 'sinjira.security.device_key.v1';
const WEB_PUSH_TOKEN_STORAGE = 'sinjira.security.push_token.v1';
const WEB_PUSH_ENABLED_STORAGE = 'sinjira.security.push_enabled.v1';
const WEB_PUSH_PLATFORM_STORAGE = 'sinjira.security.push_platform.v1';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: false,
    shouldSetBadge: false,
  }),
});

const tabs = [
  { key: 'home', label: 'Accueil', path: '/app/' },
  { key: 'messages', label: 'Messages', path: '/compte/messages.html' },
  { key: 'dating', label: 'Rencontres', path: '/compte/rencontres.html' },
  { key: 'employment', label: 'Emploi', path: '/compte/emploi.html' },
  { key: 'world', label: 'Monde', path: '/compte/monde-parallele.html' },
  { key: 'ai', label: 'Mon IA', path: PERSONAL_AI_PATH },
] as const;

const quickLinks = [
  { label: 'Alertes', path: '/compte/notifications.html' },
  { label: 'Profil', path: '/compte/profil.html' },
  { label: 'Sécurité', path: '/compte/securite.html' },
  { label: 'Mode Voyage', path: '/compte/securite.html#travel-title' },
  { label: 'Registre perso', path: VAULT_PATH },
] as const;

type TabKey = (typeof tabs)[number]['key'];

function normalizeSinjiraUrl(url: string | null): string | null {
  if (!url) return null;
  if (url.startsWith('sinjira://')) {
    const relativePath = url.replace(/^sinjira:\/\//, '/');
    return `${ORIGIN}${relativePath}`;
  }
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'https:' && ALLOWED_WEB_HOSTS.has(parsed.hostname)) {
      return `${ORIGIN}${parsed.pathname}${parsed.search}${parsed.hash}`;
    }
  } catch {
    return null;
  }
  return null;
}

function isVaultUrl(url: string) {
  try {
    const parsed = new URL(url, ORIGIN);
    return parsed.pathname === VAULT_PATH;
  } catch {
    return false;
  }
}

function isPersonalAiUrl(url: string) {
  try {
    const parsed = new URL(url, ORIGIN);
    return parsed.pathname === PERSONAL_AI_PATH;
  } catch {
    return false;
  }
}

function tabForUrl(url: string): TabKey | null {
  const match = tabs.find((tab) => url.includes(tab.path));
  return match?.key ?? null;
}

function makeDeviceKey() {
  const cryptoObject = globalThis.crypto as Crypto | undefined;
  if (cryptoObject?.randomUUID) return cryptoObject.randomUUID();
  return `sinjira-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
}

function projectId() {
  return Constants.easConfig?.projectId || (Constants.expoConfig?.extra?.eas?.projectId as string | undefined) || '';
}

export default function App() {
  const webViewRef = useRef<WebView>(null);
  const appStateRef = useRef<AppStateStatus>(AppState.currentState);
  const vaultLocalGateUntilRef = useRef(0);
  const [currentUrl, setCurrentUrl] = useState(HOME_URL);
  const [activeTab, setActiveTab] = useState<TabKey>('home');
  const [canGoBack, setCanGoBack] = useState(false);
  const [webViewKey, setWebViewKey] = useState(0);
  const [nativeDeviceKey, setNativeDeviceKey] = useState('');
  const [securityReady, setSecurityReady] = useState(false);
  const [biometricEnabled, setBiometricEnabled] = useState(false);
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [nativeMessage, setNativeMessage] = useState('');
  const [pushEnabled, setPushEnabled] = useState(false);
  const [pushToken, setPushToken] = useState('');

  const allowedHosts = useMemo(() => new Set(ALLOWED_WEB_HOSTS), []);

  const injectedSecurityScript = useMemo(() => {
    if (!nativeDeviceKey) return 'true;';
    const enabled = pushEnabled ? '1' : '0';
    const platform = Platform.OS;
    return `try{localStorage.setItem(${JSON.stringify(WEB_DEVICE_KEY_STORAGE)},${JSON.stringify(nativeDeviceKey)});localStorage.setItem(${JSON.stringify(WEB_PUSH_ENABLED_STORAGE)},${JSON.stringify(enabled)});localStorage.setItem(${JSON.stringify(WEB_PUSH_PLATFORM_STORAGE)},${JSON.stringify(platform)});${pushToken ? `localStorage.setItem(${JSON.stringify(WEB_PUSH_TOKEN_STORAGE)},${JSON.stringify(pushToken)});` : `localStorage.removeItem(${JSON.stringify(WEB_PUSH_TOKEN_STORAGE)});`}setTimeout(()=>import('/assets/js/sinjira-security-push-bridge-v24-4-98.js?v=24.4.99').catch(()=>{}),0);}catch(e){};true;`;
  }, [nativeDeviceKey, pushEnabled, pushToken]);

  const syncPushToWeb = (enabled: boolean, token: string) => {
    const script = `try{localStorage.setItem(${JSON.stringify(WEB_PUSH_ENABLED_STORAGE)},${JSON.stringify(enabled ? '1' : '0')});localStorage.setItem(${JSON.stringify(WEB_PUSH_PLATFORM_STORAGE)},${JSON.stringify(Platform.OS)});${token ? `localStorage.setItem(${JSON.stringify(WEB_PUSH_TOKEN_STORAGE)},${JSON.stringify(token)});` : `localStorage.removeItem(${JSON.stringify(WEB_PUSH_TOKEN_STORAGE)});`}window.dispatchEvent(new Event('sinjira:push-changed'));}catch(e){};true;`;
    webViewRef.current?.injectJavaScript(script);
  };

  const unlockWithBiometrics = async () => {
    try {
      const [hardware, enrolled] = await Promise.all([
        LocalAuthentication.hasHardwareAsync(),
        LocalAuthentication.isEnrolledAsync(),
      ]);
      if (!hardware || !enrolled) {
        await SecureStore.deleteItemAsync(BIOMETRIC_LOCK_STORAGE);
        setBiometricEnabled(false);
        setNativeMessage('Aucune biométrie locale utilisable. Le verrou biométrique a été désactivé pour éviter de vous bloquer.');
        setIsUnlocked(true);
        return true;
      }
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Déverrouiller SINJIRA',
        cancelLabel: 'Annuler',
        disableDeviceFallback: false,
      });
      if (result.success) {
        setNativeMessage('');
        setIsUnlocked(true);
        return true;
      }
      setIsUnlocked(false);
      setNativeMessage('SINJIRA reste verrouillé. Réessayez lorsque vous êtes prêt.');
      return false;
    } catch {
      setIsUnlocked(false);
      setNativeMessage('La vérification locale est temporairement indisponible.');
      return false;
    }
  };

  const requestVaultLocalGate = async () => {
    try {
      const [hardware, enrolled] = await Promise.all([
        LocalAuthentication.hasHardwareAsync(),
        LocalAuthentication.isEnrolledAsync(),
      ]);
      if (!hardware || !enrolled) {
        vaultLocalGateUntilRef.current = Date.now() + VAULT_LOCAL_GATE_MS;
        setNativeMessage('Aucune biométrie locale n’est configurée. Le Registre reste protégé par l’authentification renforcée et le moteur de risque SINJIRA.');
        return true;
      }
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Ouvrir mon Registre personnel',
        cancelLabel: 'Annuler',
        disableDeviceFallback: false,
      });
      if (!result.success) {
        setNativeMessage('Le Registre personnel reste fermé. La vérification locale n’a pas été validée.');
        return false;
      }
      vaultLocalGateUntilRef.current = Date.now() + VAULT_LOCAL_GATE_MS;
      setNativeMessage('Vérification locale réussie. SINJIRA vérifiera ensuite votre MFA et le risque du compte.');
      return true;
    } catch {
      setNativeMessage('La vérification locale du Registre est indisponible. Le Registre personnel reste fermé sur cet appareil.');
      return false;
    }
  };

  const enableSecurityPush = async (quiet = false) => {
    const id = projectId();
    if (!id) {
      if (!quiet) setNativeMessage('Les notifications push seront disponibles dès que le projet mobile sera relié à EAS avec son identifiant de projet.');
      return false;
    }
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('security', {
        name: 'Sécurité SINJIRA',
        importance: Notifications.AndroidImportance.HIGH,
        sound: null,
        lockscreenVisibility: Notifications.AndroidNotificationVisibility.PRIVATE,
      });
    }
    let permission = await Notifications.getPermissionsAsync();
    if (permission.status !== 'granted') permission = await Notifications.requestPermissionsAsync();
    if (permission.status !== 'granted') {
      if (!quiet) setNativeMessage('Permission de notification refusée. SINJIRA continuera de protéger le compte sans notification push.');
      return false;
    }
    const token = (await Notifications.getExpoPushTokenAsync({ projectId: id })).data;
    await SecureStore.setItemAsync(PUSH_OPT_IN_STORAGE, '1');
    await SecureStore.setItemAsync(PUSH_TOKEN_STORAGE, token);
    setPushEnabled(true);
    setPushToken(token);
    syncPushToWeb(true, token);
    if (!quiet) setNativeMessage('Notifications de sécurité activées. Leur contenu restera volontairement discret.');
    return true;
  };

  const disableSecurityPush = async () => {
    await SecureStore.deleteItemAsync(PUSH_OPT_IN_STORAGE);
    await SecureStore.deleteItemAsync(PUSH_TOKEN_STORAGE);
    setPushEnabled(false);
    setPushToken('');
    syncPushToWeb(false, '');
    setNativeMessage('Notifications push de sécurité désactivées sur cet appareil.');
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      let key = await SecureStore.getItemAsync(DEVICE_KEY_STORAGE);
      if (!key) {
        key = makeDeviceKey();
        await SecureStore.setItemAsync(DEVICE_KEY_STORAGE, key);
      }
      const biometric = (await SecureStore.getItemAsync(BIOMETRIC_LOCK_STORAGE)) === '1';
      const push = (await SecureStore.getItemAsync(PUSH_OPT_IN_STORAGE)) === '1';
      const token = (await SecureStore.getItemAsync(PUSH_TOKEN_STORAGE)) || '';
      if (cancelled) return;
      setNativeDeviceKey(key);
      setBiometricEnabled(biometric);
      setPushEnabled(push);
      setPushToken(token);
      if (biometric) await unlockWithBiometrics();
      else setIsUnlocked(true);
      if (!cancelled) setSecurityReady(true);
      if (push && !token) void enableSecurityPush(true);
    })().catch(() => {
      if (!cancelled) {
        setNativeMessage('Le stockage sécurisé local est indisponible.');
        setIsUnlocked(true);
        setSecurityReady(true);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextState) => {
      const previous = appStateRef.current;
      appStateRef.current = nextState;

      if (nextState === 'background' || nextState === 'inactive') {
        vaultLocalGateUntilRef.current = 0;
        if (isVaultUrl(currentUrl)) {
          setCurrentUrl(`${ORIGIN}${ACCOUNT_HOME_PATH}`);
          setCanGoBack(false);
          setWebViewKey((value) => value + 1);
          setNativeMessage('Registre personnel verrouillé automatiquement lorsque SINJIRA a quitté le premier plan.');
        }
        if (isPersonalAiUrl(currentUrl)) {
          setCurrentUrl(`${ORIGIN}${ACCOUNT_HOME_PATH}`);
          setActiveTab('home');
          setCanGoBack(false);
          setWebViewKey((value) => value + 1);
          setNativeMessage('Mon IA privée a été fermée automatiquement lorsque SINJIRA a quitté le premier plan.');
        }
        if (biometricEnabled) setIsUnlocked(false);
      }

      if (
        biometricEnabled &&
        (previous === 'background' || previous === 'inactive') &&
        nextState === 'active'
      ) {
        void unlockWithBiometrics();
      }
    });
    return () => subscription.remove();
  }, [biometricEnabled, currentUrl]);

  const navigateToUrl = async (url: string, tab?: TabKey) => {
    if (isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current) {
      const approved = await requestVaultLocalGate();
      if (!approved) return;
    }
    setCurrentUrl(url);
    if (tab) setActiveTab(tab);
    else {
      const nextTab = tabForUrl(url);
      if (nextTab) setActiveTab(nextTab);
    }
  };

  const navigate = async (path: string, tab?: TabKey) => {
    await navigateToUrl(`${ORIGIN}${path}`, tab);
  };

  useEffect(() => {
    Linking.getInitialURL().then((url) => {
      const normalized = normalizeSinjiraUrl(url);
      if (normalized) void navigateToUrl(normalized);
    });
    const subscription = Linking.addEventListener('url', ({ url }) => {
      const normalized = normalizeSinjiraUrl(url);
      if (normalized) void navigateToUrl(normalized);
    });
    return () => subscription.remove();
  }, []);

  useEffect(() => {
    const subscription = Notifications.addNotificationResponseReceivedListener((response) => {
      const path = response.notification.request.content.data?.path;
      if (typeof path === 'string' && path.startsWith('/') && !path.startsWith('//')) {
        void navigate(path);
      }
    });
    return () => subscription.remove();
  }, []);

  useEffect(() => {
    if (Platform.OS !== 'android') return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!isUnlocked && biometricEnabled) return true;
      if (canGoBack) {
        webViewRef.current?.goBack();
        return true;
      }
      return false;
    });
    return () => subscription.remove();
  }, [canGoBack, isUnlocked, biometricEnabled]);

  const toggleBiometric = async () => {
    if (biometricEnabled) {
      await SecureStore.deleteItemAsync(BIOMETRIC_LOCK_STORAGE);
      setBiometricEnabled(false);
      setIsUnlocked(true);
      setNativeMessage('Protection biométrique locale désactivée. Le Registre personnel conserve sa vérification locale ponctuelle lorsqu’elle est disponible.');
      return;
    }
    const [hardware, enrolled] = await Promise.all([
      LocalAuthentication.hasHardwareAsync(),
      LocalAuthentication.isEnrolledAsync(),
    ]);
    if (!hardware || !enrolled) {
      setNativeMessage('Configurez Face ID, Touch ID ou une empreinte sur le téléphone avant d’activer ce verrou.');
      return;
    }
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: 'Activer la protection biométrique SINJIRA',
      cancelLabel: 'Annuler',
      disableDeviceFallback: false,
    });
    if (!result.success) return;
    await SecureStore.setItemAsync(BIOMETRIC_LOCK_STORAGE, '1');
    setBiometricEnabled(true);
    setIsUnlocked(true);
    setNativeMessage('Protection biométrique locale activée.');
  };

  const onNavigationStateChange = (state: WebViewNavigation) => {
    setCanGoBack(state.canGoBack);
    setCurrentUrl(state.url);
    const nextTab = tabForUrl(state.url);
    if (nextTab) setActiveTab(nextTab);
  };

  const shouldStart = (request: { url: string }) => {
    const { url } = request;
    if (url.startsWith('about:blank')) return true;
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'https:' && allowedHosts.has(parsed.hostname)) {
        if (isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current) {
          void navigate(VAULT_PATH);
          return false;
        }
        return true;
      }
    } catch {
      if (url.startsWith('mailto:') || url.startsWith('tel:')) void Linking.openURL(url);
      return false;
    }
    void Linking.openURL(url);
    return false;
  };

  if (!securityReady) {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar style="light" />
        <View style={styles.loading}>
          <ActivityIndicator size="large" />
          <Text style={styles.loadingText}>Préparation sécurisée de SINJIRA…</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (biometricEnabled && !isUnlocked) {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar style="light" />
        <View style={styles.lockScreen}>
          <Text style={styles.lockTitle}>SINJIRA™ est verrouillé</Text>
          <Text style={styles.lockText}>La biométrie reste sur votre téléphone. SINJIRA ne reçoit ni votre visage ni votre empreinte.</Text>
          {nativeMessage ? <Text style={styles.lockNote}>{nativeMessage}</Text> : null}
          <Pressable accessibilityRole="button" onPress={() => void unlockWithBiometrics()} style={styles.retryButton}>
            <Text style={styles.retryText}>Déverrouiller</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="light" />
      <View style={styles.topbar}>
        <View>
          <Text style={styles.brand}>SINJIRA™</Text>
          <Text style={styles.subtitle}>Application mobile · V25.0</Text>
        </View>
        <View style={styles.topActions}>
          <Pressable accessibilityRole="button" accessibilityLabel="Activer ou désactiver la protection biométrique" onPress={() => void toggleBiometric()} style={styles.refreshButton}>
            <Text style={styles.refreshText}>{biometricEnabled ? 'Bio ✓' : 'Bio'}</Text>
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="Activer ou désactiver les notifications de sécurité" onPress={() => void (pushEnabled ? disableSecurityPush() : enableSecurityPush())} style={styles.refreshButton}>
            <Text style={styles.refreshText}>{pushEnabled ? 'Alertes ✓' : 'Alertes'}</Text>
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="Recharger la page" onPress={() => { webViewRef.current?.reload(); setWebViewKey((value) => value + 1); }} style={styles.refreshButton}>
            <Text style={styles.refreshText}>↻</Text>
          </Pressable>
        </View>
      </View>

      {nativeMessage ? (
        <View style={styles.nativeNotice}>
          <Text style={styles.nativeNoticeText}>{nativeMessage}</Text>
        </View>
      ) : null}

      <View style={styles.quickRail}>
        {quickLinks.map((item) => (
          <Pressable key={item.path} accessibilityRole="button" onPress={() => void navigate(item.path)} style={styles.quickButton}>
            <Text style={styles.quickText}>{item.label}</Text>
          </Pressable>
        ))}
      </View>

      <WebView
        key={webViewKey}
        ref={webViewRef}
        source={{ uri: currentUrl }}
        style={styles.webview}
        originWhitelist={['https://*', 'sinjira://*']}
        sharedCookiesEnabled
        thirdPartyCookiesEnabled={false}
        domStorageEnabled
        javaScriptEnabled
        cacheEnabled
        injectedJavaScriptBeforeContentLoaded={injectedSecurityScript}
        startInLoadingState
        pullToRefreshEnabled={Platform.OS === 'ios'}
        allowsBackForwardNavigationGestures={Platform.OS === 'ios'}
        onNavigationStateChange={onNavigationStateChange}
        onShouldStartLoadWithRequest={shouldStart}
        renderLoading={() => (
          <View style={styles.loading}>
            <ActivityIndicator size="large" />
            <Text style={styles.loadingText}>Chargement de SINJIRA…</Text>
          </View>
        )}
        renderError={() => (
          <View style={styles.errorBox}>
            <Text style={styles.errorTitle}>Connexion indisponible</Text>
            <Text style={styles.errorText}>Vérifiez votre connexion Internet, puis touchez Réessayer.</Text>
            <Pressable accessibilityRole="button" onPress={() => setWebViewKey((value) => value + 1)} style={styles.retryButton}>
              <Text style={styles.retryText}>Réessayer</Text>
            </Pressable>
          </View>
        )}
      />

      <View style={styles.bottomNav}>
        {tabs.map((tab) => {
          const selected = tab.key === activeTab;
          return (
            <Pressable key={tab.key} accessibilityRole="tab" accessibilityState={{ selected }} onPress={() => void navigate(tab.path, tab.key)} style={[styles.tab, selected && styles.tabSelected]}>
              <Text style={[styles.tabText, selected && styles.tabTextSelected]}>{tab.label}</Text>
            </Pressable>
          );
        })}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#070914' },
  topbar: { minHeight: 58, paddingHorizontal: 10, paddingVertical: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#0d1020', borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#2a3047' },
  topActions: { flexDirection: 'row', gap: 5, alignItems: 'center' },
  brand: { color: '#ffffff', fontSize: 20, fontWeight: '800', letterSpacing: 0.4 },
  subtitle: { color: '#9da8c7', fontSize: 11, marginTop: 1 },
  refreshButton: { borderWidth: 1, borderColor: '#384260', borderRadius: 999, paddingHorizontal: 8, paddingVertical: 7 },
  refreshText: { color: '#e9edff', fontWeight: '700', fontSize: 10 },
  nativeNotice: { paddingHorizontal: 12, paddingVertical: 7, backgroundColor: '#12172a' },
  nativeNoticeText: { color: '#c8d0eb', fontSize: 11, textAlign: 'center' },
  quickRail: { flexDirection: 'row', gap: 6, paddingHorizontal: 8, paddingVertical: 8, backgroundColor: '#090c17' },
  quickButton: { flex: 1, minHeight: 34, alignItems: 'center', justifyContent: 'center', borderRadius: 10, borderWidth: 1, borderColor: '#252d45', backgroundColor: '#11162a' },
  quickText: { color: '#dce3ff', fontSize: 10, fontWeight: '700', textAlign: 'center' },
  webview: { flex: 1, backgroundColor: '#070914' },
  loading: { ...StyleSheet.absoluteFill, alignItems: 'center', justifyContent: 'center', gap: 12, backgroundColor: '#070914' },
  loadingText: { color: '#c8d0eb', fontSize: 14 },
  lockScreen: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30, backgroundColor: '#070914' },
  lockTitle: { color: '#ffffff', fontSize: 22, fontWeight: '800', marginBottom: 10, textAlign: 'center' },
  lockText: { color: '#aab3cf', textAlign: 'center', lineHeight: 21, marginBottom: 14 },
  lockNote: { color: '#c8d0eb', textAlign: 'center', fontSize: 12, marginBottom: 16 },
  errorBox: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 28, backgroundColor: '#070914' },
  errorTitle: { color: '#ffffff', fontSize: 19, fontWeight: '800', marginBottom: 8 },
  errorText: { color: '#aab3cf', textAlign: 'center', lineHeight: 20, marginBottom: 18 },
  retryButton: { borderRadius: 10, paddingHorizontal: 18, paddingVertical: 10, backgroundColor: '#e4e9ff' },
  retryText: { color: '#10152a', fontWeight: '800' },
  bottomNav: { minHeight: 58, flexDirection: 'row', paddingHorizontal: 6, paddingTop: 5, paddingBottom: Platform.OS === 'android' ? 6 : 3, backgroundColor: '#0d1020', borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: '#2a3047' },
  tab: { flex: 1, alignItems: 'center', justifyContent: 'center', borderRadius: 10, marginHorizontal: 2 },
  tabSelected: { backgroundColor: '#1b2340' },
  tabText: { color: '#8e98b7', fontSize: 11, fontWeight: '700' },
  tabTextSelected: { color: '#ffffff' },
});