#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read(path:str)->str:
    target=ROOT/path
    if not target.exists():
        raise AssertionError(f'Fichier absent: {path}')
    return target.read_text('utf-8',errors='ignore')


def require(text:str,markers:list[str],label:str)->None:
    missing=[marker for marker in markers if marker not in text]
    if missing:
        raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text:str,markers:list[str],label:str)->None:
    found=[marker for marker in markers if marker.lower() in text.lower()]
    if found:
        raise AssertionError(f'{label}: marqueurs interdits présents: {found}')


def main()->int:
    library_html=read('compte/bibliotheque.html')
    reads_html=read('compte/mes-lectures.html')
    demo_html=read('projets/sinjira/romans/lire-demo.html')
    library_js=read('assets/js/sinjira-library-v24-4-61.js')
    reads_js=read('assets/js/sinjira-reads-v24-4-61.js')
    progress_js=read('assets/js/sinjira-reader-progress-v24-4-61.js')

    # La bibliothèque V26 se répartit en 3 catégories Web distinctes.
    # Le contrat V24 des lectures/droits continue d'être validé sur ses
    # modules sources; il n'impose plus leur mélange sur l'accueil.
    require(library_html,[
        'data-library-page="hub-v26"',
        'sinjira-library-hub-v26.js?v=',
        'bibliotheque-romans.html',
        'bibliotheque-jeux.html',
        'bibliotheque-ressources.html',
        'liseuse.html?edition=integrale',
        'Le rôle propriétaire reste distinct des droits numériques attribués aux produits.'
    ],'bibliotheque.html')

    romans_html=read('compte/bibliotheque-romans.html')
    jeux_html=read('compte/bibliotheque-jeux.html')
    ressources_html=read('compte/bibliotheque-ressources.html')
    liseuse_html=read('compte/liseuse.html')
    require(romans_html,[
        'data-v18-page="reads-v24-4-61"',
        'data-reader-library',
        'sinjira-reads-v24-4-61.js?v=',
        'liseuse.html?edition=integrale',
        'liseuse.html?edition=demo',
    ],'bibliotheque-romans.html')
    require(jeux_html,['data-library-account-games','sinjira-library-hub-v26.js?v='],
            'bibliotheque-jeux.html')
    require(ressources_html,['documents.html','licences.html','playtests.html'],
            'bibliotheque-ressources.html')
    require(liseuse_html,[
        'noindex,nofollow,noarchive',
        'sinjira-liseuse-v26.js?v=',
        'reader-canvas','reader-text','reader-chapters'
    ],'liseuse.html')

    require(reads_html,[
        'data-v18-page="reads-v24-4-61"',
        'sinjira-reads-v24-4-61.js?v=24.4.61',
        'data-reader-library'
    ],'mes-lectures.html')

    require(library_js,[
        "from('projects')",
        "from('project_access')",
        "from('sinjira_reader_library')",
        "from('user_entitlements')",
        "rpc('is_sinjira_admin'",
        "rpc('is_sinjira_owner'",
        'Accès privé',
        'Inclus avec le compte'
    ],'sinjira-library-v24-4-61.js')

    require(reads_js,[
        "from('sinjira_novels')",
        "from('sinjira_reader_library')",
        'data-v2461-add-read',
        'data-v2461-remove-read',
        "onConflict:'user_id,novel_id'"
    ],'sinjira-reads-v24-4-61.js')
    forbid(reads_js,["from('novels')","from('reader_library')"],'sinjira-reads-v24-4-61.js')

    require(progress_js,[
        'getCurrentUser',
        "from('sinjira_novels')",
        "from('sinjira_reader_library')",
        "onConflict:'user_id,novel_id'"
    ],'sinjira-reader-progress-v24-4-61.js')

    require(demo_html,[
        'sinjira-reader.js?v=',
        'sinjira-reader-progress-v24-4-61.js?v='
    ],'lire-demo.html')
    if demo_html.index('sinjira-reader.js?v=') > demo_html.index('sinjira-reader-progress-v24-4-61.js?v='):
        raise AssertionError('lire-demo.html: le synchroniseur canonique doit être chargé après le lecteur existant.')

    paid_markers=['stripe','openai','anthropic','twilio','paypal','lemonsqueezy','paddle','replicate']
    for label,text in (
        ('sinjira-library-v24-4-61.js',library_js),
        ('sinjira-reads-v24-4-61.js',reads_js),
        ('sinjira-reader-progress-v24-4-61.js',progress_js),
    ):
        forbid(text,paid_markers,label)

    print('OK bibliothèque V24/V26: catégories distinctes, accès réels, romans canoniques, droits numériques et progression protégée.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
