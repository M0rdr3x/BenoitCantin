#!/usr/bin/env python3
"""V57 : vraie page compte/liseuse.html, moteur PDF simulé, aucun vrai roman.

Tests sur moteurs Chromium/WebKit dans un mobile simulé. Les ressources
externes sont toutes bloquées. Les données du livre sont synthétiques et
ne traversent jamais Supabase. Ce n'est pas une certification sur iPhone réel.
"""
import argparse
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from test_sinjira_liseuse_mobile_v54 import serve_fixture, swipe


MOCK_PDF_JS = """
export const GlobalWorkerOptions = {workerSrc:''};
function makePage(pageNumber){
  return {
    async getTextContent(){
      const items=Array.from({length:46},(_,i)=>({
        str:'LIVRE DE TEST · Page '+pageNumber+' · paragraphe '+(i+1)+
          ' : une phrase synthétique qui occupe de la place et permet de lire '+
          'avec une taille de texte confortable sur téléphone. Aucune donnée privée.',
        transform:[1,0,0,1,40,900-i*28],height:12,
        width:120,hasEOL:true
      }));
      return {items};
    },
    getViewport({scale=1}={}){return {width:612*scale,height:792*scale}},
    render(){return {promise:Promise.resolve()}}
  };
}
export function getDocument({data}={}){
  if(!data||data.length<1024)throw Error('V57 mock: missing test PDF');
  return {promise:Promise.resolve({
    numPages:82,getPage:async n=>{
      if(n<1||n>82)throw Error('V57 mock: invalid page '+n);
      return makePage(n);
    },destroy:async()=>{}
  })};
}
"""

SUPABASE_STUB = """
export function getSupabase(){throw Error('V57: unexpected Supabase access')};
export async function requireUser(){throw Error('V57: unexpected sign-in')};
export function safeInternalDestination(x){return x};
"""

def install_isolation(page, image_only_pages=(), text_error_pages=()):
    """Simule un PDF sans texte ou un échec d'extraction sans accès externe."""
    requests=[]
    mock_pdf = MOCK_PDF_JS
    if image_only_pages:
        pages = "[" + ",".join(str(int(n)) for n in image_only_pages) + "]"
        mock_pdf = MOCK_PDF_JS.replace(
            "const items=Array.from(",
            f"const items={pages}.includes(pageNumber)?[]:Array.from(", 1
        )
    if text_error_pages:
        pages = "[" + ",".join(str(int(n)) for n in text_error_pages) + "]"
        mock_pdf = mock_pdf.replace(
            "    async getTextContent(){",
            "    async getTextContent(){\n"
            + f"      if({pages}.includes(pageNumber)) "
            + "throw Error('V82 simulated extraction unavailable');",
            1
        )
    def intercept(route):
        url=route.request.url
        parsed=urlparse(url)
        path=parsed.path
        if path == "/assets/js/sinjira-supabase.js":
            route.fulfill(status=200,content_type="text/javascript",
                          body=SUPABASE_STUB)
        elif "pdfjs-dist@4.9.155/build/pdf.min.mjs" in url:
            route.fulfill(status=200,content_type="text/javascript",body=mock_pdf)
        elif path == "/projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf":
            route.fulfill(status=200,content_type="application/pdf",
                          body=b"%PDF-1.4 V57 synthetic only " + b"0"*2400)
        elif path == "/assets/js/site.js":
            route.fulfill(status=200,content_type="text/javascript",body="// isolated V57")
        elif parsed.hostname in ("127.0.0.1","localhost"):
            route.continue_()
        else:
            requests.append(url)
            route.abort()
    page.route("**/*", intercept)
    return requests


def snapshot(page):
    return page.evaluate("""()=>{
      const v=document.querySelector('#reader-viewer');
      const t=document.querySelector('#reader-text');
      const output=document.querySelector('#reader-screen-count');
      return {
        page:Number(document.querySelector('#reader-page').value),
        scroll:v.scrollTop,max:Math.max(0,v.scrollHeight-v.clientHeight),
        layout:v.dataset.readerLayout,text:t.textContent,
        textHidden:t.hidden,screen:output.textContent,
        prevDisabled:document.querySelector('#reader-previous').disabled,
        nextDisabled:document.querySelector('#reader-next').disabled,
        mode:document.querySelector('#reader-mode').textContent
      };
    }""")


