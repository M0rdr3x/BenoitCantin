#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/send-game-report/index.ts'

REQUIRED = {
    'POST uniquement': "req.method !== 'POST'",
    'normalisation MIME exacte': ".split(';',1)[0].trim().toLowerCase()",
    'JSON exact': "contentType!=='application/json'",
    'lecture bornée par flux': 'req.body?.getReader()',
    'annulation au dépassement': 'reader.cancel()',
    'décodage UTF-8 strict': "new TextDecoder('utf-8',{fatal:true})",
    'réponse privée': "'Cache-Control': 'private, no-store, max-age=0'",
    'protection MIME': "'X-Content-Type-Options': 'nosniff'",
    'référent masqué': "'Referrer-Policy': 'no-referrer'",
    'champs fiche allowlistés': 'const TEXT_FIELDS = new Set([',
    'texte fiche borné': 'const MAX_TEXT = 6000;',
    'modèle PDF origine fixe': "const TEMPLATE_ORIGIN='https://www.benoitcantin.com';",
    'redirections modèle refusées': "redirect:'error'",
    'taille modèle bornée': 'const MAX_TEMPLATE_BYTES=15*1024*1024;',
    'signature PDF vérifiée': "!=='%PDF-'",
    'services payants désactivés': 'const PAID_EXTERNAL_SERVICES_ENABLED=false;',
    'courriel uniquement au compte': 'to: [user.email]',
    'log livraison fixe': "console.warn('[SINJIRA report]', { code:'REPORT_DELIVERY_RECORD_FAILED' });",
    'log fournisseur fixe': "console.error('[SINJIRA report]', { code:'REPORT_EMAIL_PROVIDER_FAILED', status:resendResponse.status });",
    'log erreur globale fixe': "console.error('[SINJIRA report]', { code:'SEND_GAME_REPORT_FAILED' });",
}

REQUIRED_PATTERNS = {
    'requête bornée exactement à 220000 octets': re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*220_?000\s*;'),
}

