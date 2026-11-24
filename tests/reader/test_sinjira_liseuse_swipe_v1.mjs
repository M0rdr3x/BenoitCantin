import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const root=new URL("../../",import.meta.url);
const read=path=>readFile(new URL(path,root),"utf8");
test("balayage mobile : gestes, seuils et annulation multi-touch",async()=>{
  const js=await read("assets/js/sinjira-liseuse-v26.js");
  for(const marker of [
    "addEventListener('touchstart'","addEventListener('touchend'",
    "addEventListener('touchcancel'","event.touches.length!==1",
    "Math.abs(dx)<=Math.abs(dy)*1.5","dx<0?1:-1",
    "swipeViewer.scrollWidth>swipeViewer.clientWidth+8",
    "window.getSelection()?.toString()",
    "if(!start||!state.pdf"
  ])assert.ok(js.includes(marker),marker);
});
test("balayage mobile : consigne et commandes accessibles",async()=>{
  const [html,css]=await Promise.all([read("compte/liseuse.html"),read("assets/css/sinjira-liseuse-v26.css")]);
  assert.match(html,/Sur téléphone, glissez vers la gauche pour avancer/);
  assert.match(html,/vers la droite pour revenir en arrière/);
  assert.match(html,/id="reader-previous"/);
  assert.match(html,/id="reader-next"/);
  assert.match(css,/overscroll-behavior-x:contain/);
  assert.match(css,/#reader-previous.*min-height:48px/);
});
