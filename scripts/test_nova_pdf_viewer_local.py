#!/usr/bin/env python3
"""Exercise the real NOVA viewer section and module in a loopback-only harness."""
from __future__ import annotations
import argparse
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import re
import shutil
import tempfile
import threading
from stage_pdfjs_runtime import stage, check_tree
from test_pdfjs_candidate_browser import Handler, CSP, synthetic_pdf

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT/"projets/projet-nova"
MODULE = "nova-pdf-viewer.mjs"

class ViewerHandler(Handler):
    def end_headers(self):
        # Existing viewer markup has an inline width attribute. Keep strict
        # script, worker and connection restrictions; permit inline style only.
        self.send_header("Content-Security-Policy",CSP.replace("style-src 'self';","style-src 'self' 'unsafe-inline';"))
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Cache-Control","no-store")
        from http.server import SimpleHTTPRequestHandler
        SimpleHTTPRequestHandler.end_headers(self)

def run(archive, browser_name):
    from playwright.sync_api import expect, sync_playwright
    with tempfile.TemporaryDirectory(prefix="nova-viewer-local-") as temp:
        root=Path(temp)
        assets=root/"assets"
        assets.mkdir()
        documents=root/"documents"
        documents.mkdir()
        source=(NOVA/"visionneuse.html").read_text("utf-8")
        section=re.search(r'<main id="contenu">.*?</section></main>',source,re.S)
        if not section:
            raise ValueError("Viewer section absent")
        html=('<!doctype html><html lang="fr"><meta charset="utf-8"><title>Viewer test</title>'
              '<script defer src="assets/documents.js"></script>'+section[0]+
              '<script type="module" src="assets/nova-pdf-viewer.mjs"></script></html>')
        (root/"index.html").write_text(html,encoding="utf-8")
        # Synthetic fixture is used only for testing the real viewer controls;
        # the public documents are separately exercised by the runtime test.
        for name in ("01_Resume_Officiel_1_Page_Projet_Nova.pdf","02_Depliant_Public_4_Pages_Projet_Nova.pdf"):
            (documents/name).write_bytes(synthetic_pdf())
        shutil.copyfile(NOVA/"assets/documents.js",assets/"documents.js")
        original=(NOVA/"assets"/MODULE).read_text("utf-8")
        if original.count("const RUNTIME_ENABLED = false;")!=1:
            raise ValueError("Unapproved activation")
        (assets/MODULE).write_text(original,encoding="utf-8")
        server=ThreadingHTTPServer(("127.0.0.1",0),partial(ViewerHandler,directory=temp))
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        origin=f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as pw:
                browser=getattr(pw,browser_name).launch(headless=True)
                try:
                    context=browser.new_context(service_workers="block",accept_downloads=False)
                    external, observed, errors=[],[],[]
                    def route_request(route):
                        url=route.request.url
                        if url.startswith(origin+"/"):
                            observed.append(url)
                            route.continue_()
                        else:
                            external.append("blocked")
                            route.abort()
                    context.route("**/*",route_request)
                    page=context.new_page()
                    page.set_default_timeout(30000)
                    page.on("pageerror",lambda _:errors.append("pageerror"))
                    page.add_init_script("window.violations=[];document.addEventListener('securitypolicyviolation', e=>window.violations.push(e.effectiveDirective));")
                    page.goto(origin+"/?doc=resume")
                    expect(page.locator("#viewerStatus")).to_contain_text("indisponible",timeout=30000)
                    assert page.locator("#docSelect option").count()==11
                    assert page.locator("#openPdfBtn").get_attribute("href")==origin+"/documents/01_Resume_Officiel_1_Page_Projet_Nova.pdf"
                    assert page.locator("#openPdfBtn").get_attribute("rel")=="noopener noreferrer"
                    assert page.locator("#downloadBtn").get_attribute("download")=="01_Resume_Officiel_1_Page_Projet_Nova.pdf"
                    assert all(page.locator("#"+x).is_disabled() for x in ("prevPage","nextPage","zoomOut","zoomIn"))
                    assert not any("/pdfjs-6.5.438/" in x or x.endswith(".pdf") for x in observed)
                    # Unrecognized request parameter must not become a URL.
                    page.goto(origin+"/?doc=https%3A%2F%2Fexample.invalid%2Fbad.pdf")
                    expect(page.locator("#viewerStatus")).to_contain_text("indisponible",timeout=30000)
                    assert page.locator("#docSelect").input_value()=="resume"
                    assert not external and not errors and page.evaluate("window.violations.length")==0
                    records=stage(archive,assets/"pdfjs-6.5.438")
                    # Activation is simulated solely in the disposable harness.
                    (assets/MODULE).write_text(original.replace("const RUNTIME_ENABLED = false;","const RUNTIME_ENABLED = true;"),encoding="utf-8")
                    page.goto(origin+"/?doc=resume")
                    # Locator assertions poll in Playwright's injected DOM
                    # engine without eval-ing a string in the page context.
                    # Never relax script-src to accommodate a test helper.
                    canvas=page.locator("#pdfPages canvas")
                    expect(page.locator("#pageInfo")).to_have_text("Page 1 / 2",timeout=30000)
                    expect(page.locator("#nextPage")).to_be_enabled(timeout=30000)
                    expect(canvas).to_have_count(1,timeout=30000)
                    expect(canvas).to_have_attribute("width","240",timeout=30000)
                    first=int(canvas.get_attribute("width"))
                    page.locator("#nextPage").click()
                    expect(page.locator("#pageInfo")).to_have_text("Page 2 / 2",timeout=30000)
                    expect(page.locator("#zoomIn")).to_be_enabled(timeout=30000)
                    page.locator("#zoomIn").click()
                    expect(canvas).to_have_attribute("width","270",timeout=30000)
                    expect(page.locator("#zoomOut")).to_be_enabled(timeout=30000)
                    assert int(canvas.get_attribute("width")) > first
                    page.locator("#docSelect").select_option("depliant")
                    expect(page.locator("#pageInfo")).to_have_text("Page 1 / 2",timeout=30000)
                    expect(page.locator("#docSelect")).to_be_enabled(timeout=30000)
                    expect(canvas).to_have_attribute("width","240",timeout=30000)
                    assert page.locator("#downloadBtn").get_attribute("download")=="02_Depliant_Public_4_Pages_Projet_Nova.pdf"
                    assert not external and not errors and page.evaluate("window.violations.length")==0
                    check_tree(assets/"pdfjs-6.5.438",records)
                    context.close()
                    print(f"PASS: {browser_name}: actual viewer section, fail-closed fallback, public catalog, local worker rendering, page/zoom/document selection.")
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--browser",choices=("chromium","firefox","webkit"),required=True)
    a=p.parse_args()
    run(a.archive,a.browser)
