#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/life-story-delivery/index.ts'
FIXED_LOG = "console.error('[life-story-delivery]', { code: 'LIFE_STORY_DELIVERY_FAILED' });"

REQUIRED = {
    'log d’échec à code fixe': FIXED_LOG,
    'réponse d’échec générique': 'return errorResponse(req, 500);',
    'réponse utilisateur générique': "return new Response('Ce lien de remise n est pas disponible.'",
    'réponse non cachable': "'Cache-Control': 'private, no-store, max-age=0'",
    'référent masqué': "'Referrer-Policy': 'no-referrer'",
    'requête bornée': 'const MAX_REQUEST_BYTES = 256;',
    'jeton strict 256 bits hex': '/^[a-f0-9]{64}$/',
}

FORBIDDEN = {
    'message d’exception brut': 'error.message',
    'conversion brute de l’erreur': 'String(error)',
    'sérialisation brute de l’erreur': 'JSON.stringify(error)',
    'objet erreur brut journalisé': "console.error('[life-story-delivery]', error)",
    'objet erreur brut journalisé double quote': 'console.error("[life-story-delivery]", error)',
    'stack brute journalisée': 'error.stack',
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text('utf-8', errors='ignore')
    except OSError as exc:
        return [f'Fonction life-story-delivery illisible: {exc}']

    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde life-story-delivery absent: {label}.')

    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde life-story-delivery violé: {label}.')

    delivery_logs = [
        line.strip()
        for line in source.splitlines()
        if 'console.' in line and '[life-story-delivery]' in line
    ]
    if delivery_logs != [FIXED_LOG]:
        errors.append('Le journal life-story-delivery doit contenir exactement un code fixe sans détail backend.')

    catch_pos = source.rfind('} catch')
    fixed_log_pos = source.find(FIXED_LOG)
    response_pos = source.rfind('return errorResponse(req, 500);')
    if catch_pos < 0 or fixed_log_pos < catch_pos or response_pos < fixed_log_pos:
        errors.append('Le catch final doit journaliser uniquement le code fixe puis retourner l’erreur générique 500.')

    return errors


def self_test() -> None:
    safe = """
const MAX_REQUEST_BYTES = 256;
const token = 'a';
const headers = {
  'Cache-Control': 'private, no-store, max-age=0',
  'Referrer-Policy': 'no-referrer',
};
function errorResponse(req, status = 404) {
  return new Response('Ce lien de remise n est pas disponible.', { status, headers });
}
Deno.serve(async (req) => {
  if (!/^[a-f0-9]{64}$/.test(token)) return errorResponse(req);
  try {
    return new Response('ok');
  } catch {
    console.error('[life-story-delivery]', { code: 'LIFE_STORY_DELIVERY_FAILED' });
    return errorResponse(req, 500);
  }
});
"""
    with TemporaryDirectory() as raw:
        path = Path(raw) / 'index.ts'
        path.write_text(safe, encoding='utf-8')
        clean = validate(path)
        if clean:
            raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

        mutations = {
            'message brut': safe.replace(
                '} catch {\n    console.error',
                '} catch (error) {\n    console.error',
            ).replace(
                FIXED_LOG,
                "console.error('[life-story-delivery]', error.message);",
            ),
            'objet brut': safe.replace(
                '} catch {\n    console.error',
                '} catch (error) {\n    console.error',
            ).replace(
                FIXED_LOG,
                "console.error('[life-story-delivery]', error);",
            ),
            'stack brute': safe.replace(
                '} catch {\n    console.error',
                '} catch (error) {\n    console.error',
            ).replace(
                FIXED_LOG,
                "console.error('[life-story-delivery]', error.stack);",
            ),
            'code fixe retiré': safe.replace(FIXED_LOG, "console.error('[life-story-delivery]');"),
            'réponse 500 retirée': safe.replace('return errorResponse(req, 500);', 'return errorResponse(req, 400);'),
            'no-store retiré': safe.replace("  'Cache-Control': 'private, no-store, max-age=0',\n", ''),
        }

        for label, mutated in mutations.items():
            if mutated == safe:
                raise AssertionError(f'Mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            detected = validate(path)
            if not detected:
                raise AssertionError(f'Régression non détectée: {label}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Bloque toute fuite de détail backend dans les logs de life-story-delivery.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print('OK auto-test life-story-delivery error security.')
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC life-story-delivery error security: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK life-story-delivery: logs backend sanitizés, réponse 500 générique et no-store préservé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
