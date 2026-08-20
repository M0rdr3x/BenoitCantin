#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'
SIGNUP=ROOT/'assets'/'js'/'v24-signup.js'
HTML=ROOT/'compte'/'inscription.html'
RELATIONS_JS=ROOT/'assets'/'js'/'v24-relations.js'
CONTRACT_VERSION='24.4.83'


def read(path:Path)->str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text('utf-8',errors='ignore')


def all_sql()->str:
    return '\n'.join(read(p) for p in sorted(MIG.glob('*.sql')))


def latest_policy(sql:str,name:str)->str:
    matches=list(re.finditer(
        rf'create\s+policy\s+{re.escape(name)}\b.*?(?=\n\s*(?:drop\s+policy|create\s+policy|create\s+(?:or\s+replace\s+)?function|alter\s+table|revoke|grant|$))',
        sql,re.I|re.S
    ))
    return matches[-1].group(0) if matches else ''


def function_block(sql:str,name:str)->str:
    matches=list(re.finditer(
        rf'create\s+(?:or\s+replace\s+)?function\s+public\.{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;',
        sql,re.I|re.S
    ))
    return matches[-1].group(0) if matches else ''


def compact(value:str)->str:
    return re.sub(r'\s+','',value.lower())


def has_regex(text:str,pattern:str,flags:int=re.I|re.S)->bool:
    return re.search(pattern,text,flags) is not None


def add_error(errors:list[str],code:str,message:str)->None:
    errors.append(f'[{code}] {message}')


