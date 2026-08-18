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

    require(library_html,[
        'data-library-page="library-v24-4-61"',
        'sinjira-library-v24-4-61.js?v=24.4.61',
        'data-library-reads',
        'data-library-entitlements',
        'Aucun achat ou service payant n’est activé actuellement.'
    ],'bibliotheque.html')

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

    require(demo_html,['sinjira-reader-progress-v24-4-61.js?v=24.4.61'],'lire-demo.html')
    if demo_html.index('sinjira-reader.js?v=19.0') > demo_html.index('sinjira-reader-progress-v24-4-61.js?v=24.4.61'):
        raise AssertionError('lire-demo.html: le synchroniseur canonique doit être chargé après le lecteur existant.')

    paid_markers=['stripe','openai','anthropic','twilio','paypal','lemonsqueezy','paddle','replicate']
    for label,text in (
        ('sinjira-library-v24-4-61.js',library_js),
        ('sinjira-reads-v24-4-61.js',reads_js),
        ('sinjira-reader-progress-v24-4-61.js',progress_js),
    ):
        forbid(text,paid_markers,label)

    print('OK bibliothèque V24.4.61: accès réels, romans canoniques, droits numériques et progression démo cohérents sans service payant.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
