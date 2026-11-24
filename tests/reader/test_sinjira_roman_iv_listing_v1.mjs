import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const root=new URL("../../",import.meta.url);
const read=path=>readFile(new URL(path,root),"utf8");
test("Roman IV : métadonnées des trois versions et diffusion contrôlée",async()=>{
  const m=JSON.parse(await read("projets/sinjira/romans/roman-4-release.json"));
  assert.equal(m.book.volume,4);
  assert.equal(m.book.title,"Les Cicatrices du Salut");
  assert.equal(m.submitted_versions.demo.pages,55);
  assert.equal(m.submitted_versions.full_pdf.pages,494);
  assert.equal(m.submitted_versions.full_epub.container_validation,"zip_integrity_ok");
  assert.equal(m.editorial_gates.demo_certification,"A1_en_attente");
  assert.equal(m.editorial_gates.public_release_authorized,false);
  assert.equal(m.editorial_gates.private_delivery_authorized,false);
  assert.equal(m.policy.full_text_in_public_git,false);
  for(const x of Object.values(m.submitted_versions))assert.ok(!("public_url" in x));
});
test("Roman IV : la page publique expose une fiche et non des téléchargements",async()=>{
  const html=await read("projets/sinjira/romans/les-cicatrices-du-salut/index.html");
  assert.match(html,/<meta name="viewport" content="width=device-width,initial-scale=1">/);
  assert.match(html,/Les Cicatrices du Salut/);
  assert.match(html,/Certification A1 en attente/);
  assert.doesNotMatch(html,/<a[^>]+(?:\.pdf|\.epub)(?:[?#"'])/i);
  assert.doesNotMatch(html,/\/storage\/v1\/object\//i);
});
test("Roman IV : index et bibliothèque offrent une navigation non trompeuse",async()=>{
  const [page,library,style]=await Promise.all([
    read("projets/sinjira/romans/index.html"),
    read("compte/bibliotheque-romans.html"),
    read("assets/css/sinjira-roman-iv-v1.css")
  ]);
  assert.match(page,/href="les-cicatrices-du-salut\/"/);
  assert.match(library,/href="\/projets\/sinjira\/romans\/les-cicatrices-du-salut\/"/);
  assert.match(page,/55 pages/);
  assert.match(style,/@media\(max-width:700px\)/);
  assert.match(page,/Publication non activée/);
});
