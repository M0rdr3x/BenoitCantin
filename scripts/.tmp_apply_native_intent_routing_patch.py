from pathlib import Path

path = Path('mobile-native/App.tsx')
text = path.read_text(encoding='utf-8')
start_marker = "  const navigateToUrl = async (url: string, tab?: TabKey) => {\n"
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
if 'internalIntent.searchParams.get(\'surface\')' in text:
    raise SystemExit('native intent routing patch already present')
start = text.find(start_marker)
if start < 0:
    raise SystemExit('navigateToUrl marker not found')
head, tail = text[:start], text[start:]
if needle not in tail:
    raise SystemExit('vault marker not found after navigateToUrl')
tail = tail.replace(needle, insert + needle, 1)
path.write_text(head + tail, encoding='utf-8')