def run(playwright, browser_type, url):
    browser=getattr(playwright,browser_type).launch()
    try:
        context=browser.new_context(viewport={"width":390,"height":844},
                                    is_mobile=True,has_touch=True,
                                    locale="fr-CA",device_scale_factor=2,
                                    service_workers="block",reduced_motion="reduce")
        page=context.new_page()
        failures=[]
        page.on("pageerror",lambda err: failures.append(str(err)))
        rejected=install_isolation(page)
        page.goto(url,wait_until="load")
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-viewer').dataset.readerLayout==='screens'&&
          document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST')""",timeout=15000)
        first=snapshot(page)
        assert first["page"]==3 and first["layout"]=="screens",first
        assert first["max"]>200 and first["prevDisabled"] is False,{
            "scroll":first["scroll"],"max":first["max"],"page":first["page"]}
        assert first["scroll"]<2,{
            "reason":"Page initiale PDF incorrectement repositionnée",
            "scroll":first["scroll"],"max":first["max"],"page":first["page"]}
        assert "LIVRE DE TEST · Page 3" in first["text"]
        # V137 : les éléments de navigation qui appellent V26 directement
        # (champ de page, curseur, chapitres) ne doivent ni tourner ni
        # persister une position quand le roman est masqué. En mode écran
        # tactile, les swipes restent déjà bloqués par V52/V53.
        hidden_direct_navigation=page.evaluate("""()=>{
          const content=document.querySelector('#reader-content');
          const field=document.querySelector('#reader-page');
          const range=document.querySelector('#reader-range');
          const chapters=document.querySelector('#reader-chapters');
          const viewer=document.querySelector('#reader-viewer');
          const initial={page:field.value,range:range.value,chapters:chapters.value,
            scroll:viewer.scrollTop};
          content.hidden=true;
          const change=(el,value)=>{
            el.value=value;
            el.dispatchEvent(new Event('change',{bubbles:true}));
          };
          try{
            change(field,'17');
            change(range,'19');
            change(chapters,'25');
            document.querySelector('#reader-next').click();
            document.querySelector('#reader-previous').click();
            // V140 : mode et zoom sont des chemins de rendu indépendants
            // de changePage(). Une transition hors écran doit aussi les
            // laisser inchangés, y compris le libellé d'accessibilité.
            const mode=document.querySelector('#reader-mode');
            const zoom=document.querySelector('#reader-zoom');
            const beforeDisplay={
              mode:mode.getAttribute('aria-pressed'),
              modeText:mode.textContent,zoom:zoom.value,
              page:field.value
            };
            mode.click();
            zoom.value='1.5';
            zoom.dispatchEvent(new Event('change',{bubbles:true}));
            const afterDisplay={
              mode:mode.getAttribute('aria-pressed'),
              modeText:mode.textContent,zoom:zoom.value,
              page:field.value
            };
            // V141 : les réglages typographiques ne doivent ni persister
            // ni préparer un reflow à viewport nul quand le livre est caché.
            const prefIds=['reader-theme','reader-size','reader-font',
              'reader-line-height','reader-text-width','reader-letter-spacing'];
            const values=()=>Object.fromEntries(prefIds.map(id=>
              [id,document.getElementById(id).value]));
            const css=()=>({
              theme:document.body.dataset.readTheme,
              size:document.body.style.getPropertyValue('--reader-text-size'),
              font:document.body.style.getPropertyValue('--reader-font'),
              line:document.body.style.getPropertyValue('--reader-line-height'),
              measure:document.body.style.getPropertyValue('--reader-measure'),
              letter:document.body.style.getPropertyValue('--reader-letter-spacing'),
              sizeLabel:document.querySelector('#reader-size-value').textContent
            });
            const beforePrefs={values:values(),css:css(),
              storage:localStorage.getItem('sinjira:liseuse:preferences')};
            const attempted={
              'reader-theme':['clair','change'],
              'reader-size':['24','input'],
              'reader-font':['sans','change'],
              'reader-line-height':['2.1','change'],
              'reader-text-width':['600','change'],
              'reader-letter-spacing':['0.035','change']
            };
            for(const [id,[value,type]] of Object.entries(attempted)){
              const el=document.getElementById(id);
              el.value=value;
              el.dispatchEvent(new Event(type,{bubbles:true}));
            }
            const afterPrefs={values:values(),css:css(),
              storage:localStorage.getItem('sinjira:liseuse:preferences')};
            return {initial,after:{
              page:field.value,range:range.value,chapters:chapters.value,
              scroll:viewer.scrollTop
            },beforeDisplay,afterDisplay,beforePrefs,afterPrefs,
              contentHidden:content.hidden};
          }finally{content.hidden=false}
        }""")
        assert hidden_direct_navigation["contentHidden"],hidden_direct_navigation
        assert hidden_direct_navigation["after"]==hidden_direct_navigation["initial"],(
            "V137: aucune navigation directe ni valeur trompeuse lorsque le livre est masqué",
            hidden_direct_navigation
        )
        assert hidden_direct_navigation["afterDisplay"]==hidden_direct_navigation["beforeDisplay"],(
            "V140: le PDF/texte et le zoom ne doivent pas changer quand le livre est caché",
            hidden_direct_navigation
        )
        assert hidden_direct_navigation["afterPrefs"]==hidden_direct_navigation["beforePrefs"],(
            "V141: aucun style, réglage ou stockage modifié quand le livre est caché",
            hidden_direct_navigation
        )
        # La vraie navigation doit rester utilisable après réouverture.
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-viewer').dataset.readerLayout==='screens'""")

        # V142 : un numéro de page incomplet ne doit pas téléporter
        # la lecture à la première page ni effacer la progression. Un
        # effacement provisoire est fréquent sur un clavier de téléphone.
        invalid_page_input=page.evaluate("""()=>{
          const field=document.querySelector('#reader-page');
          const range=document.querySelector('#reader-range');
          const chapter=document.querySelector('#reader-chapters');
          const viewer=document.querySelector('#reader-viewer');
          const status=document.querySelector('#reader-position-status');
          const key='sinjira:liseuse:demo:la-cendre-du-jugement';
          let pageSignals=0;
          viewer.addEventListener('sinjira:reader-page-change',
            ()=>pageSignals++);
          const state=()=>({
            page:field.value,range:range.value,chapter:chapter.value,
            scroll:viewer.scrollTop,notice:status.textContent,
            storage:localStorage.getItem(key),
            updated:localStorage.getItem(key+':updated'),
            spot:localStorage.getItem(key+':spot')
          });
          const before=state();
          const attempts=[];
          for(const candidate of ['', '0', '-1', '3.5', '1e500']){
            field.value=candidate;
            field.dispatchEvent(new Event('change',{bubbles:true}));
            attempts.push({candidate,after:state()});
          }
          return {before,attempts,pageSignals};
        }""")
        assert invalid_page_input["before"]["page"]=="3",invalid_page_input
        assert invalid_page_input["pageSignals"]==0,invalid_page_input
        for attempt in invalid_page_input["attempts"]:
            assert attempt["after"]==invalid_page_input["before"],(
                "V142: saisie de page invalide ne doit pas effacer l'endroit lu",
                attempt,invalid_page_input
            )

        # V138 : un scroll retardé ou un signal screen-turn sur un roman
        # déjà masqué ne doit ni modifier l'horodatage local ni afficher
        # une sauvegarde fictive. Même la commande explicite « Enregistrer »
        # doit respecter l'état du lecteur privé.
        hidden_progress=page.evaluate("""async()=>{
          const content=document.querySelector('#reader-content');
          const viewer=document.querySelector('#reader-viewer');
          const key='sinjira:liseuse:demo:la-cendre-du-jugement';
          const status=document.querySelector('#reader-position-status');
          const read=()=>({
            page:localStorage.getItem(key),
            updated:localStorage.getItem(key+':updated'),
            spot:localStorage.getItem(key+':spot'),
            notice:status.textContent,
            screen:document.querySelector('#reader-page').value
          });
          // Terminer les éventuelles écritures légitimes de l'initialisation.
          await new Promise(done=>setTimeout(done,720));
          const before=read();
          content.hidden=true;
          try{
            viewer.dispatchEvent(new Event('sinjira:reader-screen-turn'));
            viewer.dispatchEvent(new Event('scroll'));
            document.querySelector('#reader-save-position').click();
            // La persistance différée interviendrait normalement à 650 ms.
            await new Promise(done=>setTimeout(done,740));
            return {before,after:read(),hidden:content.hidden};
          }finally{content.hidden=false}
        }""")
        assert hidden_progress["hidden"],hidden_progress
        assert hidden_progress["after"]==hidden_progress["before"],(
            "V138: la lecture masquée ne doit pas enregistrer une progression différée",
            hidden_progress
        )
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-viewer').dataset.readerLayout==='screens'""")

        # V143 : un téléphone peut envoyer resize/orientationchange
        # pendant que le PDF est masqué. Le rendu ne doit pas mesurer
        # une largeur nulle ni écraser le canvas/spot avant réouverture.
        page.locator("#reader-mode").click()
        page.wait_for_function("""()=>document.querySelector('#reader-text').hidden&&
          !document.querySelector('#reader-canvas').hidden&&
          document.querySelector('#reader-canvas').width>100""")
        hidden_pdf_resize=page.evaluate("""async()=>{
          const root=document.querySelector('#reader-content');
          const canvas=document.querySelector('#reader-canvas');
          const viewer=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          const key='sinjira:liseuse:demo:la-cendre-du-jugement';
          const grab=()=>({
            width:canvas.width,height:canvas.height,
            styleWidth:canvas.style.width,styleHeight:canvas.style.height,
            page:field.value,zoom:document.querySelector('#reader-zoom').value,
            spot:localStorage.getItem(key+':spot'),
            updated:localStorage.getItem(key+':updated')
          });
          const before=grab();
          try{
            // Course réelle : resize émis AVANT le masquage, callback APRÈS.
            window.dispatchEvent(new Event('resize'));
            root.hidden=true;
            await new Promise(done=>setTimeout(done,340));
            const afterPending=grab();
            // Puis un resize reçu directement pendant la suspension.
            window.dispatchEvent(new Event('resize'));
            await new Promise(done=>setTimeout(done,340));
            const whileHidden=grab();
            return {before,afterPending,whileHidden,
              rootHidden:root.hidden,hiddenWidth:viewer.clientWidth};
          }finally{root.hidden=false}
        }""")
        assert hidden_pdf_resize["rootHidden"],hidden_pdf_resize
        assert hidden_pdf_resize["before"]==hidden_pdf_resize["afterPending"],(
            "V143: un resize programmé avant la suspension ne doit pas réafficher un PDF caché",
            hidden_pdf_resize
        )
        assert hidden_pdf_resize["before"]==hidden_pdf_resize["whileHidden"],(
            "V143: un resize reçu pendant la suspension ne doit rien changer",
            hidden_pdf_resize
        )
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden""")
        # Après réouverture, une rotation/resize explicite doit rester
        # possible, sans désactiver le mode PDF ni le changement de page.
        page.evaluate("window.dispatchEvent(new Event('resize'))")
        page.wait_for_function("""()=>document.querySelector('#reader-canvas').width>100&&
          document.querySelector('#reader-page').value==='3'""")
        page.locator("#reader-mode").click()
        page.wait_for_function("""()=>document.querySelector('#reader-viewer')
          .dataset.readerLayout==='screens'&&
          !document.querySelector('#reader-text').hidden""")

        # V144 : rotation reçue juste avant/après le masquage du livre
        # en TEXTE paginé. L'ancien reflow dans un viewport nul pouvait
        # écraser la portion lue. Vérifier la restitution après réouverture.
        hidden_text_resize=page.evaluate("""async()=>{
          const content=document.querySelector('#reader-content');
          const viewer=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          const frame=()=>new Promise(resolve=>requestAnimationFrame(resolve));
          const settle=async n=>{for(let i=0;i<n;i++)await frame()};
          viewer.scrollTop=Math.min(365,viewer.scrollHeight-viewer.clientHeight-180);
          viewer.dispatchEvent(new Event('scroll'));
          await settle(3);
          const before={page:field.value,scroll:viewer.scrollTop,
            layout:viewer.dataset.readerLayout};
          window.dispatchEvent(new Event('resize')); // rappel rAF différé
          content.hidden=true;
          try{
            await settle(4);
            window.dispatchEvent(new Event('resize')); // rotation cachée
            await settle(3);
          }finally{content.hidden=false}
          await settle(10); // réaffichage, puis restitution différée
          const after={page:field.value,scroll:viewer.scrollTop,
            layout:viewer.dataset.readerLayout};
          return {before,after,hidden:content.hidden};
        }""")
        assert not hidden_text_resize["hidden"],hidden_text_resize
        assert hidden_text_resize["before"]["page"]=="3",hidden_text_resize
        assert hidden_text_resize["before"]["layout"]=="screens",hidden_text_resize
        assert hidden_text_resize["before"]["scroll"]>150,hidden_text_resize
        assert hidden_text_resize["after"]["page"]=="3",hidden_text_resize
        assert hidden_text_resize["after"]["layout"]=="screens",hidden_text_resize
        assert abs(hidden_text_resize["after"]["scroll"]-
                   hidden_text_resize["before"]["scroll"])<90,(
            "V144: une rotation masquée ne doit pas perdre le passage lu",
            hidden_text_resize
        )
        # Ne pas polluer la suite des contrôles de page et d'accessibilité.
        page.evaluate("""()=>{
          const viewer=document.querySelector('#reader-viewer');
          viewer.scrollTop=0;viewer.dispatchEvent(new Event('scroll'));
        }""")
        page.wait_for_function("""()=>document.querySelector('#reader-viewer').scrollTop<2""")

        # V145 : un simple changement d'application cache l'onglet
        # mais pas nécessairement #reader-content. V144 doit restituer
        # son ancre au retour via visibilitychange, sans mutation DOM.
        background_tab_restore=page.evaluate("""async()=>{
          const viewer=document.querySelector('#reader-viewer');
          const root=document.querySelector('#reader-content');
          const field=document.querySelector('#reader-page');
          const oldHidden=Object.getOwnPropertyDescriptor(document,'hidden');
          const frame=()=>new Promise(resolve=>requestAnimationFrame(resolve));
          const settle=async(n)=>{for(let i=0;i<n;i++)await frame()};
          const visible=()=>Object.defineProperty(document,'hidden',{
            configurable:true,value:false
          });
          const hidden=()=>Object.defineProperty(document,'hidden',{
            configurable:true,value:true
          });
          const restore=()=>{
            if(oldHidden)Object.defineProperty(document,'hidden',oldHidden);
            else delete document.hidden;
          };
          await settle(5);
          viewer.scrollTop=Math.min(680,viewer.scrollHeight-viewer.clientHeight-200);
          viewer.dispatchEvent(new Event('scroll'));
          await settle(3);
          const before={page:field.value,scroll:viewer.scrollTop,
            rootHidden:root.hidden,layout:viewer.dataset.readerLayout};
          try{
            hidden();
            document.dispatchEvent(new Event('visibilitychange'));
            window.dispatchEvent(new Event('resize')); // V144 mémorise l'ancre
            viewer.scrollTop=0; // navigateur mobile a perdu son scroll
            await settle(4);
            visible();
            document.dispatchEvent(new Event('visibilitychange'));
            await settle(12);
            return {before,after:{
              page:field.value,scroll:viewer.scrollTop,
              rootHidden:root.hidden,layout:viewer.dataset.readerLayout
            }};
          }finally{restore()}
        }""")
        assert not background_tab_restore["before"]["rootHidden"],background_tab_restore
        assert background_tab_restore["before"]["scroll"]>200,background_tab_restore
        assert background_tab_restore["after"]["page"]=="3",background_tab_restore
        assert background_tab_restore["after"]["layout"]=="screens",background_tab_restore
        assert not background_tab_restore["after"]["rootHidden"],background_tab_restore
        assert abs(background_tab_restore["after"]["scroll"]-
                   background_tab_restore["before"]["scroll"])<95,(
            "V145: retour d'application sans masquage DOM doit retrouver l'écran lu",
            background_tab_restore
        )
        page.evaluate("""()=>{
          const viewer=document.querySelector('#reader-viewer');
          viewer.scrollTop=0;viewer.dispatchEvent(new Event('scroll'));
        }""")
        page.wait_for_function("""()=>document.querySelector('#reader-viewer').scrollTop<2""")

        # V146 : même si la case « Lire par pages d'écran » reçoit un
        # change tardif après masquage, elle ne doit ni basculer le mode
        # ni enregistrer une préférence. La commande doit fonctionner
        # lorsqu'on ouvre à nouveau la liseuse.
        hidden_screen_mode=page.evaluate("""async()=>{
          const content=document.querySelector('#reader-content');
          const toggle=document.querySelector('#reader-screens-enabled');
          const viewer=document.querySelector('#reader-viewer');
          const key='sinjira:liseuse:lecture-par-ecrans:v53';
          const state=()=>({
            checked:toggle.checked,mode:viewer.dataset.readerLayout,
            stored:localStorage.getItem(key),
            page:document.querySelector('#reader-page').value,
            screen:document.querySelector('#reader-screen-count').textContent
          });
          const before=state();
          content.hidden=true;
          try{
            toggle.checked=!before.checked;
            toggle.dispatchEvent(new Event('change',{bubbles:true}));
            const after=state();
            return {before,after,contentWasHidden:content.hidden};
          }finally{content.hidden=false}
        }""")
        assert hidden_screen_mode["contentWasHidden"],hidden_screen_mode
        assert hidden_screen_mode["before"]==hidden_screen_mode["after"],(
            "V146: changement du mode paginé masqué ne doit pas être accepté",
            hidden_screen_mode
        )
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden""")
        visible_screen_mode=page.evaluate("""()=>{
          const toggle=document.querySelector('#reader-screens-enabled');
          const viewer=document.querySelector('#reader-viewer');
          const key='sinjira:liseuse:lecture-par-ecrans:v53';
          toggle.checked=false;
          toggle.dispatchEvent(new Event('change',{bubbles:true}));
          const off={checked:toggle.checked,mode:viewer.dataset.readerLayout,
            stored:localStorage.getItem(key)};
          toggle.checked=true;
          toggle.dispatchEvent(new Event('change',{bubbles:true}));
          return {off,on:{checked:toggle.checked,mode:viewer.dataset.readerLayout,
            stored:localStorage.getItem(key)}};
        }""")
        assert visible_screen_mode["off"]=={
            "checked":False,"mode":"scroll","stored":"off"
        },visible_screen_mode
        assert visible_screen_mode["on"]=={
            "checked":True,"mode":"screens","stored":"on"
        },visible_screen_mode
        page.wait_for_function("""()=>document.querySelector('#reader-viewer')
          .dataset.readerLayout==='screens'""")
        # V147 : un « change » retardé du curseur ne doit pas mesurer
        # la zone d'un roman caché, qui vaut zéro sur les vrais navigateurs.
        hidden_slider=page.evaluate("""()=>{
          const content=document.querySelector('#reader-content');
          const slider=document.querySelector('#reader-screen-jump');
          const viewer=document.querySelector('#reader-viewer');
          const status=document.querySelector('#reader-screen-count');
          const pageField=document.querySelector('#reader-page');
          const read=()=>({status:status.textContent,
            label:viewer.getAttribute('aria-label'),
            page:pageField.value,mode:viewer.dataset.readerLayout});
          const before=read();
          content.hidden=true;
          try{
            slider.value=slider.max;
            slider.dispatchEvent(new Event('change',{bubbles:true}));
            return {before,after:read(),hidden:content.hidden};
          }finally{content.hidden=false}
        }""")
        assert hidden_slider["hidden"] and hidden_slider["before"]==hidden_slider["after"],(
            "V147 : le curseur d'un livre masqué a modifié l'annonce ou la page",
            hidden_slider
        )
        # V148 : un événement tardif de changement de page PDF lors du
        # masquage ne doit écraser ni compteur, ni libellé, ni curseur.
        hidden_page_event=page.evaluate("""()=>{
          const content=document.querySelector('#reader-content');
          const viewer=document.querySelector('#reader-viewer');
          const slider=document.querySelector('#reader-screen-jump');
          const status=document.querySelector('#reader-screen-count');
          const location=document.querySelector('#reader-touch-location');
          const read=()=>({counter:status.textContent,slider:slider.value,
            sliderMax:slider.max,sliderHidden:slider.hidden,
            label:viewer.getAttribute('aria-label'),location:location.textContent,
            layout:viewer.dataset.readerLayout});
          const before=read();
          content.hidden=true;
          try{
            viewer.dispatchEvent(new Event('sinjira:reader-page-change'));
            return {before,after:read(),hidden:content.hidden};
          }finally{content.hidden=false}
        }""")
        assert hidden_page_event["hidden"] and hidden_page_event["before"]==hidden_page_event["after"],(
            "V148 : signal PDF masqué a écrasé la pagination ou le statut mobile",
            hidden_page_event
        )
        # V150 : input du curseur reçu avec le roman masqué, puis change
        # différé après la réouverture : ne jamais tourner une page fantôme.
        stale_slider=page.evaluate("""()=>{
          const content=document.querySelector('#reader-content');
          const viewer=document.querySelector('#reader-viewer');
          const slider=document.querySelector('#reader-screen-jump');
          const status=document.querySelector('#reader-screen-count');
          const before={top:viewer.scrollTop,screen:status.textContent};
          content.hidden=true;
          try{
            slider.value=slider.max;
            slider.dispatchEvent(new Event('input',{bubbles:true}));
          }finally{content.hidden=false}
          slider.dispatchEvent(new Event('change',{bubbles:true}));
          return {before,after:{top:viewer.scrollTop,screen:status.textContent},
            slider:slider.value,max:slider.max};
        }""")
        assert int(stale_slider["max"])>1,stale_slider
        assert stale_slider["before"]==stale_slider["after"],(
            "V150 : confirmation tardive d'un slider masqué a tourné le livre",
            stale_slider
        )
        # Le mode normal doit reprendre au début de l'écran pour la
        # réception des annonces et du curseur qui suit.
        page.evaluate("""()=>{
          const viewer=document.querySelector('#reader-viewer');
          viewer.scrollTop=0;viewer.dispatchEvent(new Event('scroll'));
        }""")
        page.wait_for_function("""()=>document.querySelector('#reader-viewer').scrollTop<2""")

        # V102 : l'emplacement du lecteur est visible dans les commandes
        # mobiles et indépendant des extraits privés du texte.
        # La démo réelle possède 82 pages ; la fixture simplifiée en a 5.
        # Ne jamais figer le nombre de pages dans ce test de page réelle.
        source_pages=page.locator("#reader-total").text_content().strip()
        assert source_pages.isdecimal() and int(source_pages)>=5,source_pages
        hint_start=page.locator("#reader-touch-location").text_content()
        assert hint_start.startswith("Écr. 1/") and f"p. 3 / {source_pages}" in hint_start, (
            "V102 : lecture sans repère de progression",hint_start
        )
        # V103 : le focus sur la région de lecture donne une position
        # précise, sans exposer le texte fictif ni déclencher une deuxième
        # région aria-live.
        def accessible_reader_label():
            return page.locator("#reader-viewer").get_attribute("aria-label")
        label_start=accessible_reader_label()
        assert page.locator("#reader-viewer").get_attribute("role")=="region"
        assert "écran 1 sur " in label_start and f"page 3 sur {source_pages}" in label_start, label_start
        assert "LIVRE DE TEST" not in label_start,label_start

        # V104 : le curseur de navigation atteint une portion de texte
        # éloignée sans appeler les boutons de changement de page source.
        jump=page.locator("#reader-screen-jump")
        jump_label=page.locator("#reader-screen-jump-label")
        # V105 : attendre que le moteur ait recalculé le nombre d'écrans.
        # WebKit peut avoir fini le chargement du texte avant le retour de
        # l'observateur MutationObserver responsable du libellé.
        page.wait_for_function("""()=>{
          const slider=document.querySelector('#reader-screen-jump');
          const label=document.querySelector('#reader-screen-jump-label');
          return !slider.hidden && !label.hidden &&
            Number(slider.max)>=4 && slider.value==='1';
        }""")
        assert jump_label.is_visible(),("V105 : l'étiquette du curseur est invisible en pagination")
        jump_forward=page.evaluate("""()=>{
          const el=document.querySelector('#reader-screen-jump');
          const v=document.querySelector('#reader-viewer');
          window.__v106JumpSignals=0;
          v.addEventListener('sinjira:reader-screen-turn',()=>{
            window.__v106JumpSignals++;
          });
          for(const screen of ['2','3','2','3']){
            el.value=screen;
            el.dispatchEvent(new Event('input',{bubbles:true}));
          }
          const preview={top:v.scrollTop,signals:window.__v106JumpSignals,
            status:document.querySelector('#reader-screen-count').textContent,
            accessible:el.getAttribute('aria-valuetext')};
          el.dispatchEvent(new Event('change',{bubbles:true}));
          return {preview,source:document.querySelector('#reader-page').value,
            top:v.scrollTop,max:v.scrollHeight-v.clientHeight,
            signals:window.__v106JumpSignals,range:el.value,
            accessible:el.getAttribute('aria-valuetext'),
            label:document.querySelector('#reader-touch-location').textContent};
        }""")
        assert jump_forward["preview"]["top"]<2 and jump_forward["preview"]["signals"]==0,(
            "V106 : le curseur déclenche une sauvegarde avant relâche",jump_forward)
        assert "relâcher" in jump_forward["preview"]["accessible"],jump_forward
        assert jump_forward["source"]=="3" and jump_forward["top"]>100 and (
            jump_forward["range"]=="3" and jump_forward["signals"]==1
        ),jump_forward
        assert "Écran 3 sur " in jump_forward["accessible"],jump_forward
        assert jump_forward["label"].startswith("Écr. 3/"),jump_forward
        jump_back=page.evaluate("""()=>{
          const el=document.querySelector('#reader-screen-jump');
          const viewer=document.querySelector('#reader-viewer');
          el.value='1';
          el.dispatchEvent(new Event('input',{bubbles:true}));
          const preview=viewer.scrollTop;
          el.dispatchEvent(new Event('change',{bubbles:true}));
          return {preview,top:viewer.scrollTop,
            signals:window.__v106JumpSignals};
        }""")
        assert jump_back["preview"]>100 and jump_back["top"]<2 and (
            jump_back["signals"]==2
        ),jump_back
        # V108 : après perte de focus pendant le drag, le navigateur peut
        # produire un change tardif : il ne doit pas tourner le livre.
        interrupted=page.evaluate("""()=>{
          const el=document.querySelector('#reader-screen-jump');
          const viewer=document.querySelector('#reader-viewer');
          const selection=screen=>{
            el.value=String(screen);
            el.dispatchEvent(new Event('input',{bubbles:true}));
          };
          const confirm=()=>el.dispatchEvent(new Event('change',{bubbles:true}));
          selection(3);
          const preview={top:viewer.scrollTop,signals:window.__v106JumpSignals};
          window.dispatchEvent(new Event('blur'));
          // V109 : contrôle immédiat avant tout change natif.
          const instant={top:viewer.scrollTop,signals:window.__v106JumpSignals,
            range:el.value,accessible:el.getAttribute('aria-valuetext')};
          el.value='3';confirm(); // confirmation obsolète
          const ignored={top:viewer.scrollTop,signals:window.__v106JumpSignals,
            range:el.value};
          selection(2);confirm(); // nouvelle demande intentionnelle
          const resumed={top:viewer.scrollTop,signals:window.__v106JumpSignals};
          selection(1);confirm(); // restaurer la page avant les swipes
          const restored={top:viewer.scrollTop,signals:window.__v106JumpSignals};
          return {preview,instant,ignored,resumed,restored,
            page:document.querySelector('#reader-page').value};
        }""")
        assert interrupted["preview"]["top"]<2 and (
            interrupted["instant"]["top"]<2 and
            interrupted["instant"]["signals"]==2 and
            interrupted["instant"]["range"]=="1" and
            "Écran 1 sur" in interrupted["instant"]["accessible"] and
            "relâcher" not in interrupted["instant"]["accessible"] and
            interrupted["ignored"]["top"]<2 and
            interrupted["ignored"]["signals"]==2 and
            interrupted["ignored"]["range"]=="1"
        ),("V108 : confirmation tardive après perte de focus",interrupted)
        assert interrupted["resumed"]["top"]>50 and (
            interrupted["resumed"]["signals"]==3 and
            interrupted["restored"]["top"]<2 and
            interrupted["restored"]["signals"]==4 and
            interrupted["page"]=="3"
        ),("V108 : le curseur doit rester utilisable après retour",interrupted)
        assert snapshot(page)["page"]==3,snapshot(page)
        assert not rejected,rejected

        # Diagnostic de régression : retracer toute tentative de déclencher
        # la navigation PDF depuis un seul geste, y compris un double module.
        page.evaluate("""() => {
          window.__readerSwipeTrace=[];
          const next=document.querySelector('#reader-next');
          const orig=next.click.bind(next);
          next.click=function(...args){
            window.__readerSwipeTrace.push({
              type:'next.click',stack:new Error('PDF next clicked').stack,
              layout:document.querySelector('#reader-viewer').dataset.readerLayout,
              top:document.querySelector('#reader-viewer').scrollTop
            });
            return orig(...args);
          };
          const input=document.querySelector('#reader-page');
          const desc=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value');
          Object.defineProperty(input,'value',{
            configurable:true,
            get(){return desc.get.call(this)},
            set(value){
              window.__readerSwipeTrace.push({
                type:'page.value.setter',value:String(value),
                stack:new Error('Page value assigned').stack
              });
              desc.set.call(this,value);
            }
          });
          next.addEventListener('click',event=>{
            window.__readerSwipeTrace.push({
              type:'next.click-event',trusted:event.isTrusted,
              stack:new Error('PDF next event').stack
            });
          },true);
          const viewer=document.querySelector('#reader-viewer');
          viewer.addEventListener('touchend',ev=>{
            window.__readerSwipeTrace.push({
              type:'touchend-after-capture',prevented:ev.defaultPrevented,
              layout:viewer.dataset.readerLayout,top:viewer.scrollTop
            });
          },true);
        }""")
        # Tout le mouvement a lieu sur la vraie fenêtre de lecture, sans
        # modifier la page PDF tant qu'elle comporte du texte.
        forward=swipe(page,-130)
        second=snapshot(page)
        assert forward["consumed"] and second["page"]==3,{
            "first_scroll":first["scroll"],"first_max":first["max"],
            "forward":forward,"second_page":second["page"],
            "second_scroll":second["scroll"],"second_screen":second["screen"],
            "trace":page.evaluate("window.__readerSwipeTrace")}
        assert second["scroll"]>first["scroll"],(first,second)
        label_next=accessible_reader_label()
        assert "écran 2 sur " in label_next and f"page 3 sur {source_pages}" in label_next,label_next
        hint_next=page.locator("#reader-touch-location").text_content()
        assert hint_next.startswith("Écr. 2/") and f"p. 3 / {source_pages}" in hint_next, (
            "V102 : barre de progression non actualisée après le swipe",
            hint_start,hint_next
        )
        reverse=swipe(page,130)
        rewind=snapshot(page)
        assert reverse["consumed"] and rewind["scroll"]==0,rewind

        # Une page source complète ne doit pas être sautée; lorsque toutes
        # ses portions sont lues, une seule autre page PDF est chargée.
        crossed=False
        for _ in range(70):
            swipe(page,-130)
            if snapshot(page)["page"]==4:
                crossed=True
                break
        assert crossed,"V57: pas de transition vers la page PDF suivante"
        page.wait_for_function("""()=>document.querySelector('#reader-text')
          .textContent.includes('LIVRE DE TEST · Page 4')""")
        assert snapshot(page)["page"]==4,snapshot(page)
        assert snapshot(page)["scroll"]==0,snapshot(page)

        # Le retour depuis le premier écran d'une autre page doit exposer
        # la dernière portion de la page PDF précédente.
        swipe(page,130)
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='3'&&
           document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST · Page 3')""")
        page.wait_for_function("""()=>{const v=document.querySelector('#reader-viewer');
          return v.scrollTop>100&&v.scrollTop>=v.scrollHeight-v.clientHeight-3}""")
        assert snapshot(page)["page"]==3,snapshot(page)

        # Marque-page de progression : passage écran puis enregistrement de
        # la position du lecteur de démo dans la clé historique V31.
        page.locator("#reader-touch-prev").click()
        page.locator("#reader-save-position").click()
        page.wait_for_function("""()=>{const key='sinjira:liseuse:demo:la-cendre-du-jugement:spot';
          const value=JSON.parse(localStorage.getItem(key)||'null');
          return value?.page===3&&value?.ratio>0}""")
        saved=page.evaluate("""()=>JSON.parse(localStorage.getItem(
          'sinjira:liseuse:demo:la-cendre-du-jugement:spot'))""")
        assert saved["ratio"]>0,saved

        # Rechargement de la page réelle, sans faux stockage pour la position :
        # le moteur doit restaurer la page 3 et un ratio cohérent.
        page.reload(wait_until="load")
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST · Page 3')""")
        page.wait_for_timeout(120)
        loaded=snapshot(page)
        new_ratio=loaded["scroll"]/max(1,loaded["max"])
        assert loaded["page"]==3 and abs(new_ratio-saved["ratio"])<0.12,(
            "V57: perte de la position après rechargement",saved,loaded
        )

        # La transition vers le PDF doit garder un seul gestionnaire tactile.
        page.locator("#reader-mode").click()
        page.wait_for_function("""()=>document.querySelector('#reader-text').hidden===true""")
        before_pdf=snapshot(page)
        assert page.locator("#reader-touch-location").text_content()==f"PDF · p. 3 / {source_pages}"
        assert page.locator("#reader-screen-jump").is_hidden(), (
            "V104: curseur d'écran affiché dans le PDF")
        assert jump_label.is_hidden(), (
            "V105 : étiquette orpheline visible alors que le PDF est actif")
        label_pdf=accessible_reader_label()
        assert f"PDF : page 3 sur {source_pages}" in label_pdf,label_pdf
        assert "texte adaptable" in label_pdf,label_pdf
        swipe(page,-130)
        page.wait_for_function("""before=>Number(document.querySelector('#reader-page').value)===before+1""",
                               arg=before_pdf["page"])
        assert snapshot(page)["page"]==before_pdf["page"]+1, (
            "V57: double saut de PDF",before_pdf,snapshot(page)
        )

        # V98 : homologuer les tapotements PDF SUR LA VRAIE PAGE HTML,
        # et pas uniquement sur la fixture simplifiée V54. Le canvas est
        # la véritable cible dans la zone PDF; les événements remontent
        # jusqu'au gestionnaire de la liseuse. PDF et identité synthétiques.
        page.evaluate("""()=>{
          window.__v98Clicks={next:0,previous:0};
          document.querySelector('#reader-next').addEventListener('click',()=>{
            window.__v98Clicks.next++;
          },true);
          document.querySelector('#reader-previous').addEventListener('click',()=>{
            window.__v98Clicks.previous++;
          },true);
        }""")

        def tap_pdf_edge(portion):
            return page.evaluate("""portion=>{
              const viewer=document.querySelector('#reader-viewer');
              const canvas=document.querySelector('#reader-canvas');
              const rect=viewer.getBoundingClientRect();
              const touch={identifier:98,target:canvas,
                clientX:rect.left+rect.width*portion,
                clientY:rect.top+Math.min(120,rect.height*.45)};
              const fire=(kind,touches)=>{
                const event=new Event(kind,{bubbles:true,cancelable:true});
                Object.defineProperties(event,{
                  touches:{value:touches},targetTouches:{value:touches},
                  changedTouches:{value:[touch]}
                });
                canvas.dispatchEvent(event);
              };
              fire('touchstart',[touch]);
              fire('touchend',[]);
              return {page:Number(document.querySelector('#reader-page').value),
                layout:viewer.dataset.readerLayout,
                textHidden:document.querySelector('#reader-text').hidden,
                clickCounts:{...window.__v98Clicks}};
            }""",portion)

        # Depuis la page 4, toucher la marge gauche ramène à la page 3.
        pdf_left=tap_pdf_edge(.15)
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='3'&&
          document.querySelector('#reader-text').hidden===true""")
        assert pdf_left["page"]==3 and pdf_left["layout"]=="scroll",pdf_left
        assert pdf_left["clickCounts"]=={"next":0,"previous":1},pdf_left

        # Le centre et les bords système ne changent ni page ni compteur.
        pdf_middle=tap_pdf_edge(.5)
        pdf_os_edge=tap_pdf_edge(.02)
        assert pdf_middle["page"]==3 and pdf_os_edge["page"]==3,(pdf_middle,pdf_os_edge)
        assert pdf_os_edge["clickCounts"]=={"next":0,"previous":1},pdf_os_edge

        # La marge droite avance exactement UNE page, et l'article PDF
        # reste caché : pas de bascule intempestive vers le texte paginé.
        pdf_right=tap_pdf_edge(.85)
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='4'&&
          document.querySelector('#reader-text').hidden===true""")
        assert pdf_right["page"]==4 and pdf_right["layout"]=="scroll",pdf_right
        assert pdf_right["clickCounts"]=={"next":1,"previous":1},pdf_right
        assert snapshot(page)["page"]==4,snapshot(page)
        assert page.locator("#reader-touch-location").text_content()==f"PDF · p. 4 / {source_pages}"
        assert f"PDF : page 4 sur {source_pages}" in accessible_reader_label()

        # V99 : les tests V98 construisent des TouchEvent. Vérifier EN PLUS
        # une vraie séquence tactile du navigateur mobile Playwright, avec
        # isMobile/hasTouch, sur le DOM réel (PDF entièrement synthétique).
        # Un tap natif émet aussi un click : aucune double navigation PDF.
        page.evaluate("""()=>{
          window.__v99NativeTouches=[];
          document.querySelector('#reader-viewer').addEventListener('touchstart',event=>{
            window.__v99NativeTouches.push({
              trusted:event.isTrusted,kind:event.type,
              count:event.touches.length
            });
          },{capture:true,passive:true});
        }""")

        def tap_native_pdf(portion):
            page.locator("#reader-viewer").scroll_into_view_if_needed()
            location=page.evaluate("""portion=>{
              const viewer=document.querySelector('#reader-viewer');
              const rect=viewer.getBoundingClientRect();
              // Rechercher un point visible loin des barres du navigateur
              // et du début de page, mais toujours dans le vrai lecteur.
              const x=rect.left+rect.width*portion;
              const y=Math.min(window.innerHeight-35,
                Math.max(35,rect.top+Math.min(115,rect.height*.45)));
              const under=document.elementFromPoint(x,y);
              return {x,y,inside:Boolean(under&&
                (under===viewer||viewer.contains(under))),
                target:under?.id||under?.tagName||null,
                top:rect.top,bottom:rect.bottom,width:rect.width};
            }""",portion)
            assert location["inside"],location
            page.touchscreen.tap(location["x"],location["y"])
            return snapshot(page),page.evaluate("""()=>({
              clicks:{...window.__v98Clicks},
              touches:[...window.__v99NativeTouches]
            })""")

        # Le centre de l'écran PDF ne doit rien tourner.
        center_native,center_events=tap_native_pdf(.5)
        assert center_native["page"]==4,center_native
        assert center_events["clicks"]=={"next":1,"previous":1},center_events

        # Tap natif côté gauche : une seule page en arrière.
        native_left,native_left_events=tap_native_pdf(.15)
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='3'""")
        assert native_left["page"]==3,native_left
        assert native_left_events["clicks"]=={"next":1,"previous":2},native_left_events

        # Tap natif côté droit : une seule page en avant.
        native_right,native_right_events=tap_native_pdf(.85)
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='4'""")
        assert native_right["page"]==4,native_right
        assert native_right_events["clicks"]=={"next":2,"previous":2},native_right_events
        assert len(native_right_events["touches"])==3,native_right_events
        assert all(t["trusted"] and t["count"]==1
                   for t in native_right_events["touches"]),native_right_events

        # Repasser au texte et à la mise en page mobile.
        page.locator("#reader-mode").click()
        # MutationObserver V53 rétablit le mode paginé après que le moteur
        # PDF a rendu le texte : attendre les DEUX conditions de stabilité.
        page.wait_for_function("""()=>
          document.querySelector('#reader-text').hidden===false &&
          document.querySelector('#reader-viewer').dataset.readerLayout==='screens'""")
        assert snapshot(page)["layout"]=="screens",snapshot(page)

        # V99 : les mêmes vrais tapotements doivent naviguer entre les
        # portions de TEXTE, jamais changer la page source PDF.
        # Laisser finir la restitution asynchrone du retour au texte.
        page.wait_for_timeout(120)
        page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")
        before_text_native=snapshot(page)
        assert before_text_native["page"]==4 and before_text_native["scroll"]<2, (
            "V99 : écran texte initial incorrect",before_text_native
        )
        text_native_next,text_events_next=tap_native_pdf(.85)
        assert text_native_next["page"]==4 and text_native_next["scroll"]>0, (
            "V99 : tap natif sur la marge du texte ne fait pas avancer l'écran",
            text_native_next,text_events_next
        )
        text_native_back,text_events_back=tap_native_pdf(.15)
        assert text_native_back["page"]==4 and text_native_back["scroll"]<2, (
            "V99 : tap natif sur la marge du texte ne revient pas à l'écran",
            text_native_back,text_events_back
        )
        assert text_events_back["clicks"]=={"next":2,"previous":2},(
            "V99 : un tap texte ne doit pas tourner la page PDF",text_events_back
        )
        assert len(text_events_back["touches"])==5,text_events_back

        # V101 : ordinateur / trackpad : glisser la page PDF à la souris.
        # La sélection de texte et les gestes sur écran tactile conservent
        # leurs gestionnaires indépendants. Même HTML, PDF entièrement fictif.
        page.locator("#reader-mode").click()
        page.wait_for_function("""()=>{
          return document.querySelector('#reader-text').hidden===true &&
            !document.querySelector('#reader-canvas').hidden &&
            document.querySelector('#reader-viewer').dataset.readerLayout==='scroll';
        }""")
        page.locator("#reader-viewer").scroll_into_view_if_needed()

        def drag_pdf_with_mouse(direction):
            coords=page.evaluate("""direction=>{
              const v=document.querySelector('#reader-viewer');
              const canvas=document.querySelector('#reader-canvas');
              const rect=canvas.getBoundingClientRect();
              const viewer=v.getBoundingClientRect();
              const from=direction==='next'?.78:.22;
              const to=direction==='next'?.22:.78;
              const x1=rect.left+rect.width*from;
              const x2=rect.left+rect.width*to;
              const y=Math.max(viewer.top+25,Math.min(viewer.bottom-25,
                rect.top+Math.min(65,rect.height*.25)));
              const target=document.elementFromPoint(x1,y);
              return {x1,x2,y,valid:target===canvas,
                canvasWidth:rect.width,viewerTop:viewer.top,
                viewerBottom:viewer.bottom};
            }""",direction)
            assert coords["valid"] and abs(coords["x2"]-coords["x1"])>=100,coords
            page.mouse.move(coords["x1"],coords["y"])
            page.mouse.down()
            page.mouse.move(coords["x2"],coords["y"]+3,steps=7)
            page.mouse.up()
            return snapshot(page),page.evaluate("({...window.__v98Clicks})")

        pdf_mouse_next,mouse_counts_next=drag_pdf_with_mouse('next')
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='5'""")
        assert pdf_mouse_next["page"]==5 and mouse_counts_next=={
            "next":3,"previous":2
        },("V101: un glissement souris doit tourner UNE page PDF",
            pdf_mouse_next,mouse_counts_next)
        pdf_mouse_back,mouse_counts_back=drag_pdf_with_mouse('previous')
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='4'""")
        assert pdf_mouse_back["page"]==4 and mouse_counts_back=={
            "next":3,"previous":3
        },("V101: souris droite = une page précédente",
            pdf_mouse_back,mouse_counts_back)

        # V154 : un clavier physique tenu enfoncé ne doit pas faire sauter
        # plusieurs pages du livre. Vérifier aussi les raccourcis PDF V26.
        repeated_keyboard=page.evaluate("""()=>{
          const viewer=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          viewer.focus({preventScroll:true});
          const fire=(key,repeat)=>{
            const event=new KeyboardEvent('keydown',{
              bubbles:true,cancelable:true,key,repeat
            });
            document.dispatchEvent(event);
            return {page:Number(field.value),blocked:event.defaultPrevented};
          };
          return {
            before:Number(field.value),
            heldNext:fire('ArrowRight',true),
            pressNext:fire('ArrowRight',false),
            heldBack:fire('PageUp',true),
            pressBack:fire('ArrowLeft',false)
          };
        }""")
        assert repeated_keyboard=={
            "before":4,
            "heldNext":{"page":4,"blocked":True},
            "pressNext":{"page":5,"blocked":True},
            "heldBack":{"page":5,"blocked":True},
            "pressBack":{"page":4,"blocked":True}
        },repeated_keyboard
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='4' &&
          !document.querySelector('#reader-canvas').hidden""")

        # V102 : la barre tactile affiche également la position à 320 px,
        # au lieu de disparaître sous les deux gros boutons de navigation.
        page.set_viewport_size({"width":320,"height":568})
        page.wait_for_function("""()=>getComputedStyle(
          document.querySelector('.reader-touch-nav')).display==='grid'""")
        narrow=page.evaluate("""()=>{
          const nav=document.querySelector('.reader-touch-nav');
          const hint=document.querySelector('#reader-touch-location');
          const prev=document.querySelector('#reader-touch-prev');
          const next=document.querySelector('#reader-touch-next');
          const label=hint.getBoundingClientRect();
          const bar=nav.getBoundingClientRect();
          return {width:document.documentElement.scrollWidth,
            mode:getComputedStyle(nav).display,
            hint:getComputedStyle(hint).display,
            label:hint.textContent,top:label.top,bottom:label.bottom,
            barTop:bar.top,barBottom:bar.bottom,
            prevHeight:prev.getBoundingClientRect().height,
            nextHeight:next.getBoundingClientRect().height};
        }""")
        assert narrow["mode"]=="grid" and narrow["hint"]!="none",narrow
        assert narrow["label"]==f"PDF · p. 4 / {source_pages}",narrow
        assert narrow["width"]<=323,narrow
        assert narrow["barTop"]>=0 and narrow["barBottom"]<=569,narrow
        assert narrow["top"]>=narrow["barTop"] and narrow["bottom"]<=569,narrow
        assert min(narrow["prevHeight"],narrow["nextHeight"])>=48,narrow
        assert not failures,failures
        assert not rejected,rejected
        context.close()
        print(f"PASS {browser_type}: vraie page, gestes, transitions PDF, "
              "sauvegarde V31, reprise après rechargement, mode PDF")
    finally:
        browser.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--browser",choices=("chromium","webkit"),required=True)
    args=parser.parse_args()
    with serve_fixture() as fixture:
        original=fixture.split("/tests/e2e/fixtures/")[0]
        with sync_playwright() as p:
            run(p,args.browser,original+"/compte/liseuse.html?edition=demo")


if __name__=="__main__":
    main()
