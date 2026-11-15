#!/usr/bin/env python3
"""Parcours public de la Boussole NOVA : navigateur réel, aucune écriture.

Ce test ne transmet jamais de bulletin politique et n'ouvre aucune collecte.
Il vérifie le domaine public, contrairement aux tests E2E locaux du dépôt.
La vue « mobile » est un viewport émulé, pas un appareil physique certifié.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets" / "projet-nova"
RECEIPT = ROOT / "docs/nova-sondages/reception-sondage-boussole-2026-11-08.json"
ORIGIN = "https://www.benoitcantin.com"
COMPASS_URL = ORIGIN + "/projets/projet-nova/boussole-electorale.html"
BROWSERS = ("chromium", "firefox", "webkit")


def expectation():
    matrix = json.loads(RECEIPT.read_text(encoding="utf-8"))
    source = (NOVA / "boussole-electorale.html").read_text(encoding="utf-8")
    import re

    references = re.findall(
        r'<script\b[^>]*\bsrc="(assets/boussole-electorale\.js\?v=[^"]+)"', source
    )
    if len(references) != 1:
        raise ValueError("Version du script boussole absente ou dupliquée")
    compass = matrix["compass"]
    validated = sum(g["status"] == "PASSED" for g in compass["gates"])
    total = len(compass["gates"])
    if validated != matrix["summary"]["compass"]["passed"] or total != matrix["summary"]["compass"]["total"]:
        raise ValueError("Incohérence des chiffres de réception")
    return {
        "script": references[0],
        "receipt": f"{validated} critères sur {total} validés",
        "percent": f"{100 * validated / total:.1f}".replace(".", ",") + " %",
        "poll_closed": matrix["poll"]["published_in_source"] is False and
                       matrix["decision"]["opening_poll_approved"] is False,
    }


def self_test():
    x = expectation()
    assert x["script"].startswith("assets/boussole-electorale.js?v=")
    assert x["poll_closed"]
    assert "critères sur 12 validés" in x["receipt"]
    assert x["percent"].endswith("%")
    for name in BROWSERS:
        assert name.islower()
    assert urlparse(COMPASS_URL).hostname == "www.benoitcantin.com"
    print("OK : paramètres de réception et URL publique cohérents, sans réseau.")


JOURNEY = r"""() => {
    const byId = id => document.getElementById(id);
    const stage = () => byId("compass-question-stage")?.querySelector("fieldset");
    const failures = [];
    const check = (condition, label) => { if (!condition) failures.push(label); };
    const choose = (value, weight = "normal") => {
      const input = stage()?.querySelector('input[type="radio"][value="' + value + '"]');
      const select = stage()?.querySelector("[data-importance]");
      if (!input || !select) return false;
      select.value = weight;
      select.dispatchEvent(new Event("change", {bubbles:true}));
      input.click();
      return true;
    };
    byId("compass-reset")?.click();
    byId("compass-start")?.click();
    check(stage()?.dataset.questionId === "q01", "première question");
    check(choose("3", "forte"), "première réponse");
    byId("compass-preview")?.click();
    const first = [...document.querySelectorAll("#compass-results-grid .compass-result-card")];
    check(first.length === 16 && first.every(card =>
      card.querySelector("strong")?.textContent.trim() === "—" &&
      !card.querySelector(".compass-axis-track i")), "absence de score après une réponse");
    byId("compass-next")?.click();
    check(stage()?.dataset.questionId === "q02", "deuxième question");
    check(choose("3", "faible"), "deuxième réponse");
    byId("compass-preview")?.click();
    const second = [...document.querySelectorAll("#compass-results-grid .compass-result-card")];
    const calculated = second.filter(card => card.querySelector(".compass-axis-track i"));
    check(second.length === 16 && calculated.length === 1 &&
      calculated[0]?.querySelector("strong")?.textContent.trim() === "+50",
      "un score pondéré +50, quinze dimensions sans score");
    check(byId("compass-summary")?.textContent.includes("Profil partiel"),
      "profil partiel explicite");
    const importance = stage()?.querySelector("[data-importance]");
    if (importance) {
      importance.value = "forte";
      importance.dispatchEvent(new Event("change", {bubbles:true}));
    }
    check(document.querySelector("#compass-results-grid .compass-result-card strong")
      ?.textContent.trim() === "0", "score actualisé à zéro");
    byId("compass-prev")?.click();
    check(stage()?.dataset.questionId === "q01", "retour à Q01");
    check(choose("skip"), "Sans opinion");
    check(document.querySelector("#compass-results-grid .compass-result-card strong")
      ?.textContent.trim() === "—", "aucun score fabriqué après un saut");
    byId("compass-reset")?.click();
    check(byId("compass-results")?.hidden &&
      !byId("compass-start-panel")?.hidden, "remise à zéro des résultats");
    byId("compass-start")?.click();
    let completed = 0;
    for (let index = 1; index <= 64; index++) {
      if (stage()?.dataset.questionId !== "q" + String(index).padStart(2, "0")) {
        failures.push("séquence interrompue à Q" + index);
        break;
      }
      if (!choose("skip")) {
        failures.push("option Sans opinion absente à Q" + index);
        break;
      }
      byId("compass-next")?.click();
      completed++;
    }
    const cards = [...document.querySelectorAll("#compass-results-grid .compass-result-card")];
    check(completed === 64 && !byId("compass-results")?.hidden, "64 étapes terminées");
    check(cards.length === 16 && cards.every(card =>
      card.querySelector("strong")?.textContent.trim() === "—"), "aucun score artificiel final");
    check(!byId("compass-radar")?.querySelector("polygon"), "pas de polygone artificiel");
    byId("compass-reset")?.click();
    check(byId("compass-results")?.hidden &&
      !byId("compass-start-panel")?.hidden, "remise à zéro finale");
    return {ok:failures.length===0,failures,completed,dimensions:cards.length};
}"""


def run(browser_name: str):
    if browser_name not in BROWSERS:
        raise ValueError("Navigateur inconnu : " + browser_name)
    expected = expectation()
    if not expected["poll_closed"]:
        raise ValueError("Sondage non confirmé fermé dans la source")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = getattr(playwright, browser_name).launch()
        try:
            for mode, viewport in (
                ("desktop", {"width": 1440, "height": 1000}),
                ("mobile_emule", {"width": 390, "height": 844}),
            ):
                context = browser.new_context(
                    locale="fr-CA", viewport=viewport,
                    reduced_motion="reduce", service_workers="block",
                )
                page = context.new_page()
                forbidden = []
                external_after_start = []
                observing = [False]

                def handle_route(route):
                    request = route.request
                    if request.method != "GET":
                        forbidden.append({"method": request.method, "url": request.url[:180]})
                        route.abort()
                    else:
                        route.continue_()

                def observe_request(request):
                    hostname = urlparse(request.url).hostname
                    if observing[0] and hostname not in ("www.benoitcantin.com", None):
                        external_after_start.append({
                            "method": request.method, "url": request.url[:180]
                        })

                page.route("**/*", handle_route)
                page.on("request", observe_request)
                response = page.goto(COMPASS_URL, wait_until="domcontentloaded", timeout=30000)
                if response is None or response.status != 200:
                    raise AssertionError("Page publique indisponible")
                page.wait_for_function(
                    """() => !!document.getElementById('compass-start') &&
                       !document.getElementById('compass-start').disabled &&
                       !!document.getElementById('compass-preview')""",
                    timeout=15000,
                )
                observed = page.evaluate("""() => ({
                    script:[...document.scripts].map(x=>x.getAttribute('src')||'')
                        .find(x=>x.startsWith('assets/boussole-electorale.js?')),
                    status:document.querySelector('.civic-reception-status')?.textContent.trim()||''
                })""")
                if observed["script"] != expected["script"]:
                    raise AssertionError("Script live périmé : " + str(observed["script"]))
                if expected["receipt"] not in observed["status"] or expected["percent"] not in observed["status"]:
                    raise AssertionError("Réception publique périmée : " + observed["status"])
                observing[0] = True
                journey = page.evaluate(JOURNEY)
                observing[0] = False
                if not journey["ok"]:
                    raise AssertionError("Parcours public défaillant : " + str(journey))
                if forbidden or external_after_start:
                    raise AssertionError("Transfert réseau pendant les réponses : " +
                                         str(forbidden + external_after_start))
                page.reload(wait_until="domcontentloaded", timeout=30000)
                page.wait_for_function(
                    """() => !!document.getElementById('compass-start') &&
                       !document.getElementById('compass-start').disabled""",
                    timeout=15000,
                )
                if expected["script"] not in page.content():
                    raise AssertionError("Script versionné différent après rechargement/cache")
                if not page.locator("#compass-results").is_hidden():
                    raise AssertionError("Les réponses locales ont survécu au rechargement")
                print(json.dumps({
                    "browser": browser_name, "view": mode, "ok": True,
                    "script": expected["script"], "completed": journey["completed"],
                    "dimensions": journey["dimensions"], "blocked_writes": len(forbidden),
                    "external_requests_during_answers": len(external_after_start),
                    "cache_reload": "passed",
                }, ensure_ascii=False))
                context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--browser", default=os.environ.get("BROWSER", "chromium"))
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        run(args.browser)
