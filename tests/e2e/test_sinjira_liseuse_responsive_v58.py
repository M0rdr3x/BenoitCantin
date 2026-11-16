#!/usr/bin/env python3
"""SINJIRA V58 : contrôle des tailles mobiles de la vraie page liseuse.

Navigateur réel (Chromium/WebKit), mais écran tactile simulé et PDF synthétique
de 82 pages. Aucune donnée privée, aucun accès Supabase ou réseau externe.
"""
import argparse

from playwright.sync_api import sync_playwright
from test_sinjira_liseuse_mobile_v54 import serve_fixture, swipe
from test_sinjira_liseuse_real_page_v57 import install_isolation, snapshot


VIEWPORTS = (
    ("petit téléphone portrait", 320, 568),
    ("téléphone standard portrait", 390, 844),
    ("téléphone paysage", 844, 390),
    ("tablette portrait", 768, 1024),
    ("grande tablette portrait", 820, 1180),
)


def geometry(page):
    return page.evaluate("""()=>{
      const viewer=document.querySelector('#reader-viewer');
      const text=document.querySelector('#reader-text');
      const nav=document.querySelector('.reader-touch-nav');
      const prev=document.querySelector('#reader-touch-prev');
      const next=document.querySelector('#reader-touch-next');
      const readerStyle=getComputedStyle(text);
      const layout=getComputedStyle(viewer);
      const navStyle=getComputedStyle(nav);
      const box=viewer.getBoundingClientRect();
      const article=text.getBoundingClientRect();
      return {
        screenWidth:innerWidth, screenHeight:innerHeight,
        documentWidth:document.documentElement.scrollWidth,
        viewerWidth:viewer.clientWidth,
        viewerHeight:viewer.clientHeight,
        articleWidth:article.width,articleLeft:article.left,articleRight:article.right,
        viewerLeft:box.left,viewerRight:box.right,
        textFont:parseFloat(readerStyle.fontSize),
        textPaddingLeft:parseFloat(readerStyle.paddingLeft),
        textPaddingRight:parseFloat(readerStyle.paddingRight),
        nextHeight:next.getBoundingClientRect().height,
        prevHeight:prev.getBoundingClientRect().height,
        navDisplay:navStyle.display,
        overflowX:layout.overflowX,
        overflowY:layout.overflowY,
        mode:viewer.dataset.readerLayout,
        textLength:text.textContent.length
      };
    }""")