FORBIDDEN = {
    'JSON direct non borné': 'await req.json()',
    'texte intégral avant borne': 'await req.text()',
    'MIME JSON par préfixe': "startsWith('application/json')",
    'message erreur backend brut': 'error.message',
    'stack erreur brute': 'error.stack',
    'objet erreur brut console.error': 'console.error(error)',
    'objet erreur court brut': 'console.error(e)',
    'réponse fournisseur brute': 'await resendResponse.text()',
    'log fournisseur brut': "console.error('Resend:'",
    'activation service payant': 'PAID_EXTERNAL_SERVICES_ENABLED=true',
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text('utf-8', errors='ignore')
    except OSError as exc:
        return [f'send-game-report illisible: {exc}']

    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde send-game-report absent: {label}.')
    for label, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(source):
            errors.append(f'Garde send-game-report absent ou affaibli: {label}.')
    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde send-game-report violé: {label}.')

    paid_pos = source.find('if (!PAID_EXTERNAL_SERVICES_ENABLED)')
    resend_pos = source.find("fetch('https://api.resend.com/emails'")
    auth_email_pos = source.find('if (!user?.email)')
    if paid_pos < 0 or auth_email_pos < paid_pos or resend_pos < auth_email_pos:
        errors.append('Le transport courriel doit rester désactivé par défaut puis exiger le compte avant tout appel fournisseur.')

    parse_pos = source.find('const parsed = await readLimitedJson(req)')
    build_pos = source.find('const pdfBytes = await buildPdf(sheet)')
    if parse_pos < 0 or build_pos < 0 or parse_pos > build_pos:
        errors.append('Le corps doit être validé avant la génération PDF.')

    report_logs = [line.strip() for line in source.splitlines() if '[SINJIRA report]' in line and 'console.' in line]
    expected_logs = [
        "if (error) console.warn('[SINJIRA report]', { code:'REPORT_DELIVERY_RECORD_FAILED' });",
        "console.error('[SINJIRA report]', { code:'REPORT_EMAIL_PROVIDER_FAILED', status:resendResponse.status });",
        "console.error('[SINJIRA report]', { code:'SEND_GAME_REPORT_FAILED' });",
    ]
    if report_logs != expected_logs:
        errors.append('Les logs send-game-report doivent rester limités aux trois codes fixes approuvés.')

    return errors


def self_test() -> None:
    safe = """
const FUNCTION_VERSION='24.5.2';
const MAX_REQUEST_BYTES=220_000;
const MAX_TEMPLATE_BYTES=15*1024*1024;
const MAX_TEXT = 6000;
const PAID_EXTERNAL_SERVICES_ENABLED=false;
const TEMPLATE_ORIGIN='https://www.benoitcantin.com';
const TEXT_FIELDS = new Set(['notes_privees']);
const PRIVATE_JSON_HEADERS = {
  'Cache-Control': 'private, no-store, max-age=0',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer'
};
async function fetchTemplateBytes(){
 const response=await fetch('https://www.benoitcantin.com/x.pdf',{cache:'no-store',redirect:'error'});
 const bytes=new Uint8Array(await response.arrayBuffer());
 if(bytes.length<5||String.fromCharCode(...bytes.subarray(0,5))!=='%PDF-') throw new Error('REPORT_TEMPLATE_NOT_PDF');
 return bytes;
}
async function readLimitedJson(req){
 const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
 if(contentType!=='application/json') return {response:new Response('',{status:415})};
 const reader=req.body?.getReader();
 if(!reader)return {body:{}};
 const chunks=[]; let total=0;
 while(true){
  const {done,value}=await reader.read(); if(done)break; if(!value)continue;
  total+=value.byteLength;
  if(total>MAX_REQUEST_BYTES){try{await reader.cancel()}catch{} return {response:new Response('',{status:413})}}
  chunks.push(value);
 }
 const bytes=new Uint8Array(total); let offset=0;
 for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength}
 const raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
 return {body:JSON.parse(raw||'{}')};
}
async function recordDelivery(){
 const error=false;
 if (error) console.warn('[SINJIRA report]', { code:'REPORT_DELIVERY_RECORD_FAILED' });
}
Deno.serve(async(req)=>{
 if (req.method !== 'POST') return new Response('',{status:405});
 try {
  const parsed = await readLimitedJson(req);
  const body=parsed.body||{};
  const user={email:'x@example.test'};
  const sheet={};
  const pdfBytes = await buildPdf(sheet);
  if (!PAID_EXTERNAL_SERVICES_ENABLED) return new Response('',{status:503});
  if (!user?.email) return new Response('',{status:401});
  const resendResponse=await fetch('https://api.resend.com/emails',{method:'POST',body:JSON.stringify({to: [user.email]})});
  if(!resendResponse.ok){
   console.error('[SINJIRA report]', { code:'REPORT_EMAIL_PROVIDER_FAILED', status:resendResponse.status });
   return new Response('',{status:502});
  }
  return new Response(String(pdfBytes.byteLength));
 } catch {
  console.error('[SINJIRA report]', { code:'SEND_GAME_REPORT_FAILED' });
  return new Response('',{status:500});
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
            'MIME JSON par préfixe': safe.replace("if(contentType!=='application/json')", "if(!contentType.startsWith('application/json'))"),
            'req.text intégral': safe.replace(' const reader=req.body?.getReader();', ' const raw=await req.text();'),
            'req.json direct': safe.replace(' const reader=req.body?.getReader();', ' const bodyDirect = await req.json();'),
            'annulation retirée': safe.replace('try{await reader.cancel()}catch{} ', ''),
            'no-store retiré': safe.replace("  'Cache-Control': 'private, no-store, max-age=0',\n", ''),
            'services payants activés': safe.replace('PAID_EXTERNAL_SERVICES_ENABLED=false', 'PAID_EXTERNAL_SERVICES_ENABLED=true'),
            'log livraison brut': safe.replace("console.warn('[SINJIRA report]', { code:'REPORT_DELIVERY_RECORD_FAILED' });", "console.warn('[SINJIRA report]', error.message);"),
            'réponse fournisseur lue': safe.replace("console.error('[SINJIRA report]', { code:'REPORT_EMAIL_PROVIDER_FAILED', status:resendResponse.status });", "const details=await resendResponse.text(); console.error('Resend:',details);"),
            'catch brut': safe.replace("} catch {\n  console.error('[SINJIRA report]', { code:'SEND_GAME_REPORT_FAILED' });", "} catch (error) {\n  console.error(error);"),
            'limite augmentée': safe.replace('MAX_REQUEST_BYTES=220_000;', 'MAX_REQUEST_BYTES=2_200_000;'),
            'destinataire arbitraire': safe.replace('to: [user.email]', 'to: [body.email]'),
        }
        for label, mutated in mutations.items():
            if mutated == safe:
                raise AssertionError(f'Mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Régression non détectée: {label}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la frontière publique et les logs de send-game-report.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('OK auto-test send-game-report security.')
        return 0
    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC send-game-report: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK send-game-report: POST JSON exact borné pendant la lecture, réponses no-store, PDF validé, transport payant désactivé et logs backend sanitizés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
