#!/usr/bin/env python3
"""Offline inventory of literal executable/style loads in an isolated web build.

This is an inventory, not a JS parser, network verification, SRI byte verification,
or complete runtime dependency graph. No remote resources are fetched or executed.
"""
from __future__ import annotations
import argparse
import base64
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit
import unittest

MAX_FILE = 16 * 1024 * 1024
MAX_FILES = 12000
MAX_TOTAL = 256 * 1024 * 1024
MAX_RECORDS = 20000
KINDS = {".html", ".htm", ".js", ".mjs", ".cjs", ".css", ".svg", ".xml"}
HOST = re.compile(r"[a-z0-9.-]{1,253}")
SAFE_CDN_PATH = re.compile(r"/[a-zA-Z0-9@/._+%~-]{1,512}")
CDNS = {"cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com", "esm.sh"}
JS_PATTERNS = (
    ("module-import", re.compile(r"""\b(?:import|export)\s+(?:[^;\r\n'"]{0,400}\bfrom\s*)?(['"])([^'"\r\n]{1,4096})\1""")),
    ("dynamic-import", re.compile(r"""\bimport\s*\(\s*(['"])([^'"\r\n]{1,4096})\1""")),
    ("worker", re.compile(r"""\b(?:Worker|SharedWorker|importScripts|serviceWorker\.register)\s*\(\s*(['"])([^'"\r\n]{1,4096})\1""")),
    ("worker-src-assignment", re.compile(r"""\bGlobalWorkerOptions\.workerSrc\s*=\s*(['"])([^'"\r\n]{1,4096})\1""")),
)
CSS_IMPORT = re.compile(r"""@import\s+(?:url\(\s*)?(['"]?)([^'"\s;)]+)\1""", re.I)
DYNAMIC = re.compile(r"""\b(?:import|Worker|SharedWorker|importScripts|serviceWorker\.register)\s*\(\s*(?!['"\s])""")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def sri_status(value):
    if value is None:
        return "absent"
    if not value.strip():
        return "invalid"
    for token in value.split():
        match = re.fullmatch(r"(sha256|sha384|sha512)-([A-Za-z0-9+/]+={0,2})", token)
        if not match:
            return "invalid"
        try:
            raw = base64.b64decode(match[2], validate=True)
        except ValueError:
            return "invalid"
        if len(raw) != {"sha256":32, "sha384":48, "sha512":64}[match[1]] or base64.b64encode(raw).decode() != match[2]:
            return "invalid"
    return "syntax-valid-not-content-verified"

def remote(value):
    # Report explicit absolute and scheme-relative references only; do not
    # disclose URL credentials, query values, fragments or arbitrary paths.
    value = value.strip()
    if not re.match(r"(?i)^(?:https?:|//|[a-z][a-z0-9+.-]*:)", value):
        return None
    result = {"url_sha256": sha(value.encode()), "origin": None, "scheme": "invalid",
              "query_or_fragment": False, "credentials": False, "cdn_path": None}
    try:
        u = urlsplit(value)
        scheme = u.scheme.lower() or "scheme-relative"
        result["scheme"] = scheme if scheme in ("https","http","scheme-relative","data","blob","javascript","file","node") else "other"
        result["query_or_fragment"] = "?" in value or "#" in value
        result["credentials"] = u.username is not None or u.password is not None
        host = u.hostname
        if host and HOST.fullmatch(host) and not result["credentials"]:
            port = u.port
            result["origin"] = host + (":" + str(port) if port is not None else "")
            if host in CDNS and SAFE_CDN_PATH.fullmatch(u.path) and not result["query_or_fragment"]:
                result["cdn_path"] = u.path
        if any(ord(c) < 32 or ord(c) == 127 for c in value) or "\\" in value:
            result["scheme"] = "invalid"
    except ValueError:
        pass
    return result

