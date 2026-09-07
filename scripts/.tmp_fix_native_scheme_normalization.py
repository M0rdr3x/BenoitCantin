from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'mobile-native' / 'App.tsx'
VALIDATOR = ROOT / 'scripts' / 'validate_mobile_native_intent_routing_v25.py'
DOC = ROOT / 'mobile-native' / 'NATIVE_INTENT_ROUTING_V25.md'
TMP_SCRIPT = ROOT / 'scripts' / '.tmp_fix_native_scheme_normalization.py'
TMP_WORKFLOW = ROOT / '.github' / 'workflows' / 'tmp-fix-native-scheme-normalization.yml'

app = APP.read_text(encoding='utf-8')
old_app = r"""  if (url.startsWith('sinjira://')) {
    const relativePath = url.replace(/^sinjira:\/\//, '/');
    return `${ORIGIN}${relativePath}`;
  }
"""
new_app = r"""  if (/^sinjira:\/+/i.test(url)) {
    const relativePath = url.replace(/^sinjira:\/+/i, '/');
    return `${ORIGIN}${relativePath}`;
  }
"""
if app.count(old_app) != 1:
    raise SystemExit(f'bloc normalizeSinjiraUrl inattendu: {app.count(old_app)} occurrence(s)')
APP.write_text(app.replace(old_app, new_app), encoding='utf-8')

validator = VALIDATOR.read_text(encoding='utf-8')
if "import re\n" not in validator:
    validator = validator.replace('from pathlib import Path\nimport sys\n', 'from pathlib import Path\nimport re\nimport sys\n', 1)

marker = "# Le résolveur doit être situé dans navigateToUrl, avant le gate Registre.\n"
insert = r"""# Le schéma mobile doit accepter les formes URI natives usuelles sans produire un chemin //.
normalize_start = app.find('function normalizeSinjiraUrl(url: string | null): string | null {')
normalize_end = app.find('\nfunction shareableSinjiraUrl', normalize_start + 1) if normalize_start >= 0 else -1
if normalize_start < 0 or normalize_end < 0:
    errors.append('App.tsx: normalizeSinjiraUrl introuvable')
    normalize_block = ''
else:
    normalize_block = app[normalize_start:normalize_end]

require(normalize_block, r"if (/^sinjira:\/+/i.test(url)) {", 'normalizeSinjiraUrl')
require(normalize_block, r"url.replace(/^sinjira:\/+/i, '/')", 'normalizeSinjiraUrl')
forbid(normalize_block, "url.startsWith('sinjira://')", 'normalizeSinjiraUrl')
forbid(normalize_block, r"url.replace(/^sinjira:\/\//, '/')", 'normalizeSinjiraUrl')

for raw in [
    'sinjira:/compte/messages.html',
    'sinjira://compte/messages.html',
    'sinjira:///compte/messages.html',
]:
    relative = re.sub(r'^sinjira:/+', '/', raw, flags=re.IGNORECASE)
    if relative != '/compte/messages.html':
        errors.append(f'normalisation schéma sinjira invalide pour {raw}: {relative}')

"""
if 'Le schéma mobile doit accepter les formes URI natives usuelles' not in validator:
    if marker not in validator:
        raise SystemExit('marqueur validator introuvable')
    validator = validator.replace(marker, insert + marker, 1)
VALIDATOR.write_text(validator, encoding='utf-8')

doc = DOC.read_text(encoding='utf-8')
section = """

## Normalisation du schéma mobile `sinjira:`

Les intentions natives acceptent les formes URI usuelles à **une, deux ou trois barres** (`sinjira:/compte/...`, `sinjira://compte/...`, `sinjira:///compte/...`). Elles sont toutes ramenées à un seul chemin interne `/compte/...` avant la décision de routage. Cela évite qu’une URI triple-slash devienne accidentellement `//compte/...` et contourne le sas natif.

Cette normalisation ne rend aucune nouvelle route admissible : les mêmes listes fermées, exclusions sensibles et règles `?surface=web` continuent de s’appliquer après normalisation.
"""
if '## Normalisation du schéma mobile `sinjira:`' not in doc:
    doc = doc.rstrip() + section.rstrip() + '\n'
DOC.write_text(doc, encoding='utf-8')

for path in [TMP_SCRIPT, TMP_WORKFLOW]:
    if path.exists():
        path.unlink()
