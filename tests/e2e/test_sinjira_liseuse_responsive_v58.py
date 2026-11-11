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
        page.wait_for_timeout(100)
        large=geometry(page)
        assert large["textFont"]==34,large
        assert large["documentWidth"]<=323,large
        assert large["articleWidth"]<=large["viewerWidth"]+3,large
        assert snapshot(page)["page"]==3,snapshot(page)
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
