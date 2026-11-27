#!/usr/bin/env python3
"""Recette HTML/CSS administrative locale, sans session ni données privées."""
import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

BASE=os.environ.get("BASE_URL","http://127.0.0.1:4173/")
ENGINE=os.environ.get("BROWSER","chromium")
assert urlparse(BASE).hostname in {"127.0.0.1","localhost"}, "Site local uniquement"

with sync_playwright() as p:
    browser=getattr(p,ENGINE).launch()
    try:
        context=browser.new_context(java_script_enabled=False,service_workers="block")
        context.route("**/*",lambda route: route.continue_() if urlparse(route.request.url).hostname in {"127.0.0.1","localhost"} else route.abort())
        page=context.new_page()
        for width in (240,320,390,768,1440):
            page.set_viewport_size({"width":width,"height":844})
            response=page.goto(urljoin(BASE,"admin/sinjira/"),wait_until="load",timeout=30000)
            assert response and response.ok
            result=page.evaluate("""() => {
              const main=document.querySelector('main');
              const tabs=[...document.querySelectorAll('[data-admin-tab]')];
              const labels=[...main.querySelectorAll('label[for]')];
              const controls=[...main.querySelectorAll('input:not([type=hidden]),select,textarea')].filter(el=>el.getClientRects().length);
              return {overflow:document.documentElement.scrollWidth>innerWidth+2,
                mainRight:main.getBoundingClientRect().right,
                labels:labels.length, valid:labels.every(el=>el.control),
                tabs:tabs.length, linked:tabs.every(el=>document.getElementById(el.getAttribute('aria-controls'))),
                heights:tabs.map(el=>el.getBoundingClientRect().height),
                controls:controls.map(el=>({left:el.getBoundingClientRect().left,right:el.getBoundingClientRect().right})),
                hidden:document.querySelector('[data-admin-panel="documents"]').getClientRects().length===0};
            }""")
            assert result["labels"]>=40 and result["valid"],(width,"libellés")
            assert result["tabs"]==15 and result["linked"] and result["hidden"],(width,"panneaux")
            assert min(result["heights"])>=44,(width,"cibles tactiles")
            assert not result["overflow"] and result["mainRight"]<=width+2,(width,"débordement")
            assert all(c["left"]>=-2 and c["right"]<=width+2 for c in result["controls"]),(width,"champs hors écran")
        print(f"OK {ENGINE}: console administrative 240–1440px, HTML/CSS local sans session.")
    finally:
        browser.close()
