"""CSP locale de secours pour les sorties HTML statiques privées.

Les en-têtes HTTP sont la protection principale sur Netlify/Vercel. GitHub
Pages ne permet pas ces en-têtes: une meta CSP injectée AVANT les scripts
applique les directives compatibles avec HTML (frame-ancestors reste HTTP).
"""
from __future__ import annotations

import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path

PRIVATE_SCOPES = frozenset({"compte", "admin", "Admin", "app"})
ROOT_PRIVATE_ALIAS = Path("administration.html")
HEAD_OPEN = re.compile(r"<head(?:\s[^>]*)?>", re.IGNORECASE)


class PrivateHtmlAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.meta_policies: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag == "script" and not attrs_map.get("src"):
            self.errors.append("JavaScript inline sans src interdit")
        for name, value in attrs:
            if name.startswith("on"):
                self.errors.append(f"attribut événement inline interdit: {name}")
            if name in {"href", "src", "action", "formaction", "xlink:href"} and (
                value or ""
            ).lstrip().lower().startswith("javascript:"):
                self.errors.append(f"URL javascript: interdite dans {name}")
        if tag == "meta" and (attrs_map.get("http-equiv") or "").lower() == "content-security-policy":
            self.meta_policies.append(attrs_map.get("content") or "")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def is_private_html(rel: Path) -> bool:
    return rel == ROOT_PRIVATE_ALIAS or (
        len(rel.parts) > 1 and rel.parts[0] in PRIVATE_SCOPES
        and rel.suffix.lower() in {".html", ".htm"}
    )


def policy_for(config: dict, rel: Path) -> str:
    if not is_private_html(rel):
        return ""
    path = "/administration.html" if rel == ROOT_PRIVATE_ALIAS else f"/{rel.parts[0]}/*"
    policies = [
        (item.get("values") or {}).get("Content-Security-Policy")
        for item in config.get("headers", [])
        if item.get("for") == path
    ]
    if len(policies) != 1 or not isinstance(policies[0], str):
        raise ValueError(f"CSP privée Netlify absente ou ambiguë: {path}")
    policy = policies[0]
    if ("script-src-attr 'none'" not in policy or
            "object-src 'none'" not in policy or
            "script-src 'self' 'unsafe-inline'" in policy or
            "script-src 'self' 'unsafe-eval'" in policy):
        raise ValueError(f"CSP privée insuffisante: {path}")
    # frame-ancestors n'a aucun effet dans une CSP meta; l'en-tête HTTP reste
    # responsable de cette directive sur les hébergeurs compatibles.
    supported = [
        directive.strip()
        for directive in policy.split(";")
        if directive.strip() and not directive.strip().startswith("frame-ancestors")
    ]
    return "; ".join(supported)


def harden_private_html(rel: Path, source: str, netlify_config: dict) -> str:
    if not is_private_html(rel):
        return source
    policy = policy_for(netlify_config, rel)
    audit = PrivateHtmlAudit()
    audit.feed(source)
    audit.close()
    if audit.errors or audit.meta_policies:
        raise ValueError(f"{rel}: JavaScript inline / meta CSP non validé: "
                         + ", ".join(audit.errors))
    matches = list(HEAD_OPEN.finditer(source))
    if len(matches) != 1 or "</head" not in source.lower():
        raise ValueError(f"{rel}: un unique élément <head> est obligatoire")
    marker = ('<meta http-equiv="Content-Security-Policy" content="'
              + escape(policy, quote=True) + '">')
    insert_at = matches[0].end()
    return source[:insert_at] + "\n" + marker + "\n" + source[insert_at:]


def private_csp_output_errors(rel: Path, html: str, netlify_config: dict) -> list[str]:
    if not is_private_html(rel):
        return []
    audit = PrivateHtmlAudit()
    audit.feed(html)
    audit.close()
    expected = policy_for(netlify_config, rel)
    errors = list(audit.errors)
    if audit.meta_policies != [expected]:
        errors.append(f"{rel}: CSP meta de sortie absente, multiple ou non conforme")
    match = HEAD_OPEN.search(html)
    meta_pos = html.find('http-equiv="Content-Security-Policy"')
    first_script = re.search(r"<script\b", html, re.IGNORECASE)
    if not match or meta_pos < match.end() or (
        first_script is not None and meta_pos > first_script.start()
    ):
        errors.append(f"{rel}: CSP meta doit précéder les scripts")
    return errors
