#!/usr/bin/env python3
"""V66 : détecter un faux glissement après déplacement vertical du doigt.

Vraie page `compte/liseuse.html`, faux PDF; aucun compte privé.
Les TouchEvents de ces scénarios sont volontairement synthétiques :
les gestes émis par le moteur Chromium sont testés séparément en V65.
"""
import argparse

from playwright.sync_api import sync_playwright

from test_sinjira_liseuse_mobile_v54 import serve_fixture
from test_sinjira_liseuse_real_page_v57 import install_isolation, snapshot


TRAJECTORY = """
({dx,dy=3,moves=[],scrollDuring=0,startX=248})=>{
  const viewer=document.querySelector('#reader-viewer');
  const base={identifier:42,target:viewer,clientX:startX,clientY:242};
  const fake=(name,touches,changed)=>{
    const ev=new Event(name,{bubbles:true,cancelable:true});
    Object.defineProperties(ev,{
      touches:{value:touches},
      changedTouches:{value:changed}
    });
    viewer.dispatchEvent(ev);
    return ev;
  };
  const initialScroll=viewer.scrollTop;
  fake('touchstart',[base],[base]);
  for(const [mx,my] of moves){
    const pt={...base,clientX:base.clientX+mx,clientY:base.clientY+my};
    fake('touchmove',[pt],[pt]);
  }
  if(scrollDuring){
    viewer.scrollTop=initialScroll+scrollDuring;
    fake('touchmove',[base],[base]);
    viewer.scrollTop=initialScroll;
  }
  const finish={...base,clientX:base.clientX+dx,clientY:base.clientY+dy};
  const done=fake('touchend',[],[finish]);
  return {prevented:done.defaultPrevented,scroll:viewer.scrollTop,
    page:Number(document.querySelector('#reader-page').value),
    layout:viewer.dataset.readerLayout};
}
"""


def run(playwright, engine, url):
    browser=getattr(playwright,engine).launch()
    try:
        context=browser.new_context(
            viewport={"width":390,"height":844},is_mobile=True,has_touch=True,
            locale="fr-CA",device_scale_factor=2,service_workers="block",
            reduced_motion="reduce"
        )
        page=context.new_page()
        errors=[]
        page.on("pageerror",lambda error:errors.append(str(error)))
        blocked=install_isolation(page)
        page.goto(url,wait_until="load")
        page.wait_for_function("""()=>{
          const v=document.querySelector('#reader-viewer');
          return !document.querySelector('#reader-content').hidden &&
            v.dataset.readerLayout==='screens' &&
            document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST');
        }""")
        assert snapshot(page)["page"]==3
        for width,height in [(390,844),(320,568)]:
            page.set_viewport_size({"width":width,"height":height})
            page.wait_for_timeout(100)
            page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")
            start=snapshot(page)
            assert start["page"]==3 and start["scroll"]==0,start

            # Le trajet traverse une grande distance verticale, même si
            # l'arrivée semble strictement horizontale.
            mixed=page.evaluate(TRAJECTORY,{
                "dx":-135,"dy":2,"moves":[[-8,120],[-70,8]]
            })
            assert not mixed["prevented"] and mixed["page"]==3 and mixed["scroll"]==0,(
                "V66: trajet vertical puis gauche interprété comme une page",
                width,mixed
            )
            reverse=page.evaluate(TRAJECTORY,{
                "dx":135,"dy":2,"moves":[[7,-125],[65,-10]]
            })
            assert not reverse["prevented"] and reverse["page"]==3,(
                "V66: trajet vertical puis droite interprété comme une page",
                width,reverse
            )
            native_scroll=page.evaluate(TRAJECTORY,{
                "dx":-135,"dy":2,"scrollDuring":48
            })
            assert not native_scroll["prevented"] and native_scroll["page"]==3,(
                "V66: scroll transitoire interprété comme balayage horizontal",
                width,native_scroll
            )
            # V67 : les 24 px des bords appartiennent aux gestes du
            # navigateur / du système. Aucune page ne doit tourner.
            edge_left=page.evaluate(TRAJECTORY,{
                "dx":135,"dy":2,"startX":8
            })
            edge_right=page.evaluate(TRAJECTORY,{
                "dx":-135,"dy":2,"startX":width-8
            })
            for edge in (edge_left,edge_right):
                assert edge["page"]==3 and edge["scroll"]==0 and not edge["prevented"],(
                    "V67: le lecteur a capté un geste système",width,edge
                )
            # Le vrai geste horizontal reste utilisable après les rejets.
            clean=page.evaluate(TRAJECTORY,{
                "dx":-135,"dy":2,"moves":[[-70,7]]
            })
            assert clean["prevented"] and clean["page"]==3 and clean["scroll"]>0,(
                "V66: geste horizontal légitime bloqué",width,clean
            )
            page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")

        # Le mode texte libre est géré par V52; cette logique doit bénéficier
        # de la même protection contre les fausses commandes PDF.
        page.locator("#reader-screens-enabled").uncheck()
        page.wait_for_function("""()=>document.querySelector('#reader-viewer')
          .dataset.readerLayout==='scroll'""")
        reject=page.evaluate(TRAJECTORY,{
            "dx":-135,"dy":2,"moves":[[-8,135],[-75,10]]
        })
        assert reject["page"]==3 and not reject["prevented"],reject
        scroll_reject=page.evaluate(TRAJECTORY,{
            "dx":-135,"dy":2,"scrollDuring":42
        })
        assert scroll_reject["page"]==3,scroll_reject
        edge_pdf_left=page.evaluate(TRAJECTORY,{
            "dx":135,"dy":2,"startX":8
        })
        edge_pdf_right=page.evaluate(TRAJECTORY,{
            "dx":-135,"dy":2,"startX":page.viewport_size["width"]-8
        })
        assert edge_pdf_left["page"]==3 and edge_pdf_right["page"]==3,(
            "V67: mode PDF a capté le geste système",
            edge_pdf_left,edge_pdf_right
        )
        allowed=page.evaluate(TRAJECTORY,{
            "dx":-135,"dy":2,"moves":[[-75,7]]
        })
        page.wait_for_function("""()=>Number(document.querySelector('#reader-page').value)===4""")
        assert allowed["page"]==4 and snapshot(page)["page"]==4,(
            "V66: changement PDF simple perdu après les faux gestes",allowed
        )
        assert not errors,errors
        assert not blocked,blocked
        print(f"PASS {engine}: V66/V67 trajectoire verticale et bord du viewport "
              "ignorés, gestes horizontaux conservés en écrans et PDF")
        context.close()
    finally:
        browser.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--browser",choices=("chromium","webkit"),required=True)
    args=parser.parse_args()
    with serve_fixture() as fixture:
        root=fixture.split("/tests/e2e/fixtures/")[0]
        with sync_playwright() as playwright:
            run(playwright,args.browser,root+"/compte/liseuse.html?edition=demo")


if __name__=="__main__":
    main()
