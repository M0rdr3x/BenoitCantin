from pathlib import Path

path = Path('mobile-native/App.tsx')
text = path.read_text(encoding='utf-8')
needle = """    if (isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current) {
"""
insert = """    let internalIntent: URL | null = null;
    try {
      const parsed = new URL(url, ORIGIN);
      if (parsed.protocol === 'https:' && allowedHosts.has(parsed.hostname)) internalIntent = parsed;
    } catch {}

    if (internalIntent && !internalIntent.search && !internalIntent.hash && internalIntent.pathname === '/compte/securite.html') {
      setNativeModulePath(null);
      setNativeHomeOpen(false);
      setNativeSecurityOpen(true);
      setCanGoBack(false);
      setActiveTab(tab ?? 'home');
      return;
    }

    if (
      internalIntent &&
      !internalIntent.hash &&
      internalIntent.searchParams.get('surface') !== 'web' &&
      isNativeModulePath(internalIntent.pathname)
    ) {
      openNativeModule(internalIntent.pathname, tab);
      return;
    }

"""
if text.count(needle) != 1:
    raise SystemExit(f'expected exactly one vault marker, found {text.count(needle)}')
if 'internalIntent.searchParams.get(\'surface\')' in text:
    raise SystemExit('native intent routing patch already present')
path.write_text(text.replace(needle, insert + needle), encoding='utf-8')
