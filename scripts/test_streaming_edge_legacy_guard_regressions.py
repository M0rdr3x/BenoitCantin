#!/usr/bin/env python3
"""Mutation tests: V24.5.48/.49 must defend the *new* streaming guarantees.

Runs the actual legacy contract validators against temporary mutated source
files; never reads remote data, calls Supabase or changes production state.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checked(module) -> int:
    with redirect_stdout(StringIO()):
        return module.main()


def mutate(module, attribute: str, needle: str, replacement: str) -> None:
    target = getattr(module, attribute)
    original = target.read_text("utf-8")
    assert original.count(needle) >= 1, f"Missing fixture: {needle}"
    with TemporaryDirectory(prefix="sinjira-edge-validator-") as tmp:
        altered = Path(tmp) / target.name
        altered.write_text(original.replace(needle, replacement, 1), "utf-8")
        setattr(module, attribute, altered)
        try:
            assert checked(module) != 0, (
                f"{module.__name__} accepted malicious mutation of "
                f"{attribute}: {needle!r}"
            )
        finally:
            setattr(module, attribute, target)


def main() -> None:
    template = load("validator_pdf_49", ROOT / "scripts/validate_edge_template_fetch_v24_5_49.py")
    privacy = load("validator_privacy_48", ROOT / "scripts/validate_edge_response_privacy_v24_5_48.py")
    assert checked(template) == 0, "Valid PDF streaming implementation rejected"
    assert checked(privacy) == 0, "Valid privacy streaming implementation rejected"

    mutations = [
        (template, "REPORT",
         "readLimitedBinaryResponse(response,MAX_TEMPLATE_BYTES)",
         "new Uint8Array(await response.arrayBuffer())"),
        (template, "LIMITED",
         "value.byteLength > maxBytes - byteCount",
         "value.byteLength > 200_000_000"),
        (template, "LIMITED",
         "if (byteCount === 0) return { ok: false }",
         "if (false) return { ok: false }"),
        (privacy, "LIMITED", "byteCount > maxBytes", "byteCount > 20_000_000"),
        (privacy, "LIMITED",
         "new TextDecoder('utf-8', { fatal: true })",
         "new TextDecoder('utf-8')"),
        (privacy, "REPORT",
         "readLimitedUtf8Body(req, MAX_REQUEST_BYTES)", "await req.text()"),
        (privacy, "DOCURL",
         "readLimitedUtf8Body(req,MAX_REQUEST_BYTES)", "await req.text()"),
        (privacy, "DOCURL",
         "parsed.username||parsed.password", "false"),
        (privacy, "DOCURL",
         "relative&&parsed.origin!==DOCUMENT_URL_BASE", "false"),
        (privacy, "DOCURL",
         r"\\u0000-\\u0020", "a-z"),
    ]
    for module, attribute, needle, replacement in mutations:
        mutate(module, attribute, needle, replacement)
    print(f"PASS: {len(mutations)} mutations Edge détectées, anciens validateurs alignés sur les limites en flux.")


if __name__ == "__main__":
    main()
