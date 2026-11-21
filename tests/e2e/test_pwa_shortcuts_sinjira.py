#!/usr/bin/env python3
"""Raccourcis d'installation SINJIRA (Android/PC) — liens publics et cohérence.

La liste des raccourcis est exposée par le navigateur; son rendu dans le
lanceur du système doit encore être vérifié sur de vrais appareils.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse, urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173").rstrip("/") + "/"
ENGINE = os.environ.get("BROWSER", "chromium").lower()
WIDTHS = (240, 320, 390, 768, 1440)
EXPECTED = (
    "/projets/sinjira/",
    "/app/",
    "/projets/sinjira/romans/",
    "/projets/sinjira/registre/",
    "/projets/sinjira/communaute/",
    "/projets/sinjira/monde-parallele/",
)


def verify_static_manifest() -> dict:
    canonical = (ROOT / "manifest.webmanifest").read_bytes()
    legacy = (ROOT / "site.webmanifest").read_bytes()
    assert canonical == legacy, "les deux manifestes divergent (octet pour octet)"
    data = json.loads(canonical.decode("utf-8"))
    assert data["id"] == "/projets/sinjira/"
    assert data["start_url"] == "/app/"
    assert data["scope"] == "/"
    assert "SINJIRA" in data["name"]
    assert [entry["url"] for entry in data["shortcuts"]] == list(EXPECTED)
    assert len(set(EXPECTED)) == len(EXPECTED)
    for entry in data["shortcuts"]:
        assert entry["name"].strip() and entry["short_name"].strip()
        assert "démo" not in entry["name"].lower()
        assert "demo" not in entry["name"].lower()
        parsed = urlparse(entry["url"])
        assert parsed.path == entry["url"] and not parsed.scheme and not parsed.netloc
        assert "projet-nova" not in entry["url"]
        assert not entry["url"].startswith(("/compte/", "/admin/", "/supabase/"))
        target = ROOT / entry["url"].lstrip("/") / "index.html"
        assert target.is_file(), f"lien de raccourci introuvable : {entry['url']}"
        assert all(icon.get("src") == "/android-chrome-192x192.png" for icon in entry["icons"])
    for icon in data["icons"]:
        assert (ROOT / icon["src"].lstrip("/")).is_file()
    print("OK : manifestes identiques, démo retirée et 6 destinations SINJIRA valides")
    return data


def verify_browser(browser, expected: dict) -> None:
    for width in WIDTHS:
        ctx = browser.new_context(
            viewport={"width": width, "height": 780},
            java_script_enabled=False,
            service_workers="block",
            reduced_motion="reduce",
        )
        try:
            page = ctx.new_page()
            response = page.goto(urljoin(BASE, "projets/sinjira/"), wait_until="domcontentloaded", timeout=30000)
            assert response is not None and response.status == 200
            manifest_link = page.locator('link[rel="manifest"]').first
            assert manifest_link.count() == 1
            url = manifest_link.get_attribute("href")
            assert url in ("/manifest.webmanifest", "/site.webmanifest"), (ENGINE, width, url)

            # Le site doit diffuser les deux configurations cohérentes,
            # sans rediriger vers une page privée.
            for name in ("manifest.webmanifest", "site.webmanifest"):
                res = ctx.request.get(urljoin(BASE, name), timeout=15000)
                assert res.status == 200, (ENGINE, width, name, res.status)
                served = res.json()
                assert served == expected, (ENGINE, width, "manifest différent du dépôt", name)
            if width in (240, 390, 1440):
                # Aucun script de connexion ni service tiers n'est exécuté :
                # seuls les statuts des pages publiques et du hub sont testés.
                for entry in expected["shortcuts"]:
                    res = ctx.request.get(urljoin(BASE, entry["url"].lstrip("/")), timeout=15000)
                    assert res.status == 200, (ENGINE, width, entry["url"], res.status)
            print(f"OK {ENGINE}: {width}px, manifeste PWA et raccourcis vers des pages existantes")
        finally:
            ctx.close()


def main():
    assert ENGINE in ("chromium", "firefox", "webkit"), ENGINE
    expected = verify_static_manifest()
    with sync_playwright() as p:
        browser = getattr(p, ENGINE).launch()
        try:
            verify_browser(browser, expected)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
