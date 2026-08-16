#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'


def all_sql():
    return '\n'.join(p.read_text('utf-8',errors='ignore') for p in sorted(MIG.glob('*.sql')))


def latest_policy(sql,name):
    matches=list(re.finditer(rf'create\s+policy\s+{re.escape(name)}\b.*?(?=\n\s*(?:drop\s+policy|create\s+policy|create\s+(?:or\s+replace\s+)?function|alter\s+table|revoke|grant|$))',sql,re.I|re.S))
    return matches[-1].group(0) if matches else ''


def compact(s):
    return re.sub(r'\s+','',s.lower())


def main():
    sql=all_sql()
    errors=[]
    if re.search(r'c\.character_id\s*=\s*c\.character_id',sql,re.I):
        # Historical migrations may contain the old bug; require the latest policies to override it.
        pass

    checks={
      'char_posts_insert':('social_character_posts.character_id',True),
      'char_posts_update':('social_character_posts.character_id',True),
      'char_comments_insert':('social_character_comments.character_id',True),
      'char_comments_update':('social_character_comments.character_id',True),
      'char_likes_insert':('social_character_likes.character_id',True),
    }
    for policy,(target,needs_owner) in checks.items():
        block=latest_policy(sql,policy)
        low=compact(block)
        if not block:
            errors.append(f'Politique absente: {policy}')
            continue
        if 'c.character_id=c.character_id' in low:
            errors.append(f'{policy}: tautologie character_id détectée.')
        expected=f'c.character_id={target}'.lower()
        if expected not in low:
            errors.append(f'{policy}: le character_id exact de la ligne n’est pas vérifié.')
        if 'c.user_id=(selectauth.uid())' not in low:
            errors.append(f'{policy}: le personnage n’est pas relié explicitement au compte authentifié.')
        if "lower(coalesce(c.status,''))<>'archived'" not in low:
            errors.append(f'{policy}: un profil personnage archivé pourrait être utilisé.')

    for policy in ['char_posts_update','char_comments_update']:
        block=compact(latest_policy(sql,policy))
        if 'withcheck' not in block:
            errors.append(f'{policy}: WITH CHECK absent; le character_id pourrait être remplacé après insertion.')

    msg=compact(latest_policy(sql,'char_messages_insert'))
    for marker in [
      'c.character_id=social_character_messages.sender_character_id',
      'c.user_id=(selectauth.uid())',
      'c.character_id=social_character_messages.recipient_character_id',
      'c.user_id=social_character_messages.recipient_user_id'
    ]:
        # Les migrations historiques peuvent encore utiliser auth.uid() directement pour cette politique.
        if marker not in msg and marker.replace('(selectauth.uid())','auth.uid()') not in msg:
            errors.append('char_messages_insert: liaison expéditeur/destinataire personnage incomplète.')
            break

    if errors:
        print(f'ECHEC identité personnage RLS: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK identité personnage: publications, commentaires, likes et messages restent liés aux personnages exacts autorisés.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
