"""Tests Playwright du refus sécurisé après téléchargement Nova figé.

Réseau simulé uniquement dans une page éphémère. La minuterie de 15 secondes
est ramenée à 120 ms dans cette page, sans modifier la production.
"""
import json


def check_stalled_fetch(browser, url, resource, mode, label):
    assert mode in ("results", "survey"), mode
    page = browser.new_page(
        locale="fr-CA", viewport={"width": 390, "height": 844},
        reduced_motion="reduce",
    )
    requests = []
    page.on("request", lambda request: requests.append(request.url)
            if request.method == "POST" else None)
    script = r"""(() => {
      const blockedName = BLOCKED_RESOURCE;
      const originalFetch = window.fetch.bind(window);
      const realTimeout = window.setTimeout.bind(window);
      window.__novaStalledCalls = 0;
      window.__novaObservedAbort = false;
      window.setTimeout = (fn, duration, ...args) =>
        realTimeout(fn, duration === 15000 ? 120 : duration, ...args);
      window.fetch = (resource, options = {}) => {
        const address = typeof resource === 'string' ? resource : resource.url;
        const path = new URL(address, document.baseURI).pathname;
        if (!path.endsWith('/' + blockedName)) {
          return originalFetch(resource, options);
        }
        window.__novaStalledCalls += 1;
        return new Promise((resolve, reject) => {
          if (!options.signal) {
            // Sans AbortSignal : la page reste bloquée. Le test expirera.
            return;
          }
          if (options.signal.aborted) {
            window.__novaObservedAbort = true;
            reject(new DOMException('Interrupted', 'AbortError'));
            return;
          }
          options.signal.addEventListener('abort', () => {
            window.__novaObservedAbort = true;
            reject(new DOMException('Interrupted', 'AbortError'));
          }, {once:true});
        });
      };
    })();""".replace("BLOCKED_RESOURCE", json.dumps(resource))
    try:
        page.add_init_script(script=script)
        response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        assert response is not None and response.status == 200, (
            label + " : document de test indisponible"
        )
        if mode == "results":
            page.wait_for_function(
                """() => document.querySelector('#results-state')?.textContent
                   .includes('indisponibles ou non validées')""",
                timeout=8_000,
            )
            assert page.locator("#results-question-list li").count() == 1, label
            assert page.locator(".nova-results-bar-item").count() == 0, label
            page.locator("#results-show-64").click()
            assert "indisponibles" in page.locator("#results-state").inner_text(), label
            assert page.locator(".nova-results-bar-item").count() == 0, label
        else:
            page.locator("#sondage-introduction [role=alert]").wait_for(
                state="visible", timeout=8_000,
            )
            page.locator("#sondage-age").check()
            page.locator("#sondage-consent").check()
            assert page.locator("#sondage-start").is_disabled(), label
            assert page.locator("#sondage-questionnaire").is_hidden(), label
        assert page.evaluate(
            "() => window.__novaStalledCalls === 1 && window.__novaObservedAbort"
        ), label + " : aucune annulation réseau observée"
        assert requests == [], label + " : POST alors que la collecte est fermée"
    finally:
        page.close()
