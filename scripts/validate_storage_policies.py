#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIGRATIONS=ROOT/'supabase'/'migrations'

REQUIRED_AVATAR_POLICIES={
    'select':'sinjira avatars select own',
    'insert':'sinjira avatars upload own',
    'update':'sinjira avatars update own',
    'delete':'sinjira avatars delete own',
}


def main()->int:
    errors=[]
    sql='\n'.join(p.read_text('utf-8',errors='ignore') for p in sorted(MIGRATIONS.glob('*.sql')))
    lower=sql.lower()

    if "'sinjira-avatars'" not in lower:
        errors.append("Bucket sinjira-avatars absent des migrations.")
    if "public=true" not in re.sub(r'\s+','',lower):
        errors.append("Le bucket avatar n'est pas explicitement public; avatarPublicUrl() dépend de ce contrat.")

    for command,policy in REQUIRED_AVATAR_POLICIES.items():
        policy_rx=re.compile(
            rf'create\s+policy\s+"{re.escape(policy)}"\s+on\s+storage\.objects.*?for\s+{command}\s+to\s+authenticated',
            re.I|re.S,
        )
        matches=list(policy_rx.finditer(sql))
        if not matches:
            errors.append(f"Politique avatar {command.upper()} absente: {policy}")
            continue
        block=matches[-1].group(0)
        if "bucket_id='sinjira-avatars'" not in re.sub(r'\s+','',block.lower()) and "bucket_id = 'sinjira-avatars'" not in block.lower():
            errors.append(f"Politique avatar {command.upper()} non limitée au bucket sinjira-avatars.")

    # Chaque politique doit limiter le premier segment du chemin à auth.uid().
    for policy in REQUIRED_AVATAR_POLICIES.values():
        start=lower.rfind(f'create policy "{policy}"')
        if start<0: continue
        block=lower[start:start+900]
        normalized=re.sub(r'\s+','',block)
        if "(storage.foldername(name))[1]=auth.uid()::text" not in normalized:
            errors.append(f"Politique avatar non cloisonnée au dossier de l'utilisateur: {policy}")

    account=(ROOT/'assets/js/sinjira-account.js').read_text('utf-8',errors='ignore')
    if 'canvas.width=512' not in account or 'canvas.height=512' not in account:
        errors.append('Le redimensionnement avatar 512 × 512 n’est plus garanti côté navigateur.')
    if "canvas.toBlob(resolve,'image/webp'" not in account:
        errors.append('La conversion WebP des avatars n’est plus garantie.')
    if "Math.min(image.naturalWidth,image.naturalHeight)" not in account:
        errors.append('Le recadrage carré centré des avatars n’est plus détecté.')

    if errors:
        print(f'ECHEC Storage/avatar: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK: avatar 512 × 512 WebP et politiques Storage SELECT/INSERT/UPDATE/DELETE cloisonnées par utilisateur.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
