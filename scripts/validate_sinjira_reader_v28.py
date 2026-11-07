#!/usr/bin/env python3
"""Contrat V28: lecture locale, repères privés, RLS et aucune fuite du Livre I."""
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class ElementIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=set()
    def handle_starttag(self, tag, attrs):
        id_=dict(attrs).get('id')
        if id_: self.ids.add(id_)

def validate_private_session_lifecycle(source: str) -> list[str]:
    """Contrat de fermeture : aucune note ou page asynchrone après déconnexion."""
    errors: list[str] = []
    required = {
        "état de session fermé": "closed:false",
        "verrou sur la lecture": "const isReady=()=>!state.closed&&Boolean(getPdf());",
        "annulation avant/après chargement de chapitre": (
            "if(!state.continuous||token!==state.chapterToken||!isReady())return;"
        ),
        "réponse asynchrone associée au compte": (
            "if(!isReady()||getUser()?.id!==user.id||getNovelId()!==novelId)return;"
        ),
        "recherche abandonnée après fermeture": (
            "if(version!==state.searchVersion||!isReady())break;"
        ),
    }
    for name, token in required.items():
        expected = 3 if "réponse asynchrone" in name or "annulation avant" in name else (
            2 if "recherche abandonnée" in name else 1
        )
        if source.count(token) < expected:
            errors.append("Isolation privée liseuse absente: " + name)
    def segment(start: str, end: str) -> str:
        if start not in source or end not in source:
            return ""
        return source.split(start, 1)[1].split(end, 1)[0]
    close = segment("    close(){", "\n    },")
    for label, token in {
        "fermeture irréversible": "state.closed=true",
        "recherches invalidées": "state.searchVersion++",
        "chapitres invalidés": "state.chapterToken++",
        "effacement des notes": "state.marks=[]",
        "effacement du texte continu": "chapter.replaceChildren()",
        "effacement des résultats": "'reader-search-results').replaceChildren()",
        "effacement des champs privés": "'reader-note-input').value=''",
    }.items():
        if token not in close:
            errors.append("Nettoyage de session liseuse absent: " + label)
    for name, start, end in (
        ("récupération des notes", "  async function loadMarks(){", "  async function addMark("),
        ("création de note", "  async function addMark(", "  async function deleteMark("),
        ("suppression de note", "  async function deleteMark(", "  function renderMarks()"),
    ):
        if "if(!isReady()||getUser()?.id!==user.id||getNovelId()!==novelId)return;" not in segment(start, end):
            errors.append("Résultat RLS asynchrone non invalidé: " + name)
    return errors


def validate():
    errors=[]
    html=(ROOT/'compte/liseuse.html').read_text('utf-8')
    ui=ElementIds();ui.feed(html)
    required=[
        'reader-focus','reader-reading-stats','reader-chapter-next',
        'reader-continuous','reader-chapter-scroll',
        'reader-bookmark-add','reader-highlight-save','reader-note-input',
        'reader-note-save','reader-selection-preview','reader-marks-list',
        'reader-marks-status','reader-search-field','reader-search-submit',
        'reader-search-cancel','reader-search-status','reader-search-results'
    ]
    errors.extend('Commande manquante: '+name for name in required if name not in ui.ids)
    main=(ROOT/'assets/js/sinjira-liseuse-v26.js').read_text('utf-8')
    companion=(ROOT/'assets/js/sinjira-liseuse-companion-v28.mjs').read_text('utf-8')
    errors.extend(validate_private_session_lifecycle(companion))
    ddl=(ROOT/'supabase/migrations/20261107120000_sinjira_reader_marks_v28.sql').read_text('utf-8')
    for needle in ['createReaderCompanion(', 'get-novel-file-url', 'resolvePrivateUrl',
                   'SIGNED_ORIGIN', 'getTextAtPage:', 'sinjira_reader_library',
                   'setReadingPageFromScroll', 'invalidateRender:']:
        if needle not in main:errors.append('Mécanisme principal absent: '+needle)
    for needle in ['sinjira_reader_marks','createReaderCompanion(', 'findMatches(',
                   'getTextAtPage(', 'document.createTextNode', 'textContent',
                   'state.searchVersion','isFull','reader-bookmark-add',
                   'reader-focus','reader-reading-stats','user_id',
                   'startContinuous(', 'exitContinuous(', 'onContinuousScroll(']:
        if needle not in companion:errors.append('Mécanisme complémentaire absent: '+needle)
    # Empêcher le stockage de texte intégral (citations ou notes) en localStorage.
    if 'localStorage.setItem(DEMO_MARKS_KEY' not in companion:
        errors.append('Enregistrement de la démo non isolé')
    if 'if(isFull)return;' not in companion:
        errors.append('Absence de garde-fou contre la sauvegarde locale intégrale')
    if 'window.localStorage' in companion or 'innerHTML' in companion:
        errors.append('Stockage ou injection HTML à auditer')
    for token in [
        'alter table public.sinjira_reader_marks enable row level security',
        'revoke all on table public.sinjira_reader_marks from public, anon',
        'to authenticated using (user_id = (select auth.uid()))',
        'to authenticated with check (user_id = (select auth.uid()))',
        'with check (user_id = (select auth.uid()))',
        'for select','for insert','for update','for delete',
        'char_length(quote) <= 280','char_length(note) <= 1500',
        'create unique index if not exists sinjira_reader_marks_one_bookmark_per_page',
    ]:
        if token not in ddl:errors.append('Garde-fou RLS manquant: '+token)
    for secret in ['SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf',
                   '537dbe86dad08c288d5f559707b888257c40ea6aadb89b5abfbbf9789e1825a6aadb89b5abfbbf9789e1825a6']:
        if secret in main or secret in companion or secret in html:
            errors.append('Fichier intégral exposé dans la liseuse')
    return errors
if __name__=='__main__':
    problems=validate()
    for error in problems:print('ÉCHEC:',error)
    if not problems:print('OK: liseuse V28, repères privés, recherche locale et contrat RLS')
    raise SystemExit(bool(problems))
