#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ERREUR compatibilité navigateur: {message}")


def main() -> None:
    site_js = read("assets/js/site.js")
    compat_css = read("assets/css/browser-compat-v24-4-22.css")
    workflow = read(".github/workflows/e2e-site.yml")
    e2e = read("tests/e2e/test_public_site.py")
    support_doc = read("BROWSER_SUPPORT.md")

    # Le noyau public doit rester parsable par des moteurs plus anciens.
    forbidden_syntax = {
        "optional chaining": "?.",
        "nullish coalescing": "??",
        "arrow functions": "=>",
        "const declarations": "const ",
        "let declarations": "let ",
    }
    for label, marker in forbidden_syntax.items():
        require(marker not in site_js, f"site.js utilise encore {label} ({marker})")

    require("browser-compat-v24-4-22.css?v=24.4.22" in site_js, "site.js ne charge pas la couche CSS V24.4.22")
    require("supportsModules" in site_js and "sinjira-legacy-browser" in site_js, "fallback sans ES Modules absent")
    require("RUNTIME_VERSION = '24.4.22'" in site_js, "version runtime publique non alignée")

    css_markers = [
        "-webkit-text-size-adjust",
        "text-size-adjust",
        "-webkit-mask-image",
        "-webkit-backdrop-filter",
        "@supports not ((backdrop-filter",
        "min-height: 100vh",
        "min-height: 100svh",
        "env(safe-area-inset-left)",
        "prefers-reduced-motion",
    ]
    for marker in css_markers:
        require(marker in compat_css, f"fallback CSS absent: {marker}")

    # Les trois moteurs de rendu majeurs doivent être testés, pas seulement Chromium.
    for browser in ("chromium", "firefox", "webkit"):
        require(browser in workflow, f"workflow E2E sans {browser}")
    require("matrix:" in workflow and "browser:" in workflow, "tests multi-navigateurs non matricés")
    require("playwright install --with-deps" in workflow, "installation Playwright multi-moteurs absente")
    require("BROWSER: ${{ matrix.browser }}" in workflow, "moteur non transmis au test E2E")

    e2e_markers = [
        'BROWSER_NAME = os.environ.get("BROWSER"',
        'SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}',
        "browser_type = getattr(p, BROWSER_NAME)",
        "has_touch=True",
        "scrollWidth <= Math.ceil(window.innerWidth) + 2",
        "browser-compat-v24-4-22.css",
        'runtime_version == "24.4.22"',
    ]
    for marker in e2e_markers:
        require(marker in e2e, f"contrat E2E incomplet: {marker}")

    require("Chromium" in support_doc and "Firefox" in support_doc and "WebKit" in support_doc, "politique de support navigateur incomplète")
    require("progressive enhancement" in support_doc.lower(), "stratégie de dégradation progressive non documentée")

    print("OK compatibilité navigateur V24.4.22: noyau public, fallbacks CSS et matrice Chromium/Firefox/WebKit validés")


if __name__ == "__main__":
    main()
