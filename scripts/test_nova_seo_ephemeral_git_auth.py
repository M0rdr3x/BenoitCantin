#!/usr/bin/env python3
"""Simule le vrai script Git push NOVA avec un faux Git et un faux jeton.

Aucune connexion réseau ni identité réelle; seuls les effets Git locaux
sont exercés dans un répertoire temporaire détruit automatiquement.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/nova-seo-normalize.yml"
STEP_MARKER = "      - name: Pousser uniquement le commit SEO autorisé\n"
SYNTHETIC_TOKEN = "SYNTHETIC-GITHUB-TOKEN-FOR-LOCAL-TEST-ONLY"


def extract_shell() -> str:
    data = WORKFLOW.read_text(encoding="utf-8", errors="strict")
    if data.count(STEP_MARKER) != 1:
        raise ValueError("Étape de push finale unique absente")
    raw = data.split(STEP_MARKER, 1)[1]
    if "        run: |\n" not in raw:
        raise ValueError("Script de push introuvable")
    raw = raw.split("        run: |\n", 1)[1]
    script_lines = []
    for line in raw.splitlines():
        if line and not line.startswith("          "):
            break
        script_lines.append(line[10:] if line.startswith("          ") else "")
    script = "\n".join(script_lines) + "\n"
    if len(script) > 12000 or "git -c credential.helper= push origin HEAD:nova-a1-reference-documents" not in script:
        raise ValueError("Périmètre script Git inattendu")
    if "SEO_PUSH_TOKEN:" not in data:
        raise ValueError("Variable du jeton final absente du workflow")
    return script


FAKE_GIT = r'''#!/usr/bin/env python3
import os, stat, subprocess, sys
from pathlib import Path

expected = ['-c','credential.helper=','push','origin','HEAD:nova-a1-reference-documents']
if sys.argv[1:] != expected:
    raise SystemExit('Commande Git non autorisée')
if os.environ.get('GIT_TERMINAL_PROMPT') != '0':
    raise SystemExit('Git interactif interdit')
ask = Path(os.environ['GIT_ASKPASS'])
if not ask.is_file() or stat.S_IMODE(ask.stat().st_mode) != 0o700:
    raise SystemExit('Fichier askpass absent ou permissions faibles')
if 'SYNTHETIC-GITHUB-TOKEN-FOR-LOCAL-TEST-ONLY' in ask.read_text(encoding='utf-8'):
    raise SystemExit('Le jeton a été écrit sur disque')
def answer(question):
    result = subprocess.run([str(ask),question],capture_output=True,text=True,check=True,timeout=5)
    return result.stdout.strip()
if answer('Username for https://github.com') != 'x-access-token':
    raise SystemExit('Identifiant Git incorrect')
if answer('Password for https://github.com') != os.environ['SEO_PUSH_TOKEN']:
    raise SystemExit('Jeton non transmis au push')
Path(os.environ['TEST_PROOF']).write_text('push-synthetique-autorise',encoding='utf-8')
'''


def run_test() -> None:
    script = extract_shell()
    with tempfile.TemporaryDirectory(prefix="sinjira-fake-git-") as root:
        directory = Path(root)
        exe_dir = directory / "bin"
        exe_dir.mkdir(mode=0o700)
        git = exe_dir / "git"
        git.write_text(FAKE_GIT, encoding="utf-8")
        git.chmod(0o700)
        proof = directory / "proof.txt"
        env = dict(os.environ)
        env["PATH"] = str(exe_dir) + os.pathsep + env.get("PATH", "")
        env["RUNNER_TEMP"] = str(directory)
        env["TEST_PROOF"] = str(proof)
        env["SEO_PUSH_TOKEN"] = SYNTHETIC_TOKEN
        success = subprocess.run(
            ["/bin/bash", "-euo", "pipefail", "-c", script],
            cwd=directory, env=env, capture_output=True, text=True, timeout=12,
            check=False,
        )
        assert success.returncode == 0, f"Échec test shell: {success.stderr[:350]}"
        assert proof.read_text(encoding="utf-8") == "push-synthetique-autorise"
        assert SYNTHETIC_TOKEN not in success.stdout + success.stderr
        assert not list(directory.glob("nova-seo-askpass.*")), "Fichier askpass non détruit"
        assert all(SYNTHETIC_TOKEN not in p.read_text(encoding="utf-8", errors="ignore")
                   for p in directory.glob("*") if p.is_file())

        proof.unlink()
        env.pop("SEO_PUSH_TOKEN", None)
        denied = subprocess.run(
            ["/bin/bash", "-euo", "pipefail", "-c", script],
            cwd=directory, env=env, capture_output=True, text=True, timeout=12,
            check=False,
        )
        assert denied.returncode != 0, "Push autorisé sans jeton"
        assert not proof.exists(), "Push effectué malgré le jeton absent"
        assert not list(directory.glob("nova-seo-askpass.*")), "Fuite askpass après refus"
    print("PASS : jeton de push synthétique non persisté, askpass nettoyé, jeton manquant refusé.")


if __name__ == "__main__":
    run_test()
