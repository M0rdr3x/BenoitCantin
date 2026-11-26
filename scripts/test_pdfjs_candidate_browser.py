#!/usr/bin/env python3
"""Exercise the verified PDF.js candidate on loopback only, not production."""
from __future__ import annotations
import argparse
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
from pathlib import Path
import shutil
import tempfile
import threading
import zipfile

from verify_pdfjs_release_candidate import VERSION, SIZE, verify

ROOT = Path(__file__).resolve().parents[1]
MODULE_HASHES = {
    "build/pdf.mjs": "49f16195d418122d8f91a41da3361667fc7d34405d186860e1bb8af4683d6006",
    "build/pdf.worker.mjs": "8336aabf764cb08c818555a2fd2545e4fed10837146de927564875c93b3c4f83",
}
CSP = ("default-src 'none'; script-src 'self'; worker-src 'self'; connect-src 'self'; "
       "img-src 'self' data: blob:; font-src 'self' data: blob:; style-src 'self'; "
       "object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'")
HTML = """<!doctype html><html lang="fr"><meta charset="utf-8"><title>PDF.js candidate</title>
<canvas id="page"></canvas><script type="module" src="/harness.mjs"></script></html>"""
HARNESS = """
import * as pdfjs from '/build/pdf.mjs';
pdfjs.GlobalWorkerOptions.workerSrc = '/build/pdf.worker.mjs';
window.cspViolations = [];
document.addEventListener('securitypolicyviolation', e => window.cspViolations.push(e.effectiveDirective));
window.renderCandidate = async (path, pageNumber, scale) => {
  if (!['/fixture.pdf','/public.pdf'].includes(path)) throw Error('Unexpected PDF path');
  const worker = new pdfjs.PDFWorker();
  let task;
  try {
    await worker.promise;
    if (!(worker.port instanceof Worker)) throw Error('Real dedicated worker required');
    task = pdfjs.getDocument({
      url: path, worker, enableXfa: false, isEvalSupported: false,
      useWasm: false, disableWorkerRendering: true,
      isOffscreenCanvasSupported: false, isImageDecoderSupported: false,
      cMapUrl: '/web/cmaps/', cMapPacked: true,
      standardFontDataUrl: '/web/standard_fonts/',
      wasmUrl: '/web/wasm/', iccUrl: '/web/iccs/',
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
    with archive.open("rb") as stream:
        payload=stream.read(SIZE+1)
    inventory=verify(payload)
    records={x["path"]:x for x in inventory["files"]}
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        for name, record in records.items():
            if not (name in MODULE_HASHES or name=="LICENSE" or name.startswith(("web/cmaps/","web/standard_fonts/","web/iccs/","web/wasm/"))):
                continue
            # Exclude PDF scripting engine and source maps. Only the candidate
            # display/worker and associated font/image resources are staged.
            if name.endswith(".map") or "quickjs-eval." in name:
                continue
            data=z.read(name)
            digest=hashlib.sha256(data).hexdigest()
            if digest!=record["sha256"] or (name in MODULE_HASHES and digest!=MODULE_HASHES[name]):
                raise ValueError("Runtime member changed")
            target=root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open("xb") as out:
                out.write(data)
    (root/"index.html").write_text(HTML,encoding="utf-8")
    (root/"harness.mjs").write_text(HARNESS,encoding="utf-8")
    (root/"fixture.pdf").write_bytes(synthetic_pdf())
    source=ROOT/"projets/projet-nova/documents/01_Resume_Officiel_1_Page_Projet_Nova.pdf"
    if source.is_symlink() or not source.is_file() or not 0 < source.stat().st_size <= 20*1024*1024:
        raise ValueError("Expected public PDF absent")
    shutil.copyfile(source,root/"public.pdf")

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
        stage(archive,root)
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
                    assert not blocked and not errors and page.evaluate("window.cspViolations.length") == 0
                    context.close()
                    print(f"PASS: {browser_name}: real worker, two-page synthetic PDF, zoom, public PDF, strict CSP and no intercepted external request.")
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
