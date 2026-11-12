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
        errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        blocked=install_isolation(page)
        page.goto(origin,wait_until="load")
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-viewer').dataset.readerLayout==='screens'&&
          document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST')""")
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
            assert info["navDisplay"]=="flex",(label,info)
            assert min(info["nextHeight"],info["prevHeight"])>=44,(label,info)
            assert info["viewerWidth"]>=280,(label,info)
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
          const m=await import('/assets/js/sinjira-liseuse-reflow-v53.mjs?v=53.11.10.1');
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
          const m=await import('/assets/js/sinjira-liseuse-reflow-v53.mjs?v=53.11.10.1');
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

        # Focus lecture : même avec les panneaux secondaires cachés, il doit
        # être possible de sortir via le bouton et d'utiliser la navigation.
        page.locator("#reader-focus").click()
        assert page.locator("body").evaluate(
            "(node)=>node.classList.contains('reader-focus-mode')"
        ),"Mode lecture plein écran inaccessible"
        focused=geometry(page)
        assert focused["viewerHeight"]>=280,focused
        page.locator("#reader-focus").click()
        assert not page.locator("body").evaluate(
            "(node)=>node.classList.contains('reader-focus-mode')"
        ),"Impossible de quitter le plein écran"

        # V61 : les libellés d'aide changent quand on quitte le mode paginé.
        page.locator("#reader-screens-enabled").uncheck()
        assert page.locator("#reader-touch-next").get_attribute("aria-label")=="Page du livre suivante"
        assert page.locator("#reader-touch-prev").get_attribute("aria-label")=="Page du livre précédente"
        page.locator("#reader-screens-enabled").check()
        assert "Écran suivant" in page.locator("#reader-touch-next").get_attribute("aria-label")

        # V60: le vrai moteur JS chargé sur cette page ne doit pas demander
        # un balayage pour seulement 10 px supplémentaires à la fin.
        tail=page.evaluate("""async ()=>{
          const m=await import('/assets/js/sinjira-liseuse-reflow-v53.mjs?v=53.11.10.1');
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