class Scan:
    def __init__(self, path, records, counts):
        self.path, self.records, self.counts = path, records, counts

    def add(self, kind, value, line, integrity=None, crossorigin=None):
        if not isinstance(value,str):
            self.counts["unresolved_reference"] += 1
            return
        info = remote(value)
        if info is None:
            return
        if len(self.records) >= MAX_RECORDS:
            raise ValueError("Reference inventory limit")
        self.records.append({"file":self.path,"line":line,"kind":kind,**info,
                             "sri":sri_status(integrity) if kind in ("script-src","stylesheet","script-preload","style-preload","modulepreload") else "not-applicable",
                             "crossorigin": "absent" if crossorigin is None else "anonymous" if crossorigin in ("","anonymous") else "other"})
    def js(self, source, line=1):
        for kind, pattern in JS_PATTERNS:
            for m in pattern.finditer(source):
                self.add(kind,m[2],line+source.count("\n",0,m.start()))
        self.counts["possible_nonliteral_js_load"] += len(DYNAMIC.findall(source))
        # Additional signatures are unresolved, never claimed to be covered.
        self.counts["possible_dynamic_script_creation"] += len(re.findall(r"""\bcreateElement\s*\(\s*['"]script['"]""",source,re.I))
    def css(self, source, line=1):
        for m in CSS_IMPORT.finditer(source):
            self.add("css-import",m[2],line+source.count("\n",0,m.start()))

class Markup(HTMLParser):
    def __init__(self, scan):
        super().__init__(convert_charrefs=True)
        self.scan = scan
        self.mode = None
        self.parts = []
        self.start = 1
    def handle_starttag(self, tag, attrs):
        keys = [k for k,v in attrs]
        if len(set(keys)) != len(keys):
            self.scan.counts["duplicate_html_attributes"] += 1
        a = dict(attrs)
        line = self.getpos()[0]
        if tag == "script":
            src = a.get("src") or a.get("href") or a.get("xlink:href")
            if src:
                self.scan.add("script-src",src,line,a.get("integrity"),a.get("crossorigin"))
            else:
                typ = (a.get("type") or "").strip().lower()
                self.mode = "importmap" if typ == "importmap" else "js" if typ in ("","module","text/javascript","application/javascript") else None
                self.parts = []
                self.start = line
        elif tag == "style":
            self.mode, self.parts, self.start = "css", [], line
        elif tag == "link":
            rel = set((a.get("rel") or "").lower().split())
            kind = ("stylesheet" if "stylesheet" in rel else "modulepreload" if "modulepreload" in rel else
                    a.get("as")+"-preload" if "preload" in rel and a.get("as") in ("script","style") else None)
            if kind:
                self.scan.add(kind,a.get("href"),line,a.get("integrity"),a.get("crossorigin"))
        elif tag in ("iframe","object","embed"):
            self.scan.add("embedded-"+tag,a.get("data") if tag=="object" else a.get("src"),line)
        elif tag == "base" and a.get("href"):
            self.scan.add("base-url",a["href"],line)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
        self.handle_endtag(tag)
    def handle_data(self, data):
        if self.mode:
            self.parts.append(data)
    def handle_endtag(self, tag):
        if tag not in ("script","style") or not self.mode:
            return
        content = "".join(self.parts)
        if self.mode == "js":
            self.scan.js(content,self.start)
        elif self.mode == "css":
            self.scan.css(content,self.start)
        else:
            try:
                obj = json.loads(content)
                tables = [obj.get("imports",{}),*obj.get("scopes",{}).values()]
                for table in tables:
                    for target in table.values():
                        self.scan.add("importmap",target,self.start)
            except (ValueError,AttributeError,TypeError):
                self.scan.counts["unresolved_importmap"] += 1
        self.mode, self.parts = None, []

def scan_text(path, source, records, counts):
    scan = Scan(path,records,counts)
    suffix = Path(path).suffix.lower()
    if suffix in (".html",".htm",".svg",".xml"):
        parser = Markup(scan)
        parser.feed(source)
        parser.close()
        if parser.mode:
            counts["unclosed_inline_block"] += 1
    elif suffix == ".css":
        scan.css(source)
    else:
        scan.js(source)

def inventory(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Invalid isolated build")
    records, counts, source_index = [], Counter(), []
    total = 0
    for path in sorted(root.rglob("*")):
        st = path.lstat()
        if stat.S_ISDIR(st.st_mode):
            continue
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise ValueError("Unexpected file in isolated build")
        if path.suffix.lower() not in KINDS:
            continue
        if st.st_size > MAX_FILE or len(source_index) >= MAX_FILES or total + st.st_size > MAX_TOTAL:
            raise ValueError("Inventory size limit")
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE+1)
        if len(data) != st.st_size:
            raise ValueError("Source changed during inventory")
        total += len(data)
        relative = path.relative_to(root).as_posix()
        source_index.append({"file":relative,"sha256":sha(data)})
        counts["scanned_"+path.suffix.lower()[1:]] += 1
        scan_text(relative,data.decode("utf-8-sig"),records,counts)
    if counts["scanned_html"] < 1 or counts["scanned_js"] < 1:
        raise ValueError("Browser source coverage incomplete")
    return {"format":"sinjira-browser-reference-inventory-v1","status":"candidate-observation-not-approval",
            "source_files":len(source_index),"source_index_sha256":sha(json.dumps(source_index,sort_keys=True,separators=(",",":")).encode()),
            "counts":dict(sorted(counts.items())),
            "reference_counts":dict(sorted(Counter(r["kind"] for r in records).items())),
            "scheme_counts":dict(sorted(Counter(r["scheme"] for r in records).items())),
            "records":sorted(records,key=lambda r:(r["file"],r["line"],r["kind"],r["url_sha256"]))}

