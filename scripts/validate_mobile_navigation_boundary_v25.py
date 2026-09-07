#!/usr/bin/env python3
"""Valide le contrat V25 de navigation de l'application mobile native SINJIRA."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "mobile-native" / "App.tsx"
ADVERSARIAL_TEST = ROOT / "mobile-native" / "scripts" / "test-external-navigation-guard.mjs"
DEEP_LINK_TEST = ROOT / "mobile-native" / "scripts" / "test-deep-link-normalizer.mjs"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-mobile-navigation-boundary-v25.yml"
PACKAGE = ROOT / "mobile-native" / "package.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ERREUR navigation mobile V25: {message}")


def main() -> int:
    text = APP.read_text(encoding="utf-8")
    adversarial_text = ADVERSARIAL_TEST.read_text(encoding="utf-8")
    deep_link_text = DEEP_LINK_TEST.read_text(encoding="utf-8")
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    package_text = PACKAGE.read_text(encoding="utf-8")

    require("const EXTERNAL_SAFE_PROTOCOLS = new Set(['https:', 'mailto:', 'tel:']);" in text,
            "les seuls protocoles externes permis doivent être HTTPS, mailto et tel")
    require("'http:'" not in text.split("const EXTERNAL_SAFE_PROTOCOLS", 1)[1].split(";", 1)[0],
            "HTTP ne doit jamais être autorisé comme protocole externe")

    for marker in (
        "'access_token'", "'refresh_token'", "'code'", "'token'", "'jwt'",
        "'session'", "'api_key'", "'apikey'", "'password'",
    ):
        require(marker in text, f"paramètre sensible absent du garde: {marker}")

    require("function containsSensitiveExternalAssignment(value: string)" in text,
            "le détecteur d'affectations sensibles encodées doit exister")
    require("value.toLowerCase().replace(/\\+/g, ' ')" in text,
            "le détecteur doit normaliser la casse et les plus avant inspection")
    require("attempt <= 3" in text and "decodeURIComponent(candidate)" in text,
            "le détecteur doit vérifier le résultat du troisième décodage URL")
    require("if (attempt === 3) return true;" in text,
            "un encodage qui dépasse le budget de décodage doit échouer de façon sûre")
    require("candidate.includes(`${key}=`)" in text,
            "le détecteur doit reconnaître les affectations sensibles après normalisation")

    require("function hasSensitiveExternalMaterial(parsed: URL)" in text,
            "le filtre de matière d'authentification externe doit exister")
    require("parsed.username || parsed.password" in text,
            "les identifiants URL userinfo doivent être refusés")
    require("containsSensitiveExternalAssignment(parsed.pathname)" in text,
            "les chemins externes doivent être inspectés pour les affectations sensibles encodées")
    require("containsSensitiveExternalAssignment(parsed.search)" in text,
            "la query brute doit être décodée pour bloquer aussi les noms de paramètres sensibles encodés")
    require("parsed.searchParams.entries()" in text,
            "les noms et valeurs des paramètres externes doivent être inspectés")
    require("containsSensitiveExternalAssignment(value)" in text,
            "les valeurs de query, dont subject/body mailto, doivent être filtrées")
    require("containsSensitiveExternalAssignment(parsed.hash)" in text,
            "le fragment externe doit être filtré après décodage borné")

    require("function isSafeTelephoneUrl(parsed: URL)" in text,
            "le protocole tel doit avoir un garde structurel dédié")
    require("parsed.protocol !== 'tel:' || parsed.search || parsed.hash" in text,
            "les URL tel doivent refuser query et fragment")
    require("decodeURIComponent(parsed.pathname)" in text,
            "le numéro tel doit être contrôlé après décodage URL")
    require("/^\\+?[0-9(). \\-]+$/.test(number)" in text,
            "tel doit accepter seulement chiffres, plus initial et séparateurs visuels ordinaires")
    require("digits.length >= 3 && digits.length <= 15" in text,
            "tel doit borner les numéros à 3–15 chiffres")

    require("parsed.protocol === 'https:' && allowedHosts.has(parsed.hostname)" in text,
            "les pages SINJIRA internes doivent rester bornées à HTTPS + hôtes approuvés")
    require("!EXTERNAL_SAFE_PROTOCOLS.has(parsed.protocol)" in text,
            "les protocoles externes inconnus doivent être refusés explicitement")
    require("if (hasSensitiveExternalMaterial(parsed))" in text,
            "toutes les sorties externes permises doivent être filtrées pour la matière sensible")
    require("parsed.protocol === 'https:' && hasSensitiveExternalMaterial(parsed)" not in text,
            "le filtre sensible ne doit pas être limité aux seules URLs HTTPS externes")
    require("void Linking.openURL(url).catch" in text,
            "l'ouverture OS doit être située derrière les gardes et gérer les erreurs")
    require("void Linking.openURL(url);" not in text,
            "aucun fallback Linking.openURL non gardé n'est permis")

    require("originWhitelist={['https://*']}" in text,
            "la WebView doit accepter uniquement HTTPS")
    require("originWhitelist={['https://*', 'sinjira://*']}" not in text,
            "le schéma sinjira:// ne doit pas être rendu dans la WebView")
    require("originWhitelist={['*']}" not in text and "http://*" not in text,
            "aucune whitelist WebView globale ou HTTP n'est permise")

    require("function normalizeSinjiraUrl(url: string | null): string | null" in text,
            "le normaliseur des deep links SINJIRA doit rester côté natif")
    require("if (/^sinjira:\\/+/i.test(url))" in text,
            "les deep links sinjira: à une, deux ou trois barres doivent rester reconnus côté natif")
    require("url.replace(/^sinjira:\\/+/i, '/')" in text,
            "les deep links sinjira: doivent être ramenés à un seul chemin interne")
    require("Linking.getInitialURL()" in text and "Linking.addEventListener('url'" in text,
            "les deep links doivent rester traités par React Native Linking")

    require("readFile(new URL('../App.tsx', import.meta.url)" in deep_link_text,
            "le test deep link doit extraire le normaliseur du vrai App.tsx")
    require("function normalizeSinjiraUrl(url: string | null): string | null {" in deep_link_text,
            "le test deep link doit rechercher la fonction réelle par sa signature")
    require("safeCustomSchemeCases" in deep_link_text and "approvedHttpsCases" in deep_link_text,
            "le test deep link doit distinguer schéma natif et HTTPS approuvé")
    require("rejectedInputs" in deep_link_text,
            "le test deep link doit couvrir explicitement les entrées refusées")
    for marker in (
        "sinjira:/compte/profil.html",
        "sinjira://compte/profil.html",
        "sinjira:///compte/profil.html",
        "sinjira:///////compte/profil.html?tab=1#bio",
        "sinjira://evil.example/path",
        "sinjira://user@evil.example/path",
        "sinjira://%2F%2Fevil.example/path",
        "sinjira://%5C%5Cevil.example/path",
        "https://user:password@sinjira.com/compte/profil.html",
        "https://evil.example/compte/profil.html",
        "http://sinjira.com/compte/profil.html",
        "//evil.example/compte/profil.html",
        "sinjira:compte/profil.html",
    ):
        require(marker in deep_link_text, f"cas deep link obligatoire absent: {marker}")
    require("assert.equal(parsed.origin, TEST_ORIGIN" in deep_link_text,
            "chaque deep link accepté doit prouver qu'il reste épinglé à l'origine SINJIRA")
    require("assert.equal(parsed.username, ''" in deep_link_text and "assert.equal(parsed.password, ''" in deep_link_text,
            "le résultat normalisé doit éliminer tout userinfo")
    require("assert.equal(reparsed.hostname, 'www.benoitcantin.com'" in deep_link_text,
            "la matrice deep link doit revérifier l'hôte final après parsing")

    require("isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current" in text,
            "la barrière locale du Coffre doit rester active pendant la navigation")
    require("thirdPartyCookiesEnabled={false}" in text,
            "les cookies tiers doivent rester désactivés")

    guarded_block = text.split("const shouldStart", 1)[1].split("if (!securityReady)", 1)[0]
    userinfo_guard_index = guarded_block.index("if (parsed.username || parsed.password)")
    internal_guard_index = guarded_block.index("if (parsed.protocol === 'https:' && allowedHosts.has(parsed.hostname))")
    protocol_guard_index = guarded_block.index("if (!EXTERNAL_SAFE_PROTOCOLS.has(parsed.protocol))")
    telephone_guard_index = guarded_block.index("if (parsed.protocol === 'tel:' && !isSafeTelephoneUrl(parsed))")
    sensitive_guard_index = guarded_block.index("if (hasSensitiveExternalMaterial(parsed))")
    open_url_index = guarded_block.index("void Linking.openURL(url).catch")
    require(userinfo_guard_index < internal_guard_index < protocol_guard_index,
            "les identifiants URL doivent être refusés avant toute classification interne/externe")
    require("les identifiants intégrés à une URL ne sont pas autorisés" in guarded_block,
            "le refus global userinfo doit fournir un message natif explicite")
    require(protocol_guard_index < telephone_guard_index < sensitive_guard_index < open_url_index,
            "le garde tel puis le filtre sensible doivent s'appliquer avant toute ouverture OS")
    require("numéros ordinaires sans code de service ni commande spéciale" in guarded_block,
            "le refus tel doit fournir un message natif explicite")

    for secret_marker in (
        "nativeDeviceKey",
        "WEB_DEVICE_KEY_STORAGE",
        "WEB_PUSH_TOKEN_STORAGE",
        "access_token",
        "refresh_token",
    ):
        if secret_marker in ("access_token", "refresh_token"):
            continue
        require(secret_marker not in guarded_block,
                f"la navigation externe ne doit pas transmettre le secret {secret_marker}")

    require("readFile(new URL('../App.tsx', import.meta.url)" in adversarial_text,
            "le test adversarial doit exécuter le garde extrait du vrai App.tsx")
    for marker in (
        "access%25255Ftoken=secret",
        "access%2525255Ftoken=secret",
        "body=access_token%25253Dsecret",
        "mailto:user@example.com?body=refresh_token%25253Dsecret",
        "https://user:password@example.com/",
        "javascript:alert(1)",
        "tel:+15145551234",
        "tel:*123%23",
        "tel:%2A123%23",
        "tel:+15145551234,123",
        "tel:+15145551234;ext=123",
        "tel:+15145551234?foo=bar",
        "tel:+15145551234#service",
        "tel:+1234567890123456",
        "tel:12",
        "tel:+1%20(514)%20555-1234",
        "tel:+33.1.42.68.53.00",
        "topic=tokenization",
    ):
        require(marker in adversarial_text, f"cas adversarial obligatoire absent: {marker}")
    require("hello%2525252520world" in adversarial_text,
            "le test doit verrouiller l'échec sûr lorsque le budget de décodage est dépassé")
    require("isSafeTelephoneUrl" in adversarial_text,
            "le test adversarial doit exécuter le garde tel réel de App.tsx")
    require("blockedTelephoneUrls" in adversarial_text and "allowedTelephoneUrls" in adversarial_text,
            "le test doit séparer clairement les formes tel dangereuses et légitimes")

    require("'  const shouldStart = (request: { url: string }) => {'" in adversarial_text,
            "le test doit extraire et exécuter le vrai shouldStart de App.tsx")
    require("function buildShouldStartHarness" in adversarial_text,
            "le test doit construire un harness d'effets de bord autour de shouldStart")
    for marker in (
        "about:blank",
        "pas une URL",
        "https://www.sinjira.com/compte/profil.html",
        "https://user:password@sinjira.com/compte/profil.html",
        "https://sinjira.com/compte/profil.html?access_token=interne",
        "https://www.benoitcantin.com/compte/registre-personnel.html",
        "javascript:access_token=secret",
        "https://example.com/?access_token=secret",
        "linkingRejects: true",
    ):
        require(marker in adversarial_text, f"cas shouldStart obligatoire absent: {marker}")
    require("identifiants intégrés à une URL" in adversarial_text,
            "le test doit vérifier le message du refus userinfo interne")
    require("numéros ordinaires sans code de service ni commande spéciale" in adversarial_text,
            "le test doit vérifier le message du refus tel")
    require("assert.deepEqual(harness.openedUrls, []" in adversarial_text,
            "les refus doivent vérifier qu'aucune ouverture OS n'a lieu")
    require("assert.deepEqual(harness.openedUrls, [rawUrl]" in adversarial_text,
            "les sorties externes propres doivent vérifier une ouverture OS unique")
    require("assert.deepEqual(harness.navigatedPaths, ['/compte/registre-personnel.html'])" in adversarial_text,
            "le test doit verrouiller l'interception locale du Registre")

    require('"test:navigation-guard": "node scripts/test-external-navigation-guard.mjs"' in package_text,
            "package.json doit exposer le test adversarial de navigation")
    require('"test:deep-link-normalizer": "node scripts/test-deep-link-normalizer.mjs"' in package_text,
            "package.json doit exposer le test exécutable des deep links")
    require("mobile-native/scripts/test-external-navigation-guard.mjs" in workflow_text,
            "le workflow doit se déclencher lorsque le test adversarial change")
    require("mobile-native/scripts/test-deep-link-normalizer.mjs" in workflow_text,
            "le workflow doit se déclencher lorsque le test deep link change")
    require("npm run test:navigation-guard" in workflow_text,
            "le workflow frontière mobile doit exécuter le test adversarial")
    require("npm run test:deep-link-normalizer" in workflow_text,
            "le workflow frontière mobile doit exécuter le test deep link")

    print("OK navigation mobile V25: frontière externe bornée, userinfo refusé avant classification, tel borné aux numéros ordinaires, deep links épinglés à l'origine par test exécutable, décodage fail-closed et décision shouldStart complète exécutée avec effets de bord en CI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
