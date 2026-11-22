#!/usr/bin/env python3
"""Deterministic, fail-closed Supabase transport sandbox for local browser E2E.

This is NOT a production API security test. It prevents browser tests with
synthetic users/data from reaching the live Supabase project. Never return
production content or include auth headers/tokens in CI logs.
"""
from __future__ import annotations

import json
from urllib.parse import urlsplit

PRODUCTION_SUPABASE_ORIGIN = "https://gpvivleexywljowcqkru.supabase.co"
NOVEL_TABLE = "/rest/v1/sinjira_novels"
NOVEL_COMMENTS_RPC = "/rest/v1/rpc/list_sinjira_novel_comments"
PUBLIC_FIXTURE_PATHS = frozenset({NOVEL_TABLE, NOVEL_COMMENTS_RPC})
CORS_HEADERS = {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "apikey, authorization, content-type, x-client-info, accept, prefer",
    "cache-control": "no-store",
    "content-type": "application/json; charset=utf-8",
}


def isolated_api_response(method: str, url: str) -> tuple[int, str]:
    """Static anonymous public data ONLY. Every other request is denied."""
    parsed = urlsplit(url)
    target = urlsplit(PRODUCTION_SUPABASE_ORIGIN)
    if parsed.scheme != target.scheme or parsed.netloc != target.netloc:
        return (403, '{"code":"CI_NETWORK_DENIED"}')

    if method == "OPTIONS" and parsed.path in PUBLIC_FIXTURE_PATHS:
        return (204, "")
    if method == "GET" and parsed.path == NOVEL_TABLE:
        # PostgREST .maybeSingle() expects one object, not a list.
        return (200, '{"id":"ci-synthetic-novel","comments_enabled":true}')
    if method == "POST" and parsed.path == NOVEL_COMMENTS_RPC:
        return (200, "[]")
    return (403, '{"code":"CI_NETWORK_DENIED"}')


def install_isolated_supabase_api(context) -> None:
    """Replace every request to production Supabase with a synthetic response."""
    def intercept(route):
        request = route.request
        status, body = isolated_api_response(request.method, request.url)
        route.fulfill(status=status, headers=CORS_HEADERS, body=body)

    # No route.continue_(), no route.fetch(): never contact real production.
    # Explicit host matching also avoids intercepting the localhost site.
    context.route(PRODUCTION_SUPABASE_ORIGIN + "/**", intercept)
