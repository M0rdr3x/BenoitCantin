#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'
SIGNUP=ROOT/'assets'/'js'/'v24-signup.js'
HTML=ROOT/'compte'/'inscription.html'
RELATIONS_JS=ROOT/'assets'/'js'/'v24-relations.js'


def read(path:Path)->str:
    return path.read_text('utf-8',errors='ignore')


def all_sql()->str:
    return '\n'.join(read(p) for p in sorted(MIG.glob('*.sql')))


def latest_policy(sql:str,name:str)->str:
    matches=list(re.finditer(rf'create\s+policy\s+{re.escape(name)}\b.*?(?=\n\s*(?:drop\s+policy|create\s+policy|create\s+(?:or\s+replace\s+)?function|alter\s+table|revoke|grant|$))',sql,re.I|re.S))
    return matches[-1].group(0) if matches else ''


def function_block(sql:str,name:str)->str:
    matches=list(re.finditer(rf'create\s+(?:or\s+replace\s+)?function\s+public\.{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;',sql,re.I|re.S))
    return matches[-1].group(0) if matches else ''


def compact(value:str)->str:
    return re.sub(r'\s+','',value.lower())


def main()->int:
    errors=[]
    sql=all_sql()
    low=re.sub(r'\s+',' ',sql.lower())
    sql_compact=compact(sql)
    signup=read(SIGNUP)
    signup_compact=compact(signup)
    html=read(HTML)
    relations_js=read(RELATIONS_JS) if RELATIONS_JS.exists() else ''
    relations_compact=compact(relations_js)

    required_functions=[
        'sinjira_age_band','sinjira_my_age_band','sinjira_can_social_interact','sinjira_social_compatible',
        'sinjira_parent_can_supervise','get_guardian_youth_contacts',
        'create_guardian_signup_invite','redeem_guardian_signup_invite','revoke_guardian_link',
        'sinjira_mfa_access_allowed','sinjira_phone_factor_verified','enforce_sinjira_account_safety_age',
        'handle_new_sinjira_user'
    ]
    for name in required_functions:
        if not function_block(sql,name):
            errors.append(f'Fonction jeunesse/sécurité absente: {name}')

    age=function_block(sql,'sinjira_age_band').lower()
    for band in ['under12','youth','youth_pending','adult','unverified']:
        if f"'{band}'" not in age:
            errors.append(f'Cohorte canonique absente de sinjira_age_band: {band}')
    if "g.status='verified'" not in compact(age):
        errors.append('La cohorte youth ne dépend pas explicitement d’un tuteur vérifié.')
    if 'account_safety_profiles' not in age:
        errors.append('sinjira_age_band ne lit pas account_safety_profiles.')

    mine=function_block(sql,'sinjira_my_age_band').lower()
    if 'sinjira_age_band(auth.uid())' not in compact(mine):
        errors.append('sinjira_my_age_band ne retourne pas exclusivement la cohorte du compte courant.')
    if 'revokeexecuteonfunctionpublic.sinjira_age_band(uuid)fromauthenticated' not in sql_compact:
        errors.append('La RPC paramétrée sinjira_age_band(uuid) reste exposée aux membres authentifiés.')

    social=function_block(sql,'sinjira_can_social_interact').lower()
    social_compact=compact(social)
    if not social:
        errors.append('Fonction canonique de compatibilité sociale absente.')
    else:
        for marker in ["='adult'andpublic.sinjira_age_band(p_b)='adult'","='youth'andpublic.sinjira_age_band(p_b)='youth'"]:
            if marker not in social_compact:
                errors.append('sinjira_can_social_interact n’impose pas strictement adulte↔adulte et jeunesse vérifiée↔jeunesse vérifiée.')
                break
        if "p_a=p_bthenpublic.sinjira_age_band(p_a)in('adult','youth')" not in social_compact:
            errors.append('Un compte youth_pending/under12/unverified pourrait être traité comme socialement actif avec lui-même.')
        if "auth.uid()<>p_aandauth.uid()<>p_bthenfalse" not in social_compact:
            errors.append('sinjira_can_social_interact permet encore de tester deux UUID tiers sans implication du compte courant.')

    policy_names=[
        'real_messages_insert','char_messages_insert','real_messages_read','char_messages_read',
        'real_posts_read','char_posts_read','real_comments_read','char_comments_read',
        'real_likes_read','char_likes_read'
    ]
    for name in policy_names:
        block=latest_policy(sql,name).lower()
        if not block:
            errors.append(f'Politique sociale absente: {name}')
        elif 'sinjira_can_social_interact' not in block:
            errors.append(f'Politique {name} n’utilise pas la règle canonique de cohorte.')

    for name in ['real_posts_insert','char_posts_insert']:
        block=compact(latest_policy(sql,name))
        if not block:
            errors.append(f'Politique de publication absente: {name}')
        elif "sinjira_my_age_band()in('youth','adult')" not in block:
            errors.append(f'Politique {name} n’exclut pas explicitement youth_pending/under12/unverified via la RPC self-only.')

    parent=function_block(sql,'sinjira_parent_can_supervise').lower()
    parent_compact=compact(parent)
    for marker in ["sinjira_age_band(p_parent)='adult'","sinjira_age_band(p_child)='youth'","g.status='verified'","guardian_links"]:
        if marker not in parent_compact:
            errors.append('La supervision parentale n’exige pas adulte + jeune vérifié + guardian_links verified.')
            break

    contacts=function_block(sql,'get_guardian_youth_contacts').lower()
    if 'sinjira_parent_can_supervise' not in contacts:
        errors.append('RPC de supervision sans vérification du lien parent/tuteur.')
    forbidden_message_fields=['body','message_body','content','message_text','text_content']
    if any(re.search(rf'\b{re.escape(field)}\b',contacts) for field in forbidden_message_fields):
        errors.append('RPC de supervision parentale expose potentiellement le contenu des messages.')
    for required_meta in ['other_user_id','last_contact_at']:
        if required_meta not in contacts:
            errors.append(f'RPC parentale privée de métadonnée utile: {required_meta}')

    invite=function_block(sql,'create_guardian_signup_invite').lower()
    invite_compact=compact(invite)
    for marker in ["sinjira_age_band(auth.uid())<>'adult'","sinjira_mfa_access_allowed(auth.uid())","youth-"]:
        if marker not in invite_compact:
            errors.append('Création du code parental sans vérification adulte/MFA ou format de code attendu.')
            break
    redeem=compact(function_block(sql,'redeem_guardian_signup_invite'))
    for marker in ["youth_pending","invalid_or_expired_guardian_code","adult_guardian_required","used_at=now()","minor_user_id=uid"]:
        if marker not in redeem:
            errors.append(f'Consommation post-inscription du code parental incomplète: {marker}')
    revoke=compact(function_block(sql,'revoke_guardian_link'))
    if 'uidnotin(r.guardian_user_id,r.minor_user_id)' not in revoke or "status='revoked'" not in revoke:
        errors.append('Révocation du lien parental non limitée aux deux parties du lien.')
    if 'revokeinsert,update,delete,truncate,references,triggeronpublic.guardian_linksfromauthenticated' not in sql_compact:
        errors.append('guardian_links reste directement modifiable par le navigateur.')
    if "interval'7days'" not in sql_compact and "interval'7day'" not in sql_compact:
        errors.append('Expiration du code parental à 7 jours absente.')
    if 'used_at is null' not in low or 'minor_user_id' not in low:
        errors.append('Code parental sans consommation à usage unique traçable.')

    new_user=function_block(sql,'handle_new_sinjira_user')
    new_user_compact=compact(new_user)
    for marker in [
        "years<12thenraiseexception'sinjira_minimum_age_12'","years<14then",
        "guardian_authorization_required_under_14","invalid_or_expired_guardian_code",
        "guardian_links","birth_date","date_of_birth","gender","sex"
    ]:
        if marker not in new_user_compact:
            errors.append(f'Pont d’inscription serveur incomplet: {marker}')
    verified_guardian=re.search(
        r'insert\s+into\s+public\.guardian_links\s*\([^)]*status[^)]*\)\s*values\s*\([^;]*[\'\"]verified[\'\"]',
        new_user,re.I|re.S
    )
    if not verified_guardian:
        errors.append('Pont d’inscription serveur: guardian_links n’est pas créé en statut verified.')

    age_trigger=function_block(sql,'enforce_sinjira_account_safety_age').lower()
    age_trigger_compact=compact(age_trigger)
    for marker in ['sinjira_minimum_age_12','date_of_birth',"new.sexnotin('female','male')"]:
        if marker not in age_trigger_compact:
            errors.append(f'Verrou âge/sexe serveur incomplet: {marker}')
    if 'beforeinsertorupdateofdate_of_birth,sexonpublic.account_safety_profiles' not in sql_compact:
        errors.append('Trigger âge/sexe non branché à account_safety_profiles.')
    if 'revokeallonfunctionpublic.enforce_sinjira_account_safety_age()frompublic,anon,authenticated' not in sql_compact:
        errors.append('Fonction trigger âge/sexe encore exposée comme RPC.')

    for marker in [
        'revokeinsert,delete,updateonpublic.account_safety_profilesfromauthenticated',
        'grantselectonpublic.account_safety_profilestoauthenticated',
        'grantupdate(birthday_greeting_opt_in,real_life_to_fiction_opt_in,relationship_data_opt_in,public_birthday_opt_in,birthday_public_opt_in,relationship_status,relationship_status_updated_at)onpublic.account_safety_profilestoauthenticated'
    ]:
        if marker not in sql_compact:
            errors.append('Surface d’écriture account_safety_profiles trop large ou non explicitement restreinte.')
            break

    for marker in ['if(age<12)','if(age<14&&!guardiancode)','birth_date:birthdate','date_of_birth:birthdate','gender,','sex:legacysex','guardian_code:guardiancode']:
        if marker not in signup_compact:
            errors.append(f'Validation/pont inscription absent: {marker}')
    if not re.search(r"\[\s*['\"]Femme['\"]\s*,\s*['\"]Homme['\"]\s*\]\.includes\(gender\)",signup):
        errors.append('Validation inscription Femme/Homme absente ou affaiblie.')
    if 'name="birth_date"' not in html or 'required' not in html:
        errors.append('Date de naissance obligatoire absente de l’inscription.')
    if 'name="gender"' not in html or '<option value="Femme">Femme</option>' not in html or '<option value="Homme">Homme</option>' not in html:
        errors.append('Inscription sans choix strict Femme/Homme.')
    for stale in ['Non binaire','Préfère ne pas répondre']:
        if stale in html:
            errors.append(f'Option de profil non prévue encore visible: {stale}')
    if 'data-guardian-code' not in html or 'Code d’autorisation parentale' not in html:
        errors.append('Champ de code parental absent du formulaire d’inscription.')

    for marker in ["rpc('sinjira_my_age_band')","rpc('create_guardian_signup_invite')","rpc('redeem_guardian_signup_invite')","rpc('revoke_guardian_link')"]:
        if marker not in relations_compact:
            errors.append(f'Interface Relations & famille incomplète: {marker}')
    if "rpc('sinjira_age_band'" in relations_compact:
        errors.append('Interface Relations & famille appelle encore la RPC paramétrée sinjira_age_band(uuid).')
    if 'guardian_signup_invites' not in relations_js or 'guardian_links' not in relations_js:
        errors.append('Interface parentale sans état des codes/liens vérifiés.')
    if 'aucun contenu privé' not in relations_js.lower():
        errors.append('Interface parentale ne rappelle pas explicitement la non-lecture du contenu privé.')

    if errors:
        print(f'ECHEC sécurité jeunesse canonique: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK jeunesse: 12+, 12–13 avec autorisation parentale, youth_pending vérifiable après inscription, cohortes isolées, RPC self-only et supervision révocable sans contenu privé.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
