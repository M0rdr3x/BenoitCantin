#!/usr/bin/env python3
"""Exercise the verified PDF.js candidate on loopback only, not production."""
from __future__ import annotations
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
import threading

from verify_pdfjs_release_candidate import VERSION
from stage_pdfjs_runtime import stage as stage_runtime, check_tree

ROOT = Path(__file__).resolve().parents[1]
CSP = ("default-src 'none'; script-src 'self'; worker-src 'self'; connect-src 'self'; "
       "img-src 'self' data: blob:; font-src 'self' data: blob:; style-src 'self'; "
       "object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'")
HTML = """<!doctype html><html lang="fr"><meta charset="utf-8"><title>PDF.js candidate</title>
<canvas id="page"></canvas><script type="module" src="/harness.mjs"></script></html>"""
HARNESS = """
import * as pdfjs from '/runtime/build/pdf.mjs';
pdfjs.GlobalWorkerOptions.workerSrc = '/runtime/build/pdf.worker.mjs';
window.cspViolations = [];
document.addEventListener('securitypolicyviolation', e => window.cspViolations.push(e.effectiveDirective));
window.renderCandidate = async (path, pageNumber, scale) => {
  if (!['/fixture.pdf','/public.pdf','/public-book.pdf','/public-brochure.pdf'].includes(path)) throw Error('Unexpected PDF path');
  const worker = new pdfjs.PDFWorker();
  let task;
  try {
    await worker.promise;
    if (!(worker.port instanceof Worker)) throw Error('Real dedicated worker required');
    task = pdfjs.getDocument({
      url: path, worker, enableXfa: false, isEvalSupported: false,
      useWasm: false, disableWorkerRendering: true,
      isOffscreenCanvasSupported: false, isImageDecoderSupported: false,
      cMapUrl: '/runtime/web/cmaps/', cMapPacked: true,
      standardFontDataUrl: '/runtime/web/standard_fonts/',
      wasmUrl: '/runtime/web/wasm/', iccUrl: '/runtime/web/iccs/',
      disableAutoFetch: true, disableStream: true,
      maxImageSize: 25000000,
      stopAtErrors: true,
    });
    const doc = await task.promise;
    const page = await doc.getPage(pageNumber);
    const viewport = page.getViewport({scale});
    const canvas = document.getElementById('page');
    canvas.width = Math.ceil(viewport.width);
    canvas.height = Math.ceil(viewport.height);
    if (!canvas.width || !canvas.height || canvas.width * canvas.height > 10000000)
      throw Error('Unexpected canvas size');
    const ctx = canvas.getContext('2d');
    await page.render({canvasContext: ctx, viewport}).promise;
    const data = ctx.getImageData(0,0,canvas.width,canvas.height).data;
    let visible = 0;
    for (let i=0; i<data.length; i+=4)
      if (data[i+3] && (data[i]<230 || data[i+1]<230 || data[i+2]<230)) visible++;
    return {version:pdfjs.version,pages:doc.numPages,width:canvas.width,height:canvas.height,visible};
  } finally {
    try { if (task) await task.destroy(); } finally { worker.destroy(); }
  }
};
"""

def synthetic_pdf():
    streams = [b"0 0 0 rg 20 20 80 60 re f", b"0 0 0 rg 40 40 100 90 re f"]
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << >> /Contents 5 0 R >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << >> /Contents 6 0 R >>",
        *[b"<< /Length "+str(len(x)).encode()+b" >>\nstream\n"+x+b"\nendstream" for x in streams],
    ]
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for n,obj in enumerate(objects,1):
        offsets.append(len(result))
        result.extend(str(n).encode()+b" 0 obj\n"+obj+b"\nendobj\n")
    start=len(result)
    result.extend(b"xref\n0 7\n0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(b"trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n"+str(start).encode()+b"\n%%EOF\n")
    return bytes(result)

def stage(archive, root):
    records = stage_runtime(archive,root/"runtime")
    (root/"index.html").write_text(HTML,encoding="utf-8")
    (root/"harness.mjs").write_text(HARNESS,encoding="utf-8")
    (root/"fixture.pdf").write_bytes(synthetic_pdf())
    fixtures = {
        "public.pdf": "01_Resume_Officiel_1_Page_Projet_Nova.pdf",
        "public-book.pdf": "04_Livre_Nova_Complet.pdf",
        "public-brochure.pdf": "02_Depliant_Public_4_Pages_Projet_Nova.pdf",
    }
    for name,filename in fixtures.items():
        source=ROOT/"projets/projet-nova/documents"/filename
        if source.is_symlink() or not source.is_file() or not 0 < source.stat().st_size <= 20*1024*1024:
            raise ValueError("Expected public PDF absent")
        shutil.copyfile(source,root/name)
    return records

class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,".mjs":"text/javascript",".wasm":"application/wasm"}
    def end_headers(self):
        self.send_header("Content-Security-Policy",CSP)
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Cache-Control","no-store")
        super().end_headers()
    def list_directory(self,path):
        self.send_error(404)
        return None
    def log_message(self,*args):
        pass

def run(archive,browser_name):
    from playwright.sync_api import sync_playwright
    with tempfile.TemporaryDirectory(prefix="pdfjs-browser-") as temp:
        root=Path(temp)
        records=stage(archive,root)
        server=ThreadingHTTPServer(("127.0.0.1",0),partial(Handler,directory=temp))
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        origin=f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as pw:
                browser=getattr(pw,browser_name).launch(headless=True)
                try:
                    context=browser.new_context(service_workers="block",accept_downloads=False)
                    blocked=[]
                    def route_request(route):
                        if route.request.url.startswith(origin+"/"):
                            route.continue_()
                        else:
                            blocked.append("external")
                            route.abort()
                    context.route("**/*",route_request)
                    page=context.new_page()
                    page.set_default_timeout(30000)
                    errors=[]
                    page.on("pageerror",lambda _:errors.append("pageerror"))
                    page.goto(origin+"/",wait_until="load")
                    page.wait_for_function("typeof window.renderCandidate === 'function'")
                    # wait_for_function has an explicit deadline; evaluate is
                    # also bounded by the overall process timeout in CI.
                    result=page.evaluate("async () => await window.renderCandidate('/fixture.pdf',1,1)")
                    assert result["version"]==VERSION and result["pages"]==2 and result["width"]==200 and result["height"]==200 and result["visible"]>1000
                    second=page.evaluate("async () => await window.renderCandidate('/fixture.pdf',2,1.5)")
                    assert second["pages"]==2 and second["width"]==300 and second["height"]==300 and second["visible"]>result["visible"]
                    public=page.evaluate("async () => await window.renderCandidate('/public.pdf',1,0.8)")
                    assert public["version"]==VERSION and public["pages"]>=1 and public["visible"]>100
                    for path in ("/public-book.pdf","/public-brochure.pdf"):
                        result=page.evaluate("(path) => window.renderCandidate(path,1,0.8)",path)
                        assert result["version"]==VERSION and result["pages"]>=1 and result["visible"]>100
                    assert not blocked and not errors and page.evaluate("window.cspViolations.length") == 0
                    check_tree(root/"runtime",records)
                    context.close()
                    print(f"PASS: {browser_name}: real worker, two-page synthetic PDF, zoom, three public PDFs, strict CSP and no intercepted external request.")
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
    args=p.parse_args()
    run(args.archive,args.browser)
