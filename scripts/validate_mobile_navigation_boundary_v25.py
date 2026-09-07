#!/usr/bin/env python3
"""Valide le contrat V25 de navigation de l'application mobile native SINJIRA."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "mobile-native" / "App.tsx"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ERREUR navigation mobile V25: {message}")


def main() -> int:
    text = APP.read_text(encoding="utf-8")

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
    require("attempt < 3" in text and "decodeURIComponent(candidate)" in text,
            "le détecteur doit décoder de façon bornée les valeurs URL imbriquées")
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

    require("isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current" in text,
            "la barrière locale du Coffre doit rester active pendant la navigation")
    require("thirdPartyCookiesEnabled={false}" in text,
            "les cookies tiers doivent rester désactivés")

    guarded_block = text.split("const shouldStart", 1)[1].split("if (!securityReady)", 1)[0]
    protocol_guard_index = guarded_block.index("if (!EXTERNAL_SAFE_PROTOCOLS.has(parsed.protocol))")
    sensitive_guard_index = guarded_block.index("if (hasSensitiveExternalMaterial(parsed))")
    open_url_index = guarded_block.index("void Linking.openURL(url).catch")
    require(protocol_guard_index < sensitive_guard_index < open_url_index,
            "le filtre sensible doit s'appliquer après l'allowlist de protocoles et avant toute ouverture OS")

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

    print("OK navigation mobile V25: WebView HTTPS SINJIRA bornée, schémas externes arbitraires refusés, liens sinjira normalisés et matière sensible encodée bloquée dans chemins, query brute, valeurs de query et fragments externes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
