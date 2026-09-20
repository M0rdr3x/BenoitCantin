#!/usr/bin/env python3
"""Static guardrails for the Mode Voyage two-step consent UX."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "compte" / "securite.html"
JS = ROOT / "assets" / "js" / "sinjira-security-travel-consent-v25.js"
CENTER_JS = ROOT / "assets" / "js" / "sinjira-security-center-v24-4-98.js"

errors: list[str] = []


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        errors.append(f"missing {label}: {needle}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        errors.append(f"forbidden {label}: {needle}")


html = HTML.read_text(encoding="utf-8")
js = JS.read_text(encoding="utf-8")
center_js = CENTER_JS.read_text(encoding="utf-8")

require(html, "sinjira-security-travel-consent-v25.js?v=25.0.1", "travel consent module on security page")
require(html, "sinjira-security-center-v24-4-98.js?v=25.0.1", "security center readiness module on security page")
require(html, ">Vérifier avant d’activer</button>", "explicit verification-first button label")
require(js, "document.addEventListener('submit', interceptTravelSubmit, true)", "capture-phase submit gate")
require(js, "event.preventDefault()", "first-step submission prevention")
require(js, "event.stopImmediatePropagation()", "legacy submit-handler blocking before confirmation")
require(js, "approvedSignature === signature", "second-step confirmation signature")
require(js, "navigator.onLine === false", "offline submission guard")
require(js, "window.addEventListener('offline'", "offline invalidation")
require(js, "window.addEventListener('online'", "reconnect invalidation")
require(js, "form.addEventListener('input'", "preview invalidation on input")
require(js, "form.addEventListener('change'", "preview invalidation on change")
require(js, "textContent = draft.destinations.join(', ')", "safe destination preview rendering")
require(js, "textContent = formatMoment(draft.startsAt)", "safe start preview rendering")
require(js, "textContent = formatMoment(draft.endsAt)", "safe end preview rendering")
require(js, "Aucune donnée de ce voyage n’est envoyée au serveur avant votre confirmation", "explicit pre-confirmation travel-data disclosure")
require(js, "jamais de GPS, d’adresse, d’hôtel, de vol ou de trajet quotidien", "minimal-travel-data disclosure")
require(js, "let securityReady", "security-center readiness state")
require(js, "setTravelLocked(form, !securityReady)", "travel form locked before security center ready")
require(js, "if(!securityReady)", "submit blocked before security center ready")
require(js, "sinjira:security-center-ready", "security-center ready event listener")
require(center_js, "document.documentElement.dataset.securityCenterReady='true'", "security center ready state")
require(center_js, "window.dispatchEvent(new Event('sinjira:security-center-ready'))", "security center ready event")
require(center_js, "delete document.documentElement.dataset.securityCenterReady", "failed boot clears readiness")

forbidden_storage = ("localStorage", "sessionStorage", "indexedDB")
for name in forbidden_storage:
    forbid(js, name, "travel draft persistence")

forbidden_transport = ("getSupabase", ".rpc(", "functions.invoke", "fetch(", "XMLHttpRequest", "sendBeacon")
for name in forbidden_transport:
    forbid(js, name, "network transport from consent gate")

forbidden_location = ("geolocation", "latitude", "longitude", "coords")
for name in forbidden_location:
    forbid(js.lower(), name.lower(), "precise location collection")

forbid(js, ".innerHTML", "HTML injection surface in travel consent preview")

if errors:
    print("Mode Voyage consent validation failed:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Mode Voyage consent validation passed.")
