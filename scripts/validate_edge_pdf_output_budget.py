#!/usr/bin/env python3
"""Security regression: never generate a disabled email PDF; bound PDF output.

Static markers are backed by Node runtime tests; no external request.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'supabase/functions/send-game-report/index.ts'
SHEET=ROOT/'supabase/functions/send-player-sheet/index.ts'
CAP='const MAX_GENERATED_PDF_BYTES=20*1024*1024;'
BOUND='output.byteLength===0||output.byteLength>MAX_GENERATED_PDF_BYTES'


def validate(report: str, sheet: str) -> list[str]:
    errors: list[str]=[]
    for name, source, fn in (
        ('send-game-report', report, 'async function buildPdf('),
        ('send-player-sheet', sheet, 'async function buildPlayerSheet('),
    ):
        start=source.find(fn)
        save=source.find('new Uint8Array(await pdf.save())',start)
        cap=source.find(BOUND,save)
        done=source.find('return output;',cap)
        if source.count(CAP)!=1 or not (start>=0 and start<save<cap<done):
            errors.append(name+': PDF final non borné après sérialisation')
        if 'response.arrayBuffer()' in source:
            errors.append(name+': modèle distant téléchargé intégralement')
        if 'fetchBoundedPdf(' not in source:
            errors.append(name+': modèle distant non borné en flux')
    mode=report.find("const mode = body?.mode === 'email' ? 'email' : 'download'")
    refuse=report.find("if (mode === 'email' && !PAID_EXTERNAL_SERVICES_ENABLED)")
    user=report.find('const user = await optionalUser(req)',mode)
    generate=report.find('const pdfBytes = await buildPdf(sheet)',mode)
    if not (mode>=0 and mode<refuse<user<generate):
        errors.append('send-game-report: email désactivé non rejeté avant accès/CPU PDF')
    if report.count('const PAID_EXTERNAL_SERVICES_ENABLED=false;')!=1:
        errors.append('send-game-report: transport externe non fermé')
    if sheet.count('const PAID_EXTERNAL_SERVICES_ENABLED=false;')!=1:
        errors.append('send-player-sheet: transport externe non fermé')
    return errors


def self_test(report: str, sheet: str) -> None:
    if validate(report,sheet):
        raise AssertionError('La version de référence doit réussir')
    mutants=[
        ('email appelé avant garde',report.replace(
            "if (mode === 'email' && !PAID_EXTERNAL_SERVICES_ENABLED)",
            "if (false)",1),sheet),
        ('garde email supprimé',report.replace(
            "if (mode === 'email' && !PAID_EXTERNAL_SERVICES_ENABLED)",
            "if (mode === 'download' && !PAID_EXTERNAL_SERVICES_ENABLED)",1),sheet),
        ('limite PDF public supprimée',report.replace(BOUND,'false',1),sheet),
        ('limite PDF privé supprimée',report,sheet.replace(BOUND,'false',1)),
        ('plafond public gonflé',report.replace(CAP,CAP.replace('20*','200*'),1),sheet),
        ('plafond privé gonflé',report,sheet.replace(CAP,CAP.replace('20*','200*'),1)),
        ('retour au téléchargement intégral',report.replace(
            'fetchBoundedPdf(reportTemplateUrl(),MAX_TEMPLATE_BYTES)',
            'response.arrayBuffer()',1),sheet),
        ('email fournisseur activé',report.replace(
            'const PAID_EXTERNAL_SERVICES_ENABLED=false;',
            'const PAID_EXTERNAL_SERVICES_ENABLED=true;',1),sheet),
    ]
    for label,r,s in mutants:
        if (r,s)==(report,sheet) or not validate(r,s):
            raise AssertionError('Mutation non rejetée: '+label)
    print('OK budget PDF: 8 mutations négatives rejetées')


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    try:
        report=REPORT.read_text('utf-8')
        sheet=SHEET.read_text('utf-8')
    except (OSError,UnicodeError):
        print('ECHEC: route PDF illisible')
        return 1
    errors=validate(report,sheet)
    if errors:
        for error in errors:
            print('ECHEC '+error)
        return 1
    if args.self_test:
        self_test(report,sheet)
    print('OK : 2 PDFs plafonnés à 20 Mio après sérialisation, email public bloqué avant CPU')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
