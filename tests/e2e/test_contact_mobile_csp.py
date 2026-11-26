#!/usr/bin/env python3
"""Contact SINJIRA — ergonomie tactile et verrou de confidentialité fail-closed.

Exécution locale sur Chromium, Firefox et WebKit, sans endpoint de données.
"""
from __future__ import annotations

import os
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

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
    assert 'href="/assets/css/contact-ux-v1.css?v=1.0.1"' in html
    assert 'aria-labelledby="contact-channel-title"' in html
    assert '<h2 id="contact-channel-title">Choisir le bon contact</h2>' in html
    assert html.index('name="viewport"') < html.index("sinjira-nav-boot-v2.js")
    assert html.count("site.js?v=24.4.105") == 1
    assert "onsubmit=" not in html and "onclick=" not in html
    assert "<script>(" not in html and "style=" not in html
    assert "var PERSONAL_ENDPOINT=''" in js
    assert "fields.disabled=true" in js and "event.preventDefault()" in js
    assert "form.getAttribute('data-personal-formspree-state')==='active-separate-endpoint'" in js
    assert "@media(max-width:640px)" in css
    assert 'class="contact-channel-list" role="list"' in html
    assert ".contact-channel-list .btn" in css and "min-height: 48px;" in css
    assert "/projets/projet-nova/contact.html" in html
    assert "/compte/vie-privee.html" in html
    print("OK: contrat statique CSP, destinations et verrou de confidentialité")


def verify(context, width: int, js_enabled: bool) -> None:
    page = context.new_page()
    try:
        response = page.goto(BASE + "/contact.html", wait_until="domcontentloaded", timeout=30_000)
        assert response and response.status == 200, (BROWSER, width, "contact inaccessible")
        if js_enabled:
            assert response.headers.get("content-security-policy") == STRICT_CSP
        # Vérifier le DOM et l'arbre accessible avec une attente bornée.
        # count() seul peut lire l'arbre avant sa mise à jour dans Firefox.
        expect(page.locator("body.contact-ux-page")).to_have_count(1, timeout=5000)
        title = page.locator("#contact-channel-title")
        expect(title).to_be_visible(timeout=5000)
        expect(title).to_have_text("Choisir le bon contact", timeout=5000)
        heading = page.get_by_role("heading", name="Choisir le bon contact", exact=True)
        expect(heading).to_have_count(1, timeout=5000)
        expect(heading).to_be_visible(timeout=5000)
        channels = page.get_by_role("list", name="Démarches de contact disponibles")
        expect(channels).to_have_count(1, timeout=5000)
        expect(channels.get_by_role("listitem")).to_have_count(3, timeout=5000)
        destinations = channels.locator(":scope > li > a")
        expect(destinations).to_have_count(3, timeout=5000)
        assert page.locator('.contact-channel-list > li > a[href="mailto:sinjiraofficiel@gmail.com"]').count() == 1
        assert page.locator('.contact-channel-list > li > a[href="/compte/vie-privee.html"]').count() == 1
        assert page.locator('.contact-channel-list > li > a[href="/projets/projet-nova/contact.html"]').count() == 1

        assert destinations.nth(0).get_attribute("href") == "mailto:sinjiraofficiel@gmail.com"
        assert destinations.nth(1).get_attribute("href") == "/compte/vie-privee.html"
        assert destinations.nth(2).get_attribute("href") == "/projets/projet-nova/contact.html"
        assert page.locator('main#contenu[tabindex="-1"]').count() == 1
        assert page.locator('.footer-col a[href="/contact.html"][aria-current="page"]').count() == 1
        assert page.get_by_text("Si votre application de messagerie ne s’ouvre pas", exact=False).is_visible()
        preview = page.locator("#contact-preview")
        assert preview.count() == 1 and preview.get_attribute("open") is None
        summary = preview.locator("summary")
        for item, minimum in [(summary, 44)] + [(link, 48) for link in destinations.all()]:
            b = item.bounding_box()
            assert b, (BROWSER, width, "élément non affiché")
            assert b["height"] >= minimum, (BROWSER, width, "cible trop petite", b)
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