def run(playwright, engine, origin):
    browser=getattr(playwright,engine).launch()
    try:
        context=browser.new_context(
            viewport={"width":390,"height":844},
            is_mobile=True,has_touch=True,locale="fr-CA",
            device_scale_factor=2,service_workers="block",
            reduced_motion="reduce"
        )
        page=context.new_page()
        # V135 : la voix de test ne joue aucun son et n'appelle aucun
        # service de synthèse externe ; elle mesure les ordres speak/cancel.
        # La simulation est injectée AVANT le chargement de V26 dans le
        # vrai HTML pour que le support speechReady soit déterministe.
        page.add_init_script("""(()=>{
          const voice={
            speakCount:0,cancelCount:0,lastUtterance:null,
            getVoices(){return [{lang:'fr-CA',name:'Voix fictive',voiceURI:'v135-test'}]},
            speak(utterance){this.speakCount++;this.lastUtterance=utterance},
            cancel(){this.cancelCount++},
            pause(){},resume(){},addEventListener(){},removeEventListener(){}
          };
          Object.defineProperty(window,'speechSynthesis',{
            value:voice,configurable:true
          });
          Object.defineProperty(window,'SpeechSynthesisUtterance',{
            value:class{constructor(text){this.text=text}},configurable:true
          });
          window.__v135VoiceLab=voice;
        })()""")
        errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        blocked=install_isolation(page)
        page.goto(origin,wait_until="load")
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-viewer').dataset.readerLayout==='screens'&&
          document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST')""")
        assert snapshot(page)["page"]==3,snapshot(page)
        # V134 : vraie navigation du navigateur hors du livre, puis Retour.
        # Certains moteurs conservent la page BFCache, d'autres la rechargent :
        # vérifier honnêtement les deux chemins, sans prétendre imposer BFCache.
        navigation_before=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          v.scrollTop=Math.min(315,v.scrollHeight-v.clientHeight);
          v.dispatchEvent(new Event('scroll'));
          window.__v134NavigationEvidence={
            beforePage:document.querySelector('#reader-page').value,
            beforeScroll:v.scrollTop,
            persisted:null
          };
          window.addEventListener('pageshow',event=>{
            window.__v134NavigationEvidence.persisted=Boolean(event.persisted);
          });
          return {page:Number(document.querySelector('#reader-page').value),
            scroll:v.scrollTop,layout:v.dataset.readerLayout};
        }""")
        assert navigation_before["page"]==3 and navigation_before["scroll"]>150,navigation_before
        page.goto(origin+"&reader-v134-navigation-probe=1",wait_until="load")
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-viewer')?.dataset.readerLayout==='screens'&&
          document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST')""")
        page.go_back(wait_until="domcontentloaded")
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-viewer')?.dataset.readerLayout==='screens'&&
          document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST')""")
        # Laisser au moteur deux frames pour rétablir l'ancre après pageshow.
        navigation_after=page.evaluate("""async()=>{
          await new Promise(resolve=>requestAnimationFrame(
            ()=>requestAnimationFrame(resolve)));
          const v=document.querySelector('#reader-viewer');
          return {page:Number(document.querySelector('#reader-page').value),
            scroll:v.scrollTop,layout:v.dataset.readerLayout,
            evidence:window.__v134NavigationEvidence||null};
        }""")
        assert navigation_after["page"]==3 and navigation_after["layout"]=="screens",navigation_after
        if navigation_after["evidence"] and navigation_after["evidence"]["persisted"] is True:
            # Un vrai retour BFCache, et non un simple dispatch synthétique.
            assert abs(navigation_after["scroll"]-navigation_before["scroll"])<80,(
                navigation_before,navigation_after
            )
        else:
            # Rechargement normal : pas de faux certificat BFCache ; le livre
            # fictif et les commandes doivent néanmoins être opérationnels.
            assert navigation_after["scroll"]>=0,navigation_after
        # Vérifier que les swipes fonctionnent après une vraie navigation.
        page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          v.scrollTop=0;
          v.dispatchEvent(new Event('scroll'));
        }""")
        navigation_next=swipe(page,-130)
        assert navigation_next["consumed"] and navigation_next["scroll"]>0,navigation_next
        navigation_prev=swipe(page,130)
        assert navigation_prev["consumed"] and navigation_prev["scroll"]==0,navigation_prev
        assert not blocked,blocked
        assert not errors,errors

        # V135 : changer d'application sans pagehide coupe immédiatement
        # la synthèse vocale, même si le navigateur garde l'onglet en mémoire.
        # La voix est un mock muet, jamais un périphérique audio réel.
        page.locator("#reader-voice-play").evaluate("(node)=>node.click()")
        page.wait_for_function("""()=>window.__v135VoiceLab?.speakCount>0""")
        interrupted_voice=page.evaluate("""()=>{
          const lab=window.__v135VoiceLab;
          const previousUtterance=lab.lastUtterance;
          const beforeSpeak=lab.speakCount, beforeCancel=lab.cancelCount;
          const old=Object.getOwnPropertyDescriptor(document,'visibilityState');
          Object.defineProperty(document,'visibilityState',{
            configurable:true,value:'hidden'
          });
          document.dispatchEvent(new Event('visibilitychange'));
          const afterCancel=lab.cancelCount;
          previousUtterance?.onend?.(); // événement tardif d'une voix annulée
          if(old)Object.defineProperty(document,'visibilityState',old);
          else delete document.visibilityState;
          return {
            beforeSpeak,afterSpeak:lab.speakCount,beforeCancel,afterCancel,
            stopDisabled:document.querySelector('#reader-voice-stop').disabled,
            status:document.querySelector('#reader-voice-status').textContent
          };
        }""")
        assert interrupted_voice["afterCancel"]>interrupted_voice["beforeCancel"],interrupted_voice
        assert interrupted_voice["afterSpeak"]==interrupted_voice["beforeSpeak"],interrupted_voice
        assert interrupted_voice["stopDisabled"],interrupted_voice
        assert "arrière-plan" in interrupted_voice["status"],interrupted_voice
        # Les événements d'arrière-plan ne reprennent jamais la narration
        # automatiquement. La personne doit appuyer sur Écouter.
        assert not blocked,blocked
        assert not errors,errors

        # V136 : tentative programmée pendant que la page est cachée,
        # puis course entre lancement asynchrone et visibilité cachée.
        # Aucune voix ne doit être jouée dans les deux situations.
        hidden_voice=page.evaluate("""async()=>{
          const lab=window.__v135VoiceLab;
          const play=document.querySelector('#reader-voice-play');
          const old=Object.getOwnPropertyDescriptor(document,'visibilityState');
          const hidden=()=>{
            Object.defineProperty(document,'visibilityState',{
              configurable:true,value:'hidden'
            });
          };
          const visible=()=>{
            if(old)Object.defineProperty(document,'visibilityState',old);
            else delete document.visibilityState;
          };
          try{
            hidden();
            const baseline=lab.speakCount;
            play.click();
            await Promise.resolve();
            await Promise.resolve();
            const hiddenStart=lab.speakCount;
            visible();
            play.click();
            hidden(); // les await de la voix ne sont pas encore terminés
            await Promise.resolve();
            await Promise.resolve();
            await new Promise(done=>setTimeout(done,0));
            const lateStart=lab.speakCount;
            visible();
            play.click(); // reprise EXPLICITE en premier plan
            await new Promise(done=>setTimeout(done,0));
            const visibleStart=lab.speakCount;
            return {baseline,hiddenStart,lateStart,visibleStart};
          }finally{visible()}
        }""")
        assert hidden_voice["hiddenStart"]==hidden_voice["baseline"],hidden_voice
        assert hidden_voice["lateStart"]==hidden_voice["baseline"],hidden_voice
        assert hidden_voice["visibleStart"]>hidden_voice["baseline"],hidden_voice
        page.locator("#reader-voice-stop").evaluate("(node)=>node.click()")
        assert not blocked,blocked
        assert not errors,errors

        # V139 : un livre peut être masqué sans document.visibilitychange.
        # Le navigateur doit refuser le démarrage audio, arrêter la voix
        # active et ignorer les anciens onend, même si le livre revient vite.
        # La voix est entièrement fictive et muette.
        hidden_content_voice=page.evaluate("""async()=>{
          const lab=window.__v135VoiceLab;
          const content=document.querySelector('#reader-content');
          const play=document.querySelector('#reader-voice-play');
          const stop=document.querySelector('#reader-voice-stop');
          const tick=()=>new Promise(resolve=>setTimeout(resolve,0));
          const twoFrames=()=>new Promise(resolve=>requestAnimationFrame(
            ()=>requestAnimationFrame(resolve)));
          stop.click();
          const baseline=lab.speakCount;
          content.hidden=true;
          try{
            play.click();
            await tick();
            const whileHidden=lab.speakCount;
            content.hidden=false;
            await twoFrames();
            play.click();
            await tick();
            const whileVisible=lab.speakCount;
            const lastUtterance=lab.lastUtterance;
            const cancelsBefore=lab.cancelCount;
            content.hidden=true;
            await tick();
            lastUtterance?.onend?.();
            const afterHide=lab.speakCount;
            const cancelsAfter=lab.cancelCount;
            content.hidden=false;
            await twoFrames();
            play.click(); // chargement voix différé commencé visible
            content.hidden=true;
            content.hidden=false; // fenêtre toujours visible, même tâche
            await tick();
            const afterRapidToggle=lab.speakCount;
            await twoFrames();
            play.click(); // seule une reprise explicite est permise
            await tick();
            const explicitResume=lab.speakCount;
            stop.click();
            return {baseline,whileHidden,whileVisible,
              afterHide,cancelsBefore,cancelsAfter,
              afterRapidToggle,explicitResume};
          }finally{
            content.hidden=false;
          }
        }""")
        assert hidden_content_voice["whileHidden"]==hidden_content_voice["baseline"],hidden_content_voice
        assert hidden_content_voice["whileVisible"]>hidden_content_voice["baseline"],hidden_content_voice
        assert hidden_content_voice["cancelsAfter"]>hidden_content_voice["cancelsBefore"],hidden_content_voice
        assert hidden_content_voice["afterHide"]==hidden_content_voice["whileVisible"],hidden_content_voice
        assert hidden_content_voice["afterRapidToggle"]==hidden_content_voice["afterHide"],hidden_content_voice
        assert hidden_content_voice["explicitResume"]>hidden_content_voice["afterHide"],hidden_content_voice
        assert not blocked,blocked
        assert not errors,errors

        # V129 : régler la police pendant un swipe ancien et revenir à
        # l'ancienne valeur dans la même tâche ne doit pas tourner l'écran.
        preference_gesture=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          const size=document.querySelector('#reader-size');
          const original=size.value;
          const before={page:field.value,scroll:v.scrollTop};
          const start={identifier:129,target:v,clientX:255,clientY:225};
          const fire=(type,touches,changed)=>{
            const e=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(e,{
              touches:{value:touches},changedTouches:{value:changed}
            });
            v.dispatchEvent(e);return e.defaultPrevented;
          };
          fire('touchstart',[start],[start]);
          size.value='24';size.dispatchEvent(new Event('input',{bubbles:true}));
          size.value=original;size.dispatchEvent(new Event('input',{bubbles:true}));
          const consumed=fire('touchend',[],[{...start,clientX:100,clientY:227}]);
          return {before,after:{page:field.value,scroll:v.scrollTop},consumed};
        }""")
        assert preference_gesture["consumed"] is False,preference_gesture
        assert preference_gesture["before"]==preference_gesture["after"],preference_gesture
        # V133 : un retour du cache BFCache invalide l'ancien toucher.
        bfcache_gesture=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          const before={page:field.value,scroll:v.scrollTop};
          const finger={identifier:133,target:v,clientX:255,clientY:225};
          const fire=(type,touches,changed)=>{
            const ev=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(ev,{
              touches:{value:touches},changedTouches:{value:changed}
            });
            v.dispatchEvent(ev);return ev.defaultPrevented;
          };
          fire('touchstart',[finger],[finger]);
          const event=new Event('pageshow');
          Object.defineProperty(event,'persisted',{value:true});
          window.dispatchEvent(event);
          const consumed=fire('touchend',[],[{...finger,clientX:100,clientY:227}]);
          return {before,after:{page:field.value,scroll:v.scrollTop},consumed};
        }""")
        assert bfcache_gesture["consumed"] is False,bfcache_gesture
        assert bfcache_gesture["before"]==bfcache_gesture["after"],bfcache_gesture
        # V132 : selectionchange arrive parfois sans contextmenu sur iOS.
        # Une sélection pendant le balayage ne doit pas tourner d'écran.
        selection_gesture=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          const before={page:field.value,scroll:v.scrollTop};
          const start={identifier:132,target:v,clientX:255,clientY:225};
          const fire=(type,touches,changed)=>{
            const e=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(e,{touches:{value:touches},changedTouches:{value:changed}});
            v.dispatchEvent(e);return e.defaultPrevented;
          };
          fire('touchstart',[start],[start]);
          document.dispatchEvent(new Event('selectionchange'));
          const consumed=fire('touchend',[],[{...start,clientX:100,clientY:227}]);
          return {before,after:{page:field.value,scroll:v.scrollTop},consumed};
        }""")
        assert selection_gesture["consumed"] is False,selection_gesture
        assert selection_gesture["before"]==selection_gesture["after"],selection_gesture
        # V131 : un menu de sélection n'autorise pas une page fantôme.
        context_menu_gesture=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          const before={page:field.value,scroll:v.scrollTop};
          const start={identifier:131,target:v,clientX:255,clientY:225};
          const fire=(type,touches,changed)=>{
            const e=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(e,{touches:{value:touches},changedTouches:{value:changed}});
            v.dispatchEvent(e);return e.defaultPrevented;
          };
          fire('touchstart',[start],[start]);
          const menu=new MouseEvent('contextmenu',{bubbles:true,cancelable:true});
          v.dispatchEvent(menu);
          const consumed=fire('touchend',[],[{...start,clientX:100,clientY:227}]);
          return {before,after:{page:field.value,scroll:v.scrollTop},
            menuCancelled:menu.defaultPrevented,consumed};
        }""")
        assert context_menu_gesture["menuCancelled"] is False,context_menu_gesture
        assert context_menu_gesture["consumed"] is False,context_menu_gesture
        assert context_menu_gesture["before"]==context_menu_gesture["after"],context_menu_gesture
        # V130 : le plein écran invalide un ancien doigt même sans resize.
        focus_gesture=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          const before={page:field.value,scroll:v.scrollTop};
          const start={identifier:130,target:v,clientX:255,clientY:225};
          const fire=(type,touches,changed)=>{
            const e=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(e,{touches:{value:touches},changedTouches:{value:changed}});
            v.dispatchEvent(e);return e.defaultPrevented;
          };
          fire('touchstart',[start],[start]);
          window.dispatchEvent(new Event('sinjira:reader-layout-will-change'));
          const consumed=fire('touchend',[],[{...start,clientX:100,clientY:226}]);
          return {before,after:{page:field.value,scroll:v.scrollTop},consumed};
        }""")
        assert focus_gesture["consumed"] is False,focus_gesture
        assert focus_gesture["before"]==focus_gesture["after"],focus_gesture
        # V128 : orientationchange arrive avant touchend mais la taille
        # finale reste identique. Aucun ancien geste ne doit avancer.
        orientation_gesture=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          const before={page:field.value,scroll:v.scrollTop};
          const start={identifier:128,target:v,clientX:260,clientY:225};
          const fire=(type,touches,changed)=>{
            const e=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(e,{
              touches:{value:touches},changedTouches:{value:changed}
            });
            v.dispatchEvent(e);return e.defaultPrevented;
          };
          fire('touchstart',[start],[start]);
          window.dispatchEvent(new Event('orientationchange'));
          const consumed=fire('touchend',[],[{...start,clientX:100,clientY:228}]);
          return {consumed,before,after:{
            page:field.value,scroll:v.scrollTop}};
        }""")
        assert orientation_gesture["consumed"] is False,orientation_gesture
        assert orientation_gesture["before"]==orientation_gesture["after"],orientation_gesture
        # V126 : la pagination par écrans intercepte touchend en CAPTURE
        # avant V52. Un aller-retour texte→PDF→texte dans la même tâche
        # ne doit donc ni avancer d'écran ni changer de page source.
        paged_transition=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const text=document.querySelector('#reader-text');
          const field=document.querySelector('#reader-page');
          const before={page:field.value,scroll:v.scrollTop,
            layout:v.dataset.readerLayout};
          const start={identifier:126,target:v,clientX:250,clientY:225};
          const end={...start,clientX:100,clientY:227};
          const fire=(type,touches,changed)=>{
            const ev=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(ev,{
              touches:{value:touches},targetTouches:{value:touches},
              changedTouches:{value:changed}
            });
            v.dispatchEvent(ev);return ev.defaultPrevented;
          };
          fire('touchstart',[start],[start]);
          text.hidden=true;text.hidden=false;
          const consumed=fire('touchend',[],[end]);
          return {before,after:{page:field.value,scroll:v.scrollTop,
            layout:v.dataset.readerLayout},consumed};
        }""")
        assert paged_transition["consumed"] is False,paged_transition
        assert paged_transition["before"]==paged_transition["after"],paged_transition
        # V127 : le callback MutationObserver (micro-tâche) peut être livré
        # après la bascule de la vue, MAIS avant touchend. Le geste commencé
        # sur la représentation précédente ne doit pas tourner une page.
        asynchronous_transition=page.evaluate("""async()=>{
          const v=document.querySelector('#reader-viewer');
          const article=document.querySelector('#reader-text');
          const content=document.querySelector('#reader-content');
          const field=document.querySelector('#reader-page');
          const before={page:field.value,scroll:v.scrollTop,
            layout:v.dataset.readerLayout};
          const fire=(type,identifier,touches,changed)=>{
            const e=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(e,{
              touches:{value:touches},targetTouches:{value:touches},
              changedTouches:{value:changed}
            });
            v.dispatchEvent(e);return e.defaultPrevented;
          };
          const turn=async(id,mutate)=>{
            const start={identifier:id,target:v,clientX:250,clientY:225};
            fire('touchstart',id,[start],[start]);
            mutate();
            // Livrer MutationObserver AVANT touchend (aucun record restant).
            await Promise.resolve();
            return fire('touchend',id,[],[{...start,clientX:100,clientY:227}]);
          };
          const textConsumed=await turn(127,()=>{
            article.hidden=true;article.hidden=false;
          });
          const contentConsumed=await turn(128,()=>{
            content.hidden=true;content.hidden=false;
          });
          return {before,after:{page:field.value,scroll:v.scrollTop,
            layout:v.dataset.readerLayout},textConsumed,contentConsumed};
        }""")
        assert not asynchronous_transition["textConsumed"],asynchronous_transition
        assert not asynchronous_transition["contentConsumed"],asynchronous_transition
        assert asynchronous_transition["before"]==asynchronous_transition["after"],(
            asynchronous_transition
        )
        # V122 : basculement PDF vers texte continu pendant un contact,
        # sans changer le numéro ni émettre sinjira:reader-page-change.
        mode_transition=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const text=document.querySelector('#reader-text');
          const field=document.querySelector('#reader-page');
          const paged=document.querySelector('#reader-screens-enabled');
          const before=field.value;
          paged.checked=false;
          paged.dispatchEvent(new Event('change',{bubbles:true}));
          text.hidden=true;
          const start={identifier:122,target:v,clientX:260,clientY:224};
          const end={...start,clientX:112,clientY:227};
          const fire=(type,touches,changed)=>{
            const ev=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(ev,{
              touches:{value:touches},targetTouches:{value:touches},
              changedTouches:{value:changed}
            });
            v.dispatchEvent(ev);return ev.defaultPrevented;
          };
          fire('touchstart',[start],[start]);
          text.hidden=false;
          const consumed=fire('touchend',[],[end]);
          const after=field.value;
          paged.checked=true;
          paged.dispatchEvent(new Event('change',{bubbles:true}));
          return {consumed,after,before,layout:v.dataset.readerLayout};
        }""")
        assert mode_transition=={
            "consumed":False,"after":"3","before":"3","layout":"screens"
        },mode_transition
        # V123 : PDF→texte→PDF avant le relâchement, même page et même
        # représentation finale. Attendre une micro-tâche pour remettre
        # l'observateur de mutations entre l'aller-retour et touchend.
        transient_mode=page.evaluate("""async()=>{
          const v=document.querySelector('#reader-viewer');
          const text=document.querySelector('#reader-text');
          const field=document.querySelector('#reader-page');
          const paged=document.querySelector('#reader-screens-enabled');
          const before=field.value;
          paged.checked=false;
          paged.dispatchEvent(new Event('change',{bubbles:true}));
          text.hidden=true;
          await Promise.resolve();
          const start={identifier:123,target:v,clientX:260,clientY:225};
          const end={...start,clientX:100,clientY:228};
          const fire=(type,touches,changed)=>{
            const ev=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(ev,{
              touches:{value:touches},targetTouches:{value:touches},
              changedTouches:{value:changed}
            });
            v.dispatchEvent(ev);return ev.defaultPrevented;
          };
          fire('touchstart',[start],[start]);
          text.hidden=false;text.hidden=true;
          await Promise.resolve();
          const consumed=fire('touchend',[],[end]);
          const after=field.value;
          text.hidden=false;
          paged.checked=true;
          paged.dispatchEvent(new Event('change',{bubbles:true}));
          return {consumed,after,before,layout:v.dataset.readerLayout};
        }""")
        assert transient_mode=={
            "consumed":False,"after":"3","before":"3","layout":"screens"
        },transient_mode
        # V125 : cette fois AUCUN await entre PDF->texte->PDF et
        # touchend. MutationObserver n'a pas encore été appelé :
        # takeRecords doit invalider le contact dans la même tâche JS.
        synchronous_mode=page.evaluate("""async()=>{
          const v=document.querySelector('#reader-viewer');
          const text=document.querySelector('#reader-text');
          const field=document.querySelector('#reader-page');
          const paged=document.querySelector('#reader-screens-enabled');
          const before=field.value;
          paged.checked=false;
          paged.dispatchEvent(new Event('change',{bubbles:true}));
          text.hidden=true;
          await Promise.resolve();
          const start={identifier:125,target:v,clientX:250,clientY:225};
          const end={...start,clientX:100,clientY:228};
          const fire=(type,touches,changed)=>{
            const ev=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(ev,{
              touches:{value:touches},targetTouches:{value:touches},
              changedTouches:{value:changed}
            });
            v.dispatchEvent(ev);return ev.defaultPrevented;
          };
          fire('touchstart',[start],[start]);
          text.hidden=false;
          text.hidden=true;
          const consumed=fire('touchend',[],[end]);
          const after=field.value;
          text.hidden=false;
          paged.checked=true;
          paged.dispatchEvent(new Event('change',{bubbles:true}));
          return {consumed,before,after,layout:v.dataset.readerLayout};
        }""")
        assert synchronous_mode=={
            "consumed":False,"before":"3","after":"3","layout":"screens"
        },synchronous_mode
        # V121 : le PDF dispose d'un statut vocal sans doublonner les
        # écrans de texte, et sa région est visuellement dissimulée.
        spoken=page.evaluate("""()=>{
          const field=document.querySelector('#reader-page');
          const article=document.querySelector('#reader-text');
          const viewer=document.querySelector('#reader-viewer');
          const region=document.querySelector('#reader-page-announcement');
          const before=field.value,wasHidden=article.hidden;
          article.hidden=true;
          viewer.dispatchEvent(new Event('sinjira:reader-page-change'));
          const initial=region.textContent;
          field.value=String(Number(before)+1);
          viewer.dispatchEvent(new Event('sinjira:reader-page-change'));
          const updated=region.textContent;
          viewer.dispatchEvent(new Event('sinjira:reader-page-change'));
          const repeated=region.textContent;
          const style=getComputedStyle(region),rect=region.getBoundingClientRect();
          const attrs={role:region.getAttribute('role'),
            live:region.getAttribute('aria-live'),
            rendered:style.display!=='none'&&style.visibility!=='hidden',
            width:rect.width,height:rect.height};
          article.hidden=wasHidden;field.value=before;
          viewer.dispatchEvent(new Event('sinjira:reader-page-change'));
          return {initial,updated,repeated,attrs,page:Number(field.value)};
        }""")
        assert spoken["initial"]=="",spoken
        # Le parcours V58 utilise un vrai moteur PDF fictif de 82 pages,
        # tandis que la fixture minimale V54 n'en contient que cinq :
        # lire le total canonique au lieu d'imposer un nombre de test.
        expected_total=page.locator("#reader-total").inner_text().strip()
        assert expected_total.isdigit(),expected_total
        assert spoken["updated"]==f"Page 4 sur {expected_total} du livre.",spoken
        assert spoken["repeated"]==spoken["updated"],spoken
        assert spoken["attrs"]["role"]=="status" and spoken["attrs"]["live"]=="polite",spoken
        assert spoken["attrs"]["rendered"],spoken
        assert spoken["attrs"]["width"]<=1 and spoken["attrs"]["height"]<=1,spoken
        assert spoken["page"]==3,spoken
        # V124 : le statut PDF ne doit pas conserver la page de l'ancien
        # roman lors d'un masquage temporaire ou d'un retour aux écrans.
        stale=page.evaluate("""async()=>{
          const v=document.querySelector('#reader-viewer');
          const article=document.querySelector('#reader-text');
          const content=document.querySelector('#reader-content');
          const field=document.querySelector('#reader-page');
          const region=document.querySelector('#reader-page-announcement');
          const before=field.value,wasHidden=article.hidden;
          article.hidden=true;
          field.value='4';
          v.dispatchEvent(new Event('sinjira:reader-page-change'));
          const announced=region.textContent;
          content.hidden=true;
          await Promise.resolve();
          const cleared=region.textContent;
          content.hidden=false;
          await Promise.resolve();
          const restored=region.textContent;
          v.dispatchEvent(new Event('sinjira:reader-page-change'));
          const redundant=region.textContent;
          article.hidden=wasHidden;
          field.value=before;
          v.dispatchEvent(new Event('sinjira:reader-page-change'));
          return {announced,cleared,restored,redundant,page:Number(field.value),
            layout:v.dataset.readerLayout,afterScreens:region.textContent};
        }""")
        assert stale["announced"]==f"Page 4 sur {expected_total} du livre.",stale
        assert stale["cleared"]==stale["restored"]==stale["redundant"]=="",stale
        assert stale["page"]==3 and stale["layout"]=="screens",stale
        assert stale["afterScreens"]=="",stale
        # V119 : contrôle sur le vrai navigateur : un effet est émis
        # par chaque vrai geste en l'absence de préférence motion réduite;
        # aucun effet lorsque le lecteur demande moins d'animation.
        page.evaluate("""()=>{
          window.__v119Frames=[];
          const v=document.querySelector('#reader-viewer');
          v.__oldAnimate=v.animate;
          v.animate=function(frames,options){
            const record={frame:frames[0].boxShadow,duration:options.duration,
              cancellations:0};
            const listeners=new Map();
            window.__v119Frames.push(record);
            return {
              addEventListener:(name,cb)=>listeners.set(name,cb),
              cancel(){record.cancellations++;listeners.get('cancel')?.()}
            };
          };
        }""")
        page.emulate_media(reduced_motion="no-preference")
        fwd=swipe(page,-130)
        rev=swipe(page,130)
        assert fwd["consumed"] and rev["consumed"]
        assert snapshot(page)["page"]==3 and snapshot(page)["scroll"]==0
        flashes=page.evaluate("window.__v119Frames")
        assert len(flashes)==2,flashes
        assert "inset -26px" in flashes[0]["frame"],flashes
        assert "inset 26px" in flashes[1]["frame"],flashes
        assert flashes[0]["cancellations"]==1,(
            "V120 : pas de deux effets empilés lors de swipes successifs",flashes
        )
        page.emulate_media(reduced_motion="reduce")
        ignored=swipe(page,-130)
        assert ignored["consumed"]
        assert len(page.evaluate("window.__v119Frames"))==2,(
            "V119 : le choix de réduire les animations doit être respecté"
        )
        assert page.evaluate("window.__v119Frames[1].cancellations")==1,(
            "V120 : le passage à reduce coupe l'effet encore en cours"
        )
        recovered=swipe(page,130)
        assert recovered["consumed"] and snapshot(page)["scroll"]==0
        page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          v.animate=v.__oldAnimate;
          delete v.__oldAnimate;
        }""")
        # V118 : l'événement V26 invalide un touchend en attente, même
        # si le numéro de page source reste le même pendant le rechargement.
        same_page_reload=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          const start={identifier:118,target:v,clientX:255,clientY:230};
          const end={...start,clientX:110,clientY:233};
          const fire=(type,touches,changed)=>{
            const ev=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(ev,{
              touches:{value:touches},targetTouches:{value:touches},
              changedTouches:{value:changed}
            });
            v.dispatchEvent(ev);return ev.defaultPrevented;
          };
          fire('touchstart',[start],[start]);
          v.dispatchEvent(new Event('sinjira:reader-page-change'));
          const consumed=fire('touchend',[],[end]);
          return {consumed,scroll:v.scrollTop,page:Number(field.value)};
        }""")
        assert same_page_reload=={"consumed":False,"scroll":0,"page":3},same_page_reload
        # V117 : une page source modifiée pendant un contact invalide
        # l'ancien touchend. La page de test revient ensuite à son numéro.
        replaced_page=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const field=document.querySelector('#reader-page');
          const start={identifier:77,target:v,clientX:255,clientY:230};
          const end={...start,clientX:110,clientY:233};
          const fire=(type,touches,changed)=>{
            const ev=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(ev,{
              touches:{value:touches},targetTouches:{value:touches},
              changedTouches:{value:changed}
            });
            v.dispatchEvent(ev);
            return ev.defaultPrevented;
          };
          const current=field.value;
          fire('touchstart',[start],[start]);
          field.value=String(Number(current)+1);
          const consumed=fire('touchend',[],[end]);
          field.value=current;
          return {consumed,scroll:v.scrollTop,page:Number(field.value)};
        }""")
        assert replaced_page=={"consumed":False,"scroll":0,"page":3},replaced_page
        # V116 : trajectoire gauche/droite inversée en vrais événements DOM,
        # puis un véritable geste pour confirmer que la liseuse reste fluide.
        reverse=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const fire=(type,touches,changed)=>{
            const ev=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(ev,{
              touches:{value:touches},targetTouches:{value:touches},
              changedTouches:{value:changed}
            });
            v.dispatchEvent(ev);return ev.defaultPrevented;
          };
          const gesture=(a,b,c)=>{
            const start={identifier:33,clientX:a,clientY:235,target:v};
            const mid={...start,clientX:b};
            const end={...start,clientX:c,clientY:238};
            fire('touchstart',[start],[start]);
            fire('touchmove',[mid],[mid]);
            return fire('touchend',[],[end]);
          };
          return {
            left:gesture(200,280,65),
            right:gesture(200,120,340),
            scroll:v.scrollTop,
            page:Number(document.querySelector('#reader-page').value)
          };
        }""")
        assert reverse=={"left":False,"right":False,"scroll":0,"page":3},reverse
        advance=swipe(page,-130)
        assert advance["consumed"] and snapshot(page)["scroll"]>0,advance
        retreat=swipe(page,130)
        assert retreat["consumed"] and snapshot(page)["scroll"]==0,retreat
        # V113 : les gestes restent annoncés dans une seule ligne d'aide
        # tandis que les explications sont dépliables au toucher/clavier.
        guide=page.locator(".reader-swipe-help")
        guide_summary=guide.locator("summary")
        guide_text=guide.locator("p")
        assert guide.is_visible(),"V113 : le mode d'emploi mobile est invisible"
        assert not guide.evaluate("(el)=>el.open"),"V113 : aide longue ouverte au départ"
        assert not guide_text.is_visible(),"V113 : long paragraphe encombre le roman"
        assert guide_summary.evaluate("(el)=>el.getBoundingClientRect().height")>=44
        assert "gauche pour avancer" in guide_summary.inner_text()
        assert "droite pour revenir" in guide_summary.inner_text()
        guide_summary.click()
        assert guide.evaluate("(el)=>el.open")
        assert guide_text.is_visible()
        guide_summary.focus()
        page.keyboard.press("Enter")
        assert not guide.evaluate("(el)=>el.open"),(
            "V113 : impossible de replier l'aide au clavier"
        )
        assert snapshot(page)["page"]==3,snapshot(page)

        # V110 : sur téléphone les panneaux ne font pas défiler le livre
        # hors du premier écran. Le lien direct est tactile et au clavier.
        assert not page.locator(".reader-settings").evaluate("(el)=>el.open")
        assert not page.locator(".reader-audio-settings").evaluate("(el)=>el.open")
        quick=page.locator(".reader-mobile-read-link")
        assert quick.is_visible(),"V110: accès rapide au livre invisible sur téléphone"
        assert quick.evaluate("(el)=>el.getBoundingClientRect().height")>=44
        # V112 : quand V26 masque le roman, le lien mobile disparaît.
        availability=page.evaluate("""async()=>{
          const content=document.querySelector('#reader-content');
          const link=document.querySelector('#reader-mobile-read-link');
          const next=()=>new Promise(resolve=>requestAnimationFrame(resolve));
          content.hidden=true;await next();
          const denied={hidden:link.hidden,visible:getComputedStyle(link).display!=='none'};
          content.hidden=false;await next();
          const restored={hidden:link.hidden,visible:getComputedStyle(link).display!=='none'};
          return {denied,restored};
        }""")
        assert availability["denied"]=={"hidden":True,"visible":False},availability
        assert availability["restored"]=={"hidden":False,"visible":True},availability
        quick.click()
        assert page.evaluate("location.hash")=="#reader-viewer"
        assert page.evaluate("document.activeElement?.id")=="reader-viewer",(
            "V115 : le lien doit rendre les flèches utilisables depuis le livre"
        )
        page.keyboard.press("ArrowRight")
        assert snapshot(page)["page"]==3 and snapshot(page)["scroll"]>0,(
            "V115 : le raccourci mobile doit permettre de lire l'écran suivant"
        )
        page.keyboard.press("ArrowLeft")
        assert snapshot(page)["page"]==3 and snapshot(page)["scroll"]==0,(
            "V115 : retour à l'écran d'origine sans perte de position"
        )
        summary=page.locator(".reader-settings > summary")
        summary.click()
        assert page.locator(".reader-settings").evaluate("(el)=>el.open")
        summary.click()
        assert not page.locator(".reader-settings").evaluate("(el)=>el.open")

        # V111 : lorsqu'une tablette repasse d'un affichage PC au mobile,
        # les panneaux automatiques se replient sans toucher à la page lue.
        # Une ouverture choisie à la main reste prioritaire à chaque resize.
        page.set_viewport_size({"width":1280,"height":900})
        # Le premier panneau vient d'être fermé MANUELLEMENT ci-dessus :
        # le redimensionnement ne doit surtout pas écraser ce choix.
        page.wait_for_function("""()=>!document.querySelector('.reader-settings').open&&
          document.querySelector('.reader-audio-settings').open""")
        # Pour vérifier la transition automatique des DEUX panneaux, il faut
        # une nouvelle session de page avant toute interaction utilisateur.
        page.reload(wait_until="load")
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('.reader-settings').open&&
          document.querySelector('.reader-audio-settings').open""")
        page.set_viewport_size({"width":820,"height":1180})
        page.wait_for_function("""()=>!document.querySelector('.reader-settings').open&&
          !document.querySelector('.reader-audio-settings').open""")
        assert snapshot(page)["page"]==3,snapshot(page)
        summary.click()
        assert page.locator(".reader-settings").evaluate("(el)=>el.open")
        page.set_viewport_size({"width":1280,"height":900})
        page.wait_for_function("""()=>document.querySelector('.reader-audio-settings').open""")
        page.set_viewport_size({"width":390,"height":844})
        page.wait_for_function("""()=>!document.querySelector('.reader-audio-settings').open""")
        assert page.locator(".reader-settings").evaluate("(el)=>el.open"),(
            "V111 : une ouverture volontaire ne doit pas disparaître après resize"
        )
        summary.click()
        assert not page.locator(".reader-settings").evaluate("(el)=>el.open")
        assert snapshot(page)["page"]==3,snapshot(page)

        # V61 : les touches de lecture n'interceptent pas la navigation du site.
        page.evaluate("document.querySelector('#reader-viewer').blur()")
        page.keyboard.press("ArrowRight")
        away=snapshot(page)
        assert away["page"]==3 and away["scroll"]==0,away
        # Après entrée explicite dans la zone de livre, les flèches agissent
        # par portions d'écran et respectent le retour arrière.
        page.locator("#reader-viewer").focus()
        page.keyboard.press("ArrowRight")
        on_reader=snapshot(page)
        assert on_reader["page"]==3 and on_reader["scroll"]>0,on_reader
        page.keyboard.press("ArrowLeft")
        back=snapshot(page)
        assert back["page"]==3 and back["scroll"]==0,back
        # Un champ de réglage peut récupérer le focus sans tourner le roman.
        page.locator("#reader-page").focus()
        page.keyboard.press("ArrowRight")
        input_focus=snapshot(page)
        assert input_focus["page"]==3 and input_focus["scroll"]==0,input_focus
        assert "Écran suivant" in page.locator("#reader-touch-next").get_attribute("aria-label")
        assert "Écran précédent" in page.locator("#reader-touch-prev").get_attribute("aria-label")

        # Chaque taille conserve le livre, les boutons accessibles, le texte
        # réorganisé et une navigation par portion plutôt que par page PDF.
        for label,width,height in VIEWPORTS:
            page.set_viewport_size({"width":width,"height":height})
            page.wait_for_function("""()=>document.querySelector('#reader-viewer')
              .dataset.readerLayout==='screens'""")
            page.wait_for_timeout(80)
            info=geometry(page)
            assert info["mode"]=="screens",(label,info)
            assert info["textLength"]>2000,(label,info)
            # V102 : 320–400 px => barre à deux lignes (grille) pour
            # garder la position visible sous les boutons ; au-delà,
            # la barre conserve sa présentation horizontale historique.
            expected_display="grid" if width<=400 else "flex"
            assert info["navDisplay"]==expected_display,(label,info)
            # V114 : même sur iPad portrait (768/820 px), l'aide doit rester
            # facile à ouvrir et la longue notice repliée au premier affichage.
            guide=page.locator(".reader-swipe-help")
            summary=guide.locator("summary")
            assert guide.is_visible(),(label,"guide de lecture absent")
            assert not guide.evaluate("(el)=>el.open"),(label,"aide ouverte")
            assert not guide.locator("p").is_visible(),(label,"texte encombrant")
            assert summary.evaluate("(el)=>el.getBoundingClientRect().height")>=44,(
                label,"cible tactile insuffisante")
            if width in (768,820):
                summary.click()
                assert guide.evaluate("(el)=>el.open"),(label,"aide impossible à ouvrir")
                assert guide.locator("p").is_visible(),(label,"notice inaccessible")
                summary.click()
                assert not guide.evaluate("(el)=>el.open"),(label,"aide impossible à refermer")
                assert snapshot(page)["page"]==3,(label,snapshot(page))
            assert min(info["nextHeight"],info["prevHeight"])>=44,(label,info)
            assert info["viewerWidth"]>=280,(label,info)
            # V68 : écran 390 px de haut, ne pas imposer 340/410 px de lecteur.
            if label=="téléphone paysage":
                assert 175<=info["viewerHeight"]<=300,(label,info)
                assert info["viewerHeight"]<=height-100,(label,info)
            assert info["documentWidth"]<=width+3,(label,info)
            assert info["articleWidth"]<=info["viewerWidth"]+3,(label,info)
            assert info["articleLeft"]>=info["viewerLeft"]-3,(label,info)
            assert info["articleRight"]<=info["viewerRight"]+3,(label,info)
            assert not errors,(label,errors)

            # Le code doit avancer l'écran sans changer la source PDF.
            page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")
            turn=swipe(page,-130)
            after=snapshot(page)
            assert turn["consumed"] and after["page"]==3 and after["scroll"]>0,(
                label,turn,{"page":after["page"],"scroll":after["scroll"]}
            )
            page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")

        # Test typographique extrême réellement prévu dans l'interface :
        # les plus grands caractères doivent reflow et la page reste navigable.
        page.set_viewport_size({"width":320,"height":568})
        # Les coordonnées caret*FromPoint sont relatives à la fenêtre.
        # Afficher réellement le livre avant d'évaluer un texte visible.
        page.locator("#reader-viewer").scroll_into_view_if_needed()
        # V63 : mesurer un caractère effectivement visible AVANT la
        # modification du CSS. L'ancre reste en mémoire navigateur uniquement.
        anchored=page.evaluate("""async()=>{
          const m=await import('/assets/js/sinjira-liseuse-reflow-v53.mjs?v=53.11.16.146');
          const viewer=document.querySelector('#reader-viewer');
          const text=document.querySelector('#reader-text');
          viewer.scrollTop=Math.min(1850,viewer.scrollHeight-viewer.clientHeight-300);
          await new Promise(resolve=>requestAnimationFrame(resolve));
          const anchor=m.captureReaderTextAnchor({viewer,text});
          window.__v63Anchor=anchor;
          const bounds=viewer.getBoundingClientRect();
          const pageBounds=text.getBoundingClientRect();
          const style=getComputedStyle(text);
          const px=Math.min(pageBounds.right-8,Math.max(
            pageBounds.left+8,pageBounds.left+parseFloat(style.paddingLeft)+18));
          const py=Math.min(bounds.bottom-12,bounds.top+
            Math.max(24,Math.min(85,bounds.height*.14)));
          const pos=document.caretPositionFromPoint?.(px,py);
          const fallback=document.caretRangeFromPoint?.(px,py);
          return {available:Boolean(anchor),offset:anchor?.offset||0,
            position:viewer.scrollTop,viewerTop:bounds.top,
            viewerBottom:bounds.bottom,viewportHeight:innerHeight,
            textLeft:pageBounds.left,textRight:pageBounds.right,
            textNodes:text.childNodes.length,x:px,y:py,
            caretNodeType:pos?.offsetNode?.nodeType,
            caretInside:pos?.offsetNode?text.contains(pos.offsetNode):null,
            caretOffset:pos?.offset,
            fallbackNodeType:fallback?.startContainer?.nodeType,
            fallbackInside:fallback?.startContainer?
              text.contains(fallback.startContainer):null,
            caretApi:typeof document.caretPositionFromPoint,
            rangeApi:typeof document.caretRangeFromPoint,
            caretParent:pos?.offsetNode?.parentElement?.id||pos?.offsetNode?.parentElement?.className,
            fallbackParent:fallback?.startContainer?.parentElement?.id||
              fallback?.startContainer?.parentElement?.className,
            elementAtPoint:document.elementFromPoint(px,py)?.id||
              document.elementFromPoint(px,py)?.className,
            textTop:pageBounds.top,textBottom:pageBounds.bottom};
        }""")
        assert anchored["available"],("V63: caret incapable de repérer le texte",anchored)
        assert anchored["position"]>300,anchored
        page.evaluate("""()=>{
          const size=document.querySelector('#reader-size');
          size.value='34';size.dispatchEvent(new Event('input',{bubbles:true}));
          const line=document.querySelector('#reader-line-height');
          line.value='2.1';line.dispatchEvent(new Event('change',{bubbles:true}));
        }""")
        page.wait_for_function("""()=>{
          const t=document.querySelector('#reader-text');
          return Math.abs(parseFloat(getComputedStyle(t).fontSize)-34)<.01;
        }""")
        page.wait_for_timeout(180)
        # Le même caractère doit conserver son emplacement dans la zone du
        # livre malgré le passage à 34 px; un ratio seul ne suffit pas.
        preserved=page.evaluate("""()=>{
          const a=window.__v63Anchor;
          const viewer=document.querySelector('#reader-viewer');
          const node=a?.node;
          if(!node||!node.isConnected)return {valid:false};
          const range=document.createRange();
          range.setStart(node,a.offset);range.setEnd(node,a.offset+1);
          const rect=Array.from(range.getClientRects()).find(r=>r.height>0);
          return {
            valid:Boolean(rect),
            displacement:rect?Math.abs(
              rect.top-viewer.getBoundingClientRect().top-a.relativeY):999,
            scroll:viewer.scrollTop
          };
        }""")
        assert preserved["valid"] and preserved["displacement"]<24,(
            "V63: perte du caractère lu à l'agrandissement",anchored,preserved
        )
        large=geometry(page)
        assert large["textFont"]==34,large
        assert large["documentWidth"]<=323,large
        assert large["articleWidth"]<=large["viewerWidth"]+3,large
        assert snapshot(page)["page"]==3,snapshot(page)

        # V64 : après une police agrandie, changer l'orientation du téléphone
        # doit conserver le caractère lu, pas uniquement un ratio d'écran.
        before_rotation=page.evaluate("""async()=>{
          const m=await import('/assets/js/sinjira-liseuse-reflow-v53.mjs?v=53.11.16.146');
          const viewer=document.querySelector('#reader-viewer');
          const text=document.querySelector('#reader-text');
          const anchor=m.captureReaderTextAnchor({viewer,text});
          window.__v64RotateAnchor=anchor;
          return {valid:Boolean(anchor),scroll:viewer.scrollTop};
        }""")
        assert before_rotation["valid"],(
            "V64: ancre indisponible avant rotation",before_rotation
        )
        page.set_viewport_size({"width":568,"height":320})
        page.wait_for_function("""()=>{
          const v=document.querySelector('#reader-viewer');
          return innerWidth===568&&v.dataset.readerLayout==='screens';
        }""")
        landscape=geometry(page)
        assert 175<=landscape["viewerHeight"]<=240,(
            "V68: liseuse trop haute pour téléphone 568×320 en paysage",
            landscape
        )
        assert min(landscape["nextHeight"],landscape["prevHeight"])>=44,(
            "V68: les commandes tactiles doivent rester grandes",landscape
        )
        # Sur WebKit, le reflow peut finir après deux frames lorsque la CI
        # lance d'autres moteurs en parallèle. Attendre la vraie CONDITION
        # fonctionnelle (même caractère à <35 px), sans assouplir le seuil.
        try:
            page.wait_for_function("""()=>{
              const a=window.__v64RotateAnchor;
              const v=document.querySelector('#reader-viewer');
              if(!a?.node?.isConnected)return false;
              const range=document.createRange();
              range.setStart(a.node,a.offset);
              range.setEnd(a.node,a.offset+1);
              const r=Array.from(range.getClientRects()).find(x=>x.height>0);
              return Boolean(r) && Math.abs(
                r.top-v.getBoundingClientRect().top-a.relativeY
              )<35;
            }""",timeout=6500)
        except Exception:
            pass  # conserver l'assertion détaillée ci-dessous
        after_rotation=page.evaluate("""()=>{
          const a=window.__v64RotateAnchor;
          const viewer=document.querySelector('#reader-viewer');
          if(!a?.node?.isConnected)return {valid:false};
          const range=document.createRange();
          range.setStart(a.node,a.offset);range.setEnd(a.node,a.offset+1);
          const rect=Array.from(range.getClientRects()).find(r=>r.height>0);
          return {
            valid:Boolean(rect),
            displacement:rect?Math.abs(
              rect.top-viewer.getBoundingClientRect().top-a.relativeY):999,
            scroll:viewer.scrollTop
          };
        }""")
        assert after_rotation["valid"] and after_rotation["displacement"]<35,(
            "V64: le passage lu se perd après une rotation simulée",
            before_rotation,after_rotation
        )
        assert snapshot(page)["page"]==3,snapshot(page)
        page.set_viewport_size({"width":320,"height":568})
        page.wait_for_timeout(140)

        page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")
        result=swipe(page,-130)
        assert result["consumed"] and snapshot(page)["page"]==3,result

        # V88 : le mode lecture plein écran change la hauteur du conteneur
        # sans événement window.resize. Conserver le CARACTÈRE LU lors de
        # l'activation et de la désactivation, pas seulement le numéro PDF.
        page.locator("#reader-viewer").scroll_into_view_if_needed()
        focus_start=page.evaluate("""async()=>{
          const mod=await import('/assets/js/sinjira-liseuse-reflow-v53.mjs?v=53.11.16.146');
          const v=document.querySelector('#reader-viewer');
          const t=document.querySelector('#reader-text');
          v.scrollTop=Math.min(1400,v.scrollHeight-v.clientHeight-400);
          await new Promise(resolve=>requestAnimationFrame(resolve));
          const anchor=mod.captureReaderTextAnchor({viewer:v,text:t});
          window.__v88BeforeFocus=anchor;
          return {captured:Boolean(anchor),scroll:v.scrollTop};
        }""")
        assert focus_start["captured"] and focus_start["scroll"]>200,focus_start
        page.locator("#reader-focus").evaluate("(node)=>node.click()")
        assert page.locator("body").evaluate(
            "(node)=>node.classList.contains('reader-focus-mode')"
        ),"Mode lecture plein écran inaccessible"
        focused=geometry(page)
        assert focused["viewerHeight"]>=280,focused
        page.wait_for_function("""()=>{
          const a=window.__v88BeforeFocus;
          if(!a?.node?.isConnected)return false;
          const v=document.querySelector('#reader-viewer');
          const r=document.createRange();r.setStart(a.node,a.offset);
          r.setEnd(a.node,a.offset+1);
          const rect=Array.from(r.getClientRects()).find(box=>box.height>0);
          return Boolean(rect)&&Math.abs(
            rect.top-v.getBoundingClientRect().top-a.relativeY)<35;
        }""",timeout=7000)
        # En mode plein écran, le bouton peut reprendre le focus et faire
        # défiler le DOCUMENT extérieur, sans déplacer le scroll du livre.
        # Pour tester la capture caret, replacer le livre dans le viewport.
        page.locator("#reader-viewer").scroll_into_view_if_needed()
        page.evaluate("""()=>new Promise(done=>
          requestAnimationFrame(()=>requestAnimationFrame(done)))""")
        focus_during=page.evaluate("""async()=>{
          const mod=await import('/assets/js/sinjira-liseuse-reflow-v53.mjs?v=53.11.16.146');
          const v=document.querySelector('#reader-viewer');
          const t=document.querySelector('#reader-text');
          const anchor=mod.captureReaderTextAnchor({viewer:v,text:t});
          window.__v88DuringFocus=anchor;
          return {captured:Boolean(anchor),scroll:v.scrollTop};
        }""")
        assert focus_during["captured"],focus_during
        page.locator("#reader-focus").evaluate("(node)=>node.click()")
        assert not page.locator("body").evaluate(
            "(node)=>node.classList.contains('reader-focus-mode')"
        ),"Impossible de quitter le plein écran"
        page.wait_for_function("""()=>{
          const a=window.__v88DuringFocus;
          if(!a?.node?.isConnected)return false;
          const v=document.querySelector('#reader-viewer');
          const r=document.createRange();r.setStart(a.node,a.offset);
          r.setEnd(a.node,a.offset+1);
          const rect=Array.from(r.getClientRects()).find(box=>box.height>0);
          return Boolean(rect)&&Math.abs(
            rect.top-v.getBoundingClientRect().top-a.relativeY)<35;
        }""",timeout=7000)

        # V89 : le texte lu en défilement continu doit rester au même endroit
        # lorsque l'utilisateur réactive les pages d'écran (pas d'ancre
        # ancienne restée en mémoire depuis le mode paginé).
        page.locator("#reader-screens-enabled").uncheck()
        assert page.locator("#reader-touch-next").get_attribute("aria-label")=="Page du livre suivante"
        assert page.locator("#reader-touch-prev").get_attribute("aria-label")=="Page du livre précédente"
        page.locator("#reader-viewer").scroll_into_view_if_needed()
        continuous=page.evaluate("""async()=>{
          const m=await import('/assets/js/sinjira-liseuse-reflow-v53.mjs?v=53.11.16.146');
          const v=document.querySelector('#reader-viewer');
          const t=document.querySelector('#reader-text');
          v.scrollTop=Math.min(2200,Math.max(0,v.scrollHeight-v.clientHeight-300));
          await new Promise(done=>requestAnimationFrame(done));
          const anchor=m.captureReaderTextAnchor({viewer:v,text:t});
          window.__v89ContinuousAnchor=anchor;
          return {captured:Boolean(anchor),scroll:v.scrollTop};
        }""")
        assert continuous["captured"] and continuous["scroll"]>200,continuous
        page.locator("#reader-screens-enabled").check()
        page.wait_for_function("""()=>{
          const a=window.__v89ContinuousAnchor;
          if(!a?.node?.isConnected)return false;
          const v=document.querySelector('#reader-viewer');
          if(v.dataset.readerLayout!=='screens')return false;
          const r=document.createRange();
          r.setStart(a.node,a.offset);r.setEnd(a.node,a.offset+1);
          const rect=Array.from(r.getClientRects()).find(x=>x.height>0);
          return Boolean(rect)&&Math.abs(
            rect.top-v.getBoundingClientRect().top-a.relativeY)<35;
        }""",timeout=7000)
        assert "Écran suivant" in page.locator("#reader-touch-next").get_attribute("aria-label")

        # V90 : simuler le changement de hauteur dvh dû aux barres système
        # sans window.resize, sur le vrai lecteur avec sa vraie pagination.
        # Ne pas accéder au réseau ou au contenu privé.
        page.locator("#reader-viewer").scroll_into_view_if_needed()
        before_chrome=page.evaluate("""async()=>{
          const mod=await import('/assets/js/sinjira-liseuse-reflow-v53.mjs?v=53.11.16.146');
          const viewer=document.querySelector('#reader-viewer');
          const text=document.querySelector('#reader-text');
          viewer.scrollTop=Math.min(1750,Math.max(0,viewer.scrollHeight-viewer.clientHeight-350));
          await new Promise(done=>requestAnimationFrame(done));
          const a=mod.captureReaderTextAnchor({viewer,text});
          window.__v90ChromeAnchor=a;
          return {captured:Boolean(a),scroll:viewer.scrollTop,height:viewer.clientHeight,
            hasViewport:Boolean(window.visualViewport)};
        }""")
        assert before_chrome["captured"] and before_chrome["scroll"]>200,before_chrome
        # Le moteur doit conserver le caractère lu même si window.resize
        # ne se produit pas. L'événement visualViewport est émis explicitement.
        page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          v.style.height=Math.max(180,v.clientHeight-65)+'px';
          window.visualViewport?.dispatchEvent(new Event('resize'));
        }""")
        page.wait_for_function("""()=>{
          const a=window.__v90ChromeAnchor;
          if(!a?.node?.isConnected)return false;
          const v=document.querySelector('#reader-viewer');
          const r=document.createRange();r.setStart(a.node,a.offset);
          r.setEnd(a.node,a.offset+1);
          const rect=Array.from(r.getClientRects()).find(x=>x.height>0);
          return Boolean(rect)&&Math.abs(
            rect.top-v.getBoundingClientRect().top-a.relativeY)<35;
        }""",timeout=7000)
        page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          v.style.height='';
          window.visualViewport?.dispatchEvent(new Event('resize'));
        }""")

        # V60: le vrai moteur JS chargé sur cette page ne doit pas demander
        # un balayage pour seulement 10 px supplémentaires à la fin.
        tail=page.evaluate("""async ()=>{
          const m=await import('/assets/js/sinjira-liseuse-reflow-v53.mjs?v=53.11.16.146');
          const p={scrollHeight:850,clientHeight:350,lineHeight:35,
            paddingTop:22,paddingBottom:22};
          return {
            screens:m.readerScreenState({...p,scrollTop:0}).screens,
            forward:m.planReaderScreenTurn({...p,scrollTop:245,direction:'next'}),
            backward:m.planReaderScreenTurn({...p,scrollTop:500,direction:'previous'}),
            end:m.planReaderScreenTurn({...p,scrollTop:500,direction:'next'})
          };
        }""")
        assert tail["screens"]==3,tail
        assert tail["forward"]["top"]==500,tail
        assert tail["backward"]["top"]==245,tail
        assert tail["end"]["type"]=="document",tail

        assert not blocked,blocked
        assert not errors,errors

        # V110 : sur grand écran, après un chargement natif, les deux
        # panneaux retrouvent l'ouverture historique. Le raccourci mobile
        # est caché, sans que l'utilisateur perde le contenu du livre.
        page.set_viewport_size({"width":1280,"height":900})
        page.reload(wait_until="load")
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-viewer').dataset.readerLayout==='scroll'""")
        assert page.locator(".reader-settings").evaluate("(el)=>el.open")
        assert page.locator(".reader-audio-settings").evaluate("(el)=>el.open")
        assert not page.locator(".reader-mobile-read-link").is_visible()
        assert not errors,errors
        context.close()
        print(f"PASS {engine}: 320px, 390px, paysage, tablettes, police 34px, "
              "interligne 2.1, contrôles 44px, focus lecteur")
    finally:
        browser.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--browser",choices=("chromium","webkit"),required=True)
    args=parser.parse_args()
    with serve_fixture() as fixture:
        local=fixture.split("/tests/e2e/fixtures/")[0]
        with sync_playwright() as p:
            run(p,args.browser,local+"/compte/liseuse.html?edition=demo")


if __name__=="__main__":
    main()