def main()->int:
    errors=[]
    try:
        sql=all_sql()
        signup=read(SIGNUP)
        html=read(HTML)
        relations_js=read(RELATIONS_JS)
    except FileNotFoundError as exc:
        missing=str(exc.args[0]) if exc.args else 'fichier inconnu'
        add_error(errors,'FILE_MISSING',f'Fichier contractuel absent: {missing}')
        sql=signup=html=relations_js=''

    low=re.sub(r'\s+',' ',sql.lower())
    sql_compact=compact(sql)
    relations_compact=compact(relations_js)

    # --- Contrat serveur canonique -------------------------------------------------
    required_functions=[
        'sinjira_age_band','sinjira_my_age_band','sinjira_can_social_interact','sinjira_social_compatible',
        'sinjira_parent_can_supervise','get_guardian_youth_contacts',
        'create_guardian_signup_invite','redeem_guardian_signup_invite','revoke_guardian_link',
        'sinjira_mfa_access_allowed','sinjira_phone_factor_verified','enforce_sinjira_account_safety_age',
        'handle_new_sinjira_user'
    ]
    for name in required_functions:
        if not function_block(sql,name):
            add_error(errors,'RPC_MISSING',f'Fonction jeunesse/sécurité absente: {name}')

    age=function_block(sql,'sinjira_age_band').lower()
    # `under12` reste un état défensif historique même si l'inscription V83 refuse maintenant <13 ans.
    for band in ['under12','youth','youth_pending','adult','unverified']:
        if f"'{band}'" not in age:
            add_error(errors,'AGE_BAND',f'Cohorte canonique absente de sinjira_age_band: {band}')
    if "g.status='verified'" not in compact(age):
        add_error(errors,'AGE_BAND','La cohorte youth ne dépend pas explicitement d’un tuteur vérifié.')
    if 'account_safety_profiles' not in age:
        add_error(errors,'AGE_BAND','sinjira_age_band ne lit pas account_safety_profiles.')

    mine=function_block(sql,'sinjira_my_age_band').lower()
    if 'sinjira_age_band(auth.uid())' not in compact(mine):
        add_error(errors,'SELF_ONLY','sinjira_my_age_band ne retourne pas exclusivement la cohorte du compte courant.')
    if 'revokeexecuteonfunctionpublic.sinjira_age_band(uuid)fromauthenticated' not in sql_compact:
        add_error(errors,'SELF_ONLY','La RPC paramétrée sinjira_age_band(uuid) reste exposée aux membres authentifiés.')

    social=function_block(sql,'sinjira_can_social_interact').lower()
    social_compact=compact(social)
    if not social:
        add_error(errors,'SOCIAL_RULE','Fonction canonique de compatibilité sociale absente.')
    else:
        strict_pairs=[
            "='adult'andpublic.sinjira_age_band(p_b)='adult'",
            "='youth'andpublic.sinjira_age_band(p_b)='youth'"
        ]
        if not all(marker in social_compact for marker in strict_pairs):
            add_error(errors,'SOCIAL_RULE','sinjira_can_social_interact n’impose pas strictement adulte↔adulte et jeunesse vérifiée↔jeunesse vérifiée.')
        if "p_a=p_bthenpublic.sinjira_age_band(p_a)in('adult','youth')" not in social_compact:
            add_error(errors,'SOCIAL_RULE','Un compte youth_pending/under12/unverified pourrait être traité comme socialement actif avec lui-même.')
        if "auth.uid()<>p_aandauth.uid()<>p_bthenfalse" not in social_compact:
            add_error(errors,'SOCIAL_PRIVACY','sinjira_can_social_interact permet encore de tester deux UUID tiers sans implication du compte courant.')

    policy_names=[
        'real_messages_insert','char_messages_insert','real_messages_read','char_messages_read',
        'real_posts_read','char_posts_read','real_comments_read','char_comments_read',
        'real_likes_read','char_likes_read'
    ]
    for name in policy_names:
        block=latest_policy(sql,name).lower()
        if not block:
            add_error(errors,'RLS_MISSING',f'Politique sociale absente: {name}')
        elif 'sinjira_can_social_interact' not in block:
            add_error(errors,'RLS_COHORT',f'Politique {name} n’utilise pas la règle canonique de cohorte.')

    for name in ['real_posts_insert','char_posts_insert']:
        block=compact(latest_policy(sql,name))
        if not block:
            add_error(errors,'RLS_MISSING',f'Politique de publication absente: {name}')
        elif "sinjira_my_age_band()in('youth','adult')" not in block:
            add_error(errors,'RLS_WRITE',f'Politique {name} n’exclut pas explicitement youth_pending/under12/unverified via la RPC self-only.')

    parent=function_block(sql,'sinjira_parent_can_supervise').lower()
    parent_compact=compact(parent)
    parent_markers=[
        "sinjira_age_band(p_parent)='adult'",
        "sinjira_age_band(p_child)='youth'",
        "g.status='verified'",
        'guardian_links'
    ]
    if not all(marker in parent_compact for marker in parent_markers):
        add_error(errors,'GUARDIAN_RULE','La supervision parentale n’exige pas adulte + jeune vérifié + guardian_links verified.')

    contacts=function_block(sql,'get_guardian_youth_contacts').lower()
    if 'sinjira_parent_can_supervise' not in contacts:
        add_error(errors,'GUARDIAN_PRIVACY','RPC de supervision sans vérification du lien parent/tuteur.')
    forbidden_message_fields=['body','message_body','content','message_text','text_content']
    if any(re.search(rf'\b{re.escape(field)}\b',contacts) for field in forbidden_message_fields):
        add_error(errors,'GUARDIAN_PRIVACY','RPC de supervision parentale expose potentiellement le contenu des messages.')
    for required_meta in ['other_user_id','last_contact_at']:
        if required_meta not in contacts:
            add_error(errors,'GUARDIAN_METADATA',f'RPC parentale privée de métadonnée utile: {required_meta}')

    invite=function_block(sql,'create_guardian_signup_invite').lower()
    invite_compact=compact(invite)
    invite_markers=["sinjira_age_band(auth.uid())<>'adult'","sinjira_mfa_access_allowed(auth.uid())","youth-"]
    if not all(marker in invite_compact for marker in invite_markers):
        add_error(errors,'GUARDIAN_INVITE','Création du code parental sans vérification adulte/MFA ou format de code attendu.')

    redeem=compact(function_block(sql,'redeem_guardian_signup_invite'))
    for marker in ["youth_pending","invalid_or_expired_guardian_code","adult_guardian_required","used_at=now()","minor_user_id=uid"]:
        if marker not in redeem:
            add_error(errors,'GUARDIAN_REDEEM',f'Consommation post-inscription du code parental incomplète: {marker}')

    revoke=compact(function_block(sql,'revoke_guardian_link'))
    if 'uidnotin(r.guardian_user_id,r.minor_user_id)' not in revoke or "status='revoked'" not in revoke:
        add_error(errors,'GUARDIAN_REVOKE','Révocation du lien parental non limitée aux deux parties du lien.')
    if 'revokeinsert,update,delete,truncate,references,triggeronpublic.guardian_linksfromauthenticated' not in sql_compact:
        add_error(errors,'GUARDIAN_RLS','guardian_links reste directement modifiable par le navigateur.')
    if "interval'7days'" not in sql_compact and "interval'7day'" not in sql_compact:
        add_error(errors,'GUARDIAN_EXPIRY','Expiration du code parental à 7 jours absente.')
    if 'used_at is null' not in low or 'minor_user_id' not in low:
        add_error(errors,'GUARDIAN_USAGE','Code parental sans consommation à usage unique traçable.')

    # --- Pont Auth -> profil sécurité V24.4.83 -------------------------------------
    new_user=function_block(sql,'handle_new_sinjira_user')
    new_user_compact=compact(new_user)
    bridge_markers=[
        "years<13thenraiseexception'sinjira_minimum_age_13'","years<14then",
        'guardian_authorization_required_under_14','invalid_or_expired_guardian_code',
        'youth_jurisdiction_not_enabled','residence_country',
        'guardian_links','birth_date','date_of_birth','gender','sex'
    ]
    for marker in bridge_markers:
        if marker not in new_user_compact:
            add_error(errors,'AUTH_BRIDGE',f'Pont d’inscription serveur incomplet: {marker}')

    verified_guardian=re.search(
        r'insert\s+into\s+public\.guardian_links\s*\([^)]*status[^)]*\)\s*values\s*\([^;]*[\'\"]verified[\'\"]',
        new_user,re.I|re.S
    )
    if not verified_guardian:
        add_error(errors,'AUTH_BRIDGE','Pont d’inscription serveur: guardian_links n’est pas créé en statut verified.')

    age_trigger=function_block(sql,'enforce_sinjira_account_safety_age').lower()
    age_trigger_compact=compact(age_trigger)
    trigger_markers=['sinjira_minimum_age_13','date_of_birth',"new.sexnotin('female','male')"]
    for marker in trigger_markers:
        if marker not in age_trigger_compact:
            add_error(errors,'AGE_TRIGGER',f'Verrou âge/sexe serveur incomplet: {marker}')
    if 'beforeinsertorupdateofdate_of_birth,sexonpublic.account_safety_profiles' not in sql_compact:
        add_error(errors,'AGE_TRIGGER','Trigger âge/sexe non branché à account_safety_profiles.')
    if 'revokeallonfunctionpublic.enforce_sinjira_account_safety_age()frompublic,anon,authenticated' not in sql_compact:
        add_error(errors,'AGE_TRIGGER','Fonction trigger âge/sexe encore exposée comme RPC.')

    profile_write_markers=[
        'revokeinsert,delete,updateonpublic.account_safety_profilesfromauthenticated',
        'grantselectonpublic.account_safety_profilestoauthenticated',
        'grantupdate(birthday_greeting_opt_in,real_life_to_fiction_opt_in,relationship_data_opt_in,public_birthday_opt_in,birthday_public_opt_in,relationship_status,relationship_status_updated_at)onpublic.account_safety_profilestoauthenticated'
    ]
    if not all(marker in sql_compact for marker in profile_write_markers):
        add_error(errors,'PROFILE_WRITE','Surface d’écriture account_safety_profiles trop large ou non explicitement restreinte.')

    # --- Contrat frontend V24.4.83 -------------------------------------------------
    frontend_checks=[
        (r'if\s*\(\s*age\s*<\s*13\s*\)', 'SIGNUP_AGE_MIN', 'Validation frontend 13+ absente.'),
        (r'if\s*\(\s*age\s*>\s*120\s*\)', 'SIGNUP_AGE_MAX', 'Validation frontend de date de naissance irréaliste absente.'),
        (r'if\s*\(\s*age\s*<\s*14\s*&&\s*!\s*guardianCode\s*\)', 'SIGNUP_GUARDIAN', 'Code parental obligatoire à 13 ans non vérifié côté interface.'),
        (r'age\s*<\s*18\s*&&\s*!\s*isCanada\(\s*residenceCountry\s*\)', 'SIGNUP_JURISDICTION', 'Gate jeunesse Canada absent du frontend.'),
        (r'birth_date\s*:\s*birthDate\b', 'SIGNUP_METADATA', 'birth_date n’est pas transmis dans les métadonnées Auth.'),
        (r'date_of_birth\s*:\s*birthDate\b', 'SIGNUP_METADATA', 'date_of_birth n’est pas transmis dans les métadonnées Auth.'),
        (r'gender\s*,', 'SIGNUP_METADATA', 'gender n’est pas transmis dans les métadonnées Auth.'),
        (r'sex\s*:\s*legacySex\b', 'SIGNUP_METADATA', 'sex normalisé n’est pas transmis dans les métadonnées Auth.'),
        (r'guardian_code\s*:\s*guardianCode\b', 'SIGNUP_METADATA', 'guardian_code n’est pas transmis dans les métadonnées Auth.'),
        (r'residence_country\s*:\s*residenceCountry\b', 'SIGNUP_METADATA', 'pays de résidence n’est pas transmis au gate serveur.'),
        (r'GUARDIAN_CODE_RE\s*=\s*/\^YOUTH-\[A-Z0-9\]\{10\}\$/', 'SIGNUP_GUARDIAN', 'Format strict YOUTH-XXXXXXXXXX absent du frontend.')
    ]
    for pattern,code,message in frontend_checks:
        if not has_regex(signup,pattern):
            add_error(errors,code,message)

    if not has_regex(signup,r"\[\s*['\"]Femme['\"]\s*,\s*['\"]Homme['\"]\s*\]\.includes\(\s*gender\s*\)"):
        add_error(errors,'SIGNUP_SEX','Validation inscription Femme/Homme absente ou affaiblie.')

    if not has_regex(signup,r'age\s*>=\s*13\s*&&\s*age\s*<\s*18'):
        add_error(errors,'SIGNUP_GUARDIAN','La plage jeunesse 13–17 n’est pas utilisée pour afficher les contrôles parentaux.')
    if not has_regex(signup,r'age\s*>=\s*13\s*&&\s*age\s*<\s*14'):
        add_error(errors,'SIGNUP_GUARDIAN','La plage de 13 ans n’est pas utilisée pour rendre le code parental obligatoire.')

    # --- HTML d’inscription ---------------------------------------------------------
    if 'name="birth_date"' not in html or not has_regex(html,r'<input[^>]+name="birth_date"[^>]+required',re.I|re.S):
        add_error(errors,'SIGNUP_HTML','Date de naissance obligatoire absente de l’inscription.')
    if 'name="gender"' not in html:
        add_error(errors,'SIGNUP_HTML','Champ Femme/Homme absent de l’inscription.')
    for value in ['Femme','Homme']:
        if f'<option value="{value}">{value}</option>' not in html:
            add_error(errors,'SIGNUP_HTML',f'Option {value} absente de l’inscription.')
    for stale in ['Non binaire','Préfère ne pas répondre']:
        if stale in html:
            add_error(errors,'SIGNUP_HTML',f'Option de profil non prévue encore visible: {stale}')
    if 'data-guardian-code' not in html or 'Code d’autorisation parentale' not in html:
        add_error(errors,'SIGNUP_HTML','Champ de code parental absent du formulaire d’inscription.')
    if '13 à 17 ans' not in html or 'Canada' not in html:
        add_error(errors,'SIGNUP_HTML','Le gate jeunesse Canada n’est pas expliqué dans le formulaire.')

    # --- Interface Relations & famille ---------------------------------------------
    for marker in ["rpc('sinjira_my_age_band'","rpc('create_guardian_signup_invite'","rpc('redeem_guardian_signup_invite'","rpc('revoke_guardian_link'"]:
        if marker not in relations_compact:
            add_error(errors,'RELATIONS_UI',f'Interface Relations & famille incomplète: {marker}')
    if "rpc('sinjira_age_band'" in relations_compact:
        add_error(errors,'RELATIONS_PRIVACY','Interface Relations & famille appelle encore la RPC paramétrée sinjira_age_band(uuid).')
    if 'guardian_signup_invites' not in relations_js or 'guardian_links' not in relations_js:
        add_error(errors,'RELATIONS_UI','Interface parentale sans état des codes/liens vérifiés.')
    if 'aucun contenu privé' not in relations_js.lower():
        add_error(errors,'RELATIONS_PRIVACY','Interface parentale ne rappelle pas explicitement la non-lecture du contenu privé.')

    print(f'Contrat jeunesse SINJIRA V{CONTRACT_VERSION}: validation comportementale frontend + invariants serveur/RLS.')
    if errors:
        print(f'ECHEC sécurité jeunesse canonique: {len(errors)} problème(s).')
        for item in errors:
            safe=item.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
            print(f'::error title=Sécurité jeunesse SINJIRA::{safe}')
            print('- '+item)
        return 1

    print('OK jeunesse: inscription 13+, autorisation parentale à 13 ans, jeunesse 13–17 limitée au Canada, youth_pending vérifiable, cohortes isolées, RPC self-only et supervision révocable sans contenu privé.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