class Tests(unittest.TestCase):
    def test_reference_redaction(self):
        for url in ("https://user:pass@example.com/private?q=secret#secret","https://example.com/private?q=secret","data:text/javascript,secret"):
            result=remote(url)
            self.assertNotIn("secret",json.dumps(result))
            self.assertNotIn("pass",json.dumps(result))
        self.assertEqual(remote("//cdn.jsdelivr.net/npm/pkg@1.2.3/+esm")["scheme"],"scheme-relative")
        self.assertEqual(remote("https://cdn.jsdelivr.net/npm/pkg@1.2.3/+esm")["cdn_path"],"/npm/pkg@1.2.3/+esm")
        self.assertIsNone(remote("/assets/js/app.js"))
        self.assertEqual(remote("http://example.test/a")["scheme"],"http")
    def test_sri(self):
        good="sha384-"+base64.b64encode(bytes(48)).decode()
        self.assertEqual(sri_status(good),"syntax-valid-not-content-verified")
        for bad in ("","sha1-AAAA","sha384-AAAA",good+" invalid"):
            self.assertEqual(sri_status(bad),"invalid")
        self.assertEqual(sri_status(None),"absent")
    def test_scan(self):
        text="""<script SRC="https://cdn.jsdelivr.net/npm/a@1.2.3/+esm"></script>
<link rel="modulepreload" href="//unpkg.com/a">
<script type="module">import x from 'https://esm.sh/a'; import('https://esm.sh/b'); import(variable);</script>
<style>@import url('https://example.test/style.css');</style>
<script type="importmap">{"imports":{"x":"https://esm.sh/x"}}</script>
<iframe src="https://example.test/frame"></iframe>
<script src="/local.js"></script>"""
        records,counts=[],Counter()
        scan_text("index.html",text,records,counts)
        self.assertEqual(Counter(x["kind"] for x in records),Counter({"script-src":1,"modulepreload":1,"module-import":1,"dynamic-import":1,"css-import":1,"importmap":1,"embedded-iframe":1}))
        self.assertEqual(counts["possible_nonliteral_js_load"],1)
        scan_text("worker.js","new Worker('https://example.test/w.js')",records,counts)
        self.assertEqual(records[-1]["kind"],"worker")
        scan_text("worker.js","pdfjsLib.GlobalWorkerOptions.workerSrc='https://example.test/w.js';",records,counts)
        self.assertEqual(records[-1]["kind"],"worker-src-assignment")
        self.assertEqual(remote("node:fs")["scheme"],"node")
    def test_file_boundary(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"index.html").write_text("<html></html>")
            (root/"app.js").write_text("const a=1;")
            self.assertEqual(inventory(root)["source_files"],2)
            (root/"alias.js").symlink_to(root/"app.js")
            with self.assertRaises(ValueError):
                inventory(root)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--root",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--source-sha")
    args=parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if not args.root or not args.output or not re.fullmatch(r"[a-f0-9]{40}",args.source_sha or ""):
        parser.error("isolated root, output and source SHA required")
    try:
        if args.root.resolve() in args.output.resolve().parents:
            raise ValueError("Report must remain outside public build")
        report=inventory(args.root)
        if report["scheme_counts"].get("node",0):
            raise ValueError("Node-only imports in browser publication")
        report["source_sha"]=args.source_sha
        payload=(json.dumps(report,indent=2,sort_keys=True)+"\n").encode()
        with args.output.open("xb") as out:
            out.write(payload)
        print("PASS: browser reference inventory",report["source_files"],"files",len(report["records"]),"literal references; SHA-256",sha(payload))
        print("Counts:",json.dumps(report["reference_counts"],sort_keys=True))
    except (ValueError,OSError,TypeError,AttributeError,KeyError):
        print("FAIL: browser inventory rejected")
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
