#!/usr/bin/env python3
"""Contact SINJIRA — ergonomie tactile et verrou de confidentialité fail-closed.

Exécution locale sur Chromium, Firefox et WebKit, sans endpoint de données.
"""
from __future__ import annotations

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173").rstrip("/")
BROWSER = os.environ.get("BROWSER", "chromium")
WIDTHS = (240, 320, 390, 768, 1440)
STRICT_CSP = (
    "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'"
)


def static_contracts() -> None:
    html = (ROOT / "contact.html").read_text("utf-8")
    js = (ROOT / "assets/js/sinjira-contact-route-v1.js").read_text("utf-8")
    css = (ROOT / "assets/css/contact-ux-v1.css").read_text("utf-8")
    assert "<details class=\"contact-form-preview\"" in html
    assert "Afficher l’aperçu du formulaire personnel" in html
    assert 'data-personal-formspree-state="pending-separate-endpoint"' in html
    assert 'src="/assets/js/sinjira-contact-route-v1.js?v=1.0.0"' in html
    assert 'href="/assets/css/contact-ux-v1.css?v=1.0.0"' in html
    assert "onsubmit=" not in html and "onclick=" not in html
    assert "<script>(" not in html and "style=" not in html
    assert "var PERSONAL_ENDPOINT=''" in js
    assert "fields.disabled=true" in js and "event.preventDefault()" in js
    assert "form.getAttribute('data-personal-formspree-state')==='active-separate-endpoint'" in js
    assert "@media(max-width:640px)" in css
    assert "/projets/projet-nova/contact.html" in html
    assert "/compte/vie-privee.html" in html
    print("OK: contrat statique CSP, destinations et verrou de confidentialité")


def verify(context, width: int, js_enabled: bool) -> None:
    page = context.new_page()
    try:
        response = page.goto(BASE + "/contact.html", wait_until="domcontentloaded", timeout=30_000)
        assert response and response.status == 200, (BROWSER, width, "contact inaccessible")
        assert page.locator("body.contact-ux-page").count() == 1
        assert page.get_by_role("heading", name="Choisir le bon contact").count() == 1
        destinations = page.locator(".contact-route-actions a")
        assert destinations.count() == 3, (BROWSER, width, "trois parcours attendus")
        assert page.locator('.contact-route-actions a[href="mailto:sinjiraofficiel@gmail.com"]').count() == 1
        assert page.locator('.contact-route-actions a[href="/compte/vie-privee.html"]').count() == 1
        assert page.locator('.contact-route-actions a[href="/projets/projet-nova/contact.html"]').count() == 1

        preview = page.locator("#contact-preview")
        assert preview.count() == 1 and preview.get_attribute("open") is None
        summary = preview.locator("summary")
        for item in [summary] + destinations.all():
            b = item.bounding_box()
            assert b, (BROWSER, width, "élément non affiché")
            assert b["height"] >= 44, (BROWSER, width, "cible trop petite", b)
            assert b["x"] >= -2 and b["x"] + b["width"] <= width + 2, (
                BROWSER, width, "débordement tactile", b
            )

        # Contrôler l'ouverture native par clavier (pas de dépendance JS).
        summary.focus()
        page.keyboard.press("Enter")
        assert preview.get_attribute("open") is not None, (BROWSER, width, "aperçu non ouvert")
        form = page.locator("#contact-general")
        fields = page.locator("#contact-personal-fields")
        assert fields.get_attribute("disabled") is not None
        assert form.get_attribute("action") is None and form.get_attribute("method") is None
        assert form.get_attribute("data-personal-formspree-state") == "pending-separate-endpoint"
        assert page.locator("#contact-submit").is_disabled()
        for selector in (
            "#contact-name", "#contact-email", "#contact-project", "#contact-message",
            'input[name="consentement_contact"]',
        ):
            assert page.locator(selector).is_disabled(), (BROWSER, width, selector)
        assert page.evaluate(
            'new FormData(document.querySelector("#contact-general")).entries().next().done'
        ), (BROWSER, width, "données exposées")
        assert "désactivé" in page.locator("#contact-route").inner_text().lower()

        if js_enabled:
            # Le double verrou JS annule la soumission programmée.
            blocked = page.evaluate("""() => {
                const f = document.querySelector('#contact-general');
                const e = new Event('submit', {bubbles: true, cancelable: true});
                return f.dispatchEvent(e) === false && e.defaultPrevented;
            }""")
            assert blocked, (BROWSER, width, "soumission non bloquée")
        summary.click()
        assert preview.get_attribute("open") is None, (BROWSER, width, "aperçu non repliable")
        print(f"OK {BROWSER}: {width}px, JS={'actif+CSP' if js_enabled else 'désactivé'}")
    finally:
        page.close()


def main() -> None:
    if BROWSER not in ("chromium", "firefox", "webkit"):
        raise ValueError("Moteur non autorisé")
    static_contracts()
    html = (ROOT / "contact.html").read_text("utf-8")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        try:
            for js_enabled in (False, True):
                for width in WIDTHS:
                    context = browser.new_context(
                        viewport={"width": width, "height": 760},
                        java_script_enabled=js_enabled,
                        reduced_motion="reduce",
                        service_workers="block",
                    )
                    try:
                        if js_enabled:
                            context.route(
                                "**/contact.html",
                                lambda route: route.fulfill(
                                    status=200,
                                    body=html,
                                    headers={
                                        "content-type": "text/html; charset=utf-8",
                                        "content-security-policy": STRICT_CSP,
                                    },
                                ),
                            )
                        verify(context, width, js_enabled)
                    finally:
                        context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
