import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
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

const ORIGIN = 'https://www.benoitcantin.com';
const HOME_URL = `${ORIGIN}/app/`;

const tabs = [
  { key: 'feed', label: 'Fil', path: '/app/' },
  { key: 'world', label: 'Monde', path: '/compte/monde-parallele.html' },
  { key: 'messages', label: 'Messages', path: '/compte/messages.html' },
  { key: 'alerts', label: 'Alertes', path: '/compte/notifications.html' },
  { key: 'profile', label: 'Profil', path: '/compte/profil.html' },
] as const;

const quickLinks = [
  { label: 'Registre', path: '/projets/sinjira/registre/' },
  { label: 'Personnage', path: '/compte/reseau-personnage.html' },
  { label: 'Rencontres 18+', path: '/compte/rencontres.html' },
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
    if (parsed.hostname === 'www.benoitcantin.com' || parsed.hostname === 'benoitcantin.com') {
      return `${ORIGIN}${parsed.pathname}${parsed.search}${parsed.hash}`;
    }
  } catch {
    return null;
  }

  return null;
}

function tabForUrl(url: string): TabKey | null {
  const match = tabs.find((tab) => url.includes(tab.path));
  return match?.key ?? null;
}

export default function App() {
  const webViewRef = useRef<WebView>(null);
  const [currentUrl, setCurrentUrl] = useState(HOME_URL);
  const [activeTab, setActiveTab] = useState<TabKey>('feed');
  const [canGoBack, setCanGoBack] = useState(false);
  const [webViewKey, setWebViewKey] = useState(0);

  const allowedHosts = useMemo(
    () => new Set(['www.benoitcantin.com', 'benoitcantin.com']),
    [],
  );

  useEffect(() => {
    Linking.getInitialURL().then((url) => {
      const normalized = normalizeSinjiraUrl(url);
      if (normalized) {
        setCurrentUrl(normalized);
        setActiveTab(tabForUrl(normalized) ?? 'feed');
      }
    });

    const subscription = Linking.addEventListener('url', ({ url }) => {
      const normalized = normalizeSinjiraUrl(url);
      if (normalized) {
        setCurrentUrl(normalized);
        setActiveTab(tabForUrl(normalized) ?? 'feed');
      }
    });

    return () => subscription.remove();
  }, []);

  useEffect(() => {
    if (Platform.OS !== 'android') return;

    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
      if (canGoBack) {
        webViewRef.current?.goBack();
        return true;
      }
      return false;
    });

    return () => subscription.remove();
  }, [canGoBack]);

  const navigate = (path: string, tab?: TabKey) => {
    const url = `${ORIGIN}${path}`;
    setCurrentUrl(url);
    if (tab) setActiveTab(tab);
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
      if (allowedHosts.has(parsed.hostname)) return true;
    } catch {
      if (url.startsWith('mailto:') || url.startsWith('tel:')) {
        void Linking.openURL(url);
      }
      return false;
    }

    void Linking.openURL(url);
    return false;
  };

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="light" />

      <View style={styles.topbar}>
        <View>
          <Text style={styles.brand}>SINJIRA™</Text>
          <Text style={styles.subtitle}>Application mobile</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Recharger la page"
          onPress={() => {
            webViewRef.current?.reload();
            setWebViewKey((value) => value + 1);
          }}
          style={styles.refreshButton}
        >
          <Text style={styles.refreshText}>Actualiser</Text>
        </Pressable>
      </View>

      <View style={styles.quickRail}>
        {quickLinks.map((item) => (
          <Pressable
            key={item.path}
            accessibilityRole="button"
            onPress={() => navigate(item.path)}
            style={styles.quickButton}
          >
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
            <Text style={styles.errorText}>
              Vérifiez votre connexion Internet, puis touchez Réessayer.
            </Text>
            <Pressable
              accessibilityRole="button"
              onPress={() => setWebViewKey((value) => value + 1)}
              style={styles.retryButton}
            >
              <Text style={styles.retryText}>Réessayer</Text>
            </Pressable>
          </View>
        )}
      />

      <View style={styles.bottomNav}>
        {tabs.map((tab) => {
          const selected = tab.key === activeTab;
          return (
            <Pressable
              key={tab.key}
              accessibilityRole="tab"
              accessibilityState={{ selected }}
              onPress={() => navigate(tab.path, tab.key)}
              style={[styles.tab, selected && styles.tabSelected]}
            >
              <Text style={[styles.tabText, selected && styles.tabTextSelected]}>{tab.label}</Text>
            </Pressable>
          );
        })}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#070914',
  },
  topbar: {
    minHeight: 58,
    paddingHorizontal: 16,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#0d1020',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#2a3047',
  },
  brand: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: 0.4,
  },
  subtitle: {
    color: '#9da8c7',
    fontSize: 11,
    marginTop: 1,
  },
  refreshButton: {
    borderWidth: 1,
    borderColor: '#384260',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  refreshText: {
    color: '#e9edff',
    fontWeight: '700',
    fontSize: 12,
  },
  quickRail: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: '#090c17',
  },
  quickButton: {
    flex: 1,
    minHeight: 34,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#252d45',
    backgroundColor: '#11162a',
  },
  quickText: {
    color: '#dce3ff',
    fontSize: 11,
    fontWeight: '700',
    textAlign: 'center',
  },
  webview: {
    flex: 1,
    backgroundColor: '#070914',
  },
  loading: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    backgroundColor: '#070914',
  },
  loadingText: {
    color: '#c8d0eb',
    fontSize: 14,
  },
  errorBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 28,
    backgroundColor: '#070914',
  },
  errorTitle: {
    color: '#ffffff',
    fontSize: 19,
    fontWeight: '800',
    marginBottom: 8,
  },
  errorText: {
    color: '#aab3cf',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 18,
  },
  retryButton: {
    borderRadius: 10,
    paddingHorizontal: 18,
    paddingVertical: 10,
    backgroundColor: '#e4e9ff',
  },
  retryText: {
    color: '#10152a',
    fontWeight: '800',
  },
  bottomNav: {
    minHeight: 58,
    flexDirection: 'row',
    paddingHorizontal: 6,
    paddingTop: 5,
    paddingBottom: Platform.OS === 'android' ? 6 : 3,
    backgroundColor: '#0d1020',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#2a3047',
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
    marginHorizontal: 2,
  },
  tabSelected: {
    backgroundColor: '#1b2340',
  },
  tabText: {
    color: '#8e98b7',
    fontSize: 11,
    fontWeight: '700',
  },
  tabTextSelected: {
    color: '#ffffff',
  },
});
