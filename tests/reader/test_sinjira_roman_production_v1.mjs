import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {inspectSinjiraNovelEditorialReadiness}
 from "../../assets/js/sinjira-roman-production-core-v1.mjs";
const load=async path=>JSON.parse(await readFile(new URL("../../"+path,import.meta.url),"utf8"));
const [report,manifest,contract]=await Promise.all([
 load("docs/sinjira/avancement-editorial-2026-11-08.json"),
 load("projets/sinjira/romans/livre-1-release.json"),
 load("projets/sinjira/codex/livre-i-delivery-contract.json")
]);
const check=(a=report,b=manifest,c=contract)=>
 inspectSinjiraNovelEditorialReadiness(a,b,c);
const change=(fn,code)=>{
 const c=structuredClone(report);fn(c);
 const result=check(c);
 assert.equal(result.ok,false);
 assert.ok(result.errors.includes(code),result.errors.join(","));
};
test("les deux romans sont distincts, et le registre reflète les sources",()=>{
 const x=check();
 assert.equal(x.ok,true,x.errors.join(","));
 assert.equal(report.books.length,2);
 assert.equal(x.readiness_confirmed,false);
 assert.equal(x.human_approval_required,true);
});
test("Livre I : 520 pages, 30 chapitres et épilogue déclarés",()=>{
 const x=check();
 assert.equal(x.book1.declared_manuscript_pages,520);
 assert.equal(x.book1.declared_chapters,30);
 assert.equal(x.book1.declared_epilogue,true);
 assert.equal(x.book1.declared_chapter_coverage_percent,100);
});
test("100 % des chapitres déclarés ne veut pas dire 100 % éditorial ou commercial",()=>{
 const x=check();
 assert.equal(x.book1.declared_chapter_coverage_percent,100);
 assert.equal(x.book1.verified_editorial_completion_percent,null);
 assert.equal(x.book1.verified_release_completion_percent,null);
 assert.equal(x.book1.full_edition_publicly_released,false);
});
test("82 pages offertes gratuitement ne sont pas 82 % du manuscrit",()=>{
 const x=check();
 assert.equal(x.book1.demo_pages,82);
 assert.equal(x.book1.public_excerpt_page_share_percent,15.8);
 assert.equal(report.percent_policy.excerpt_share_is_not_completion,true);
});
test("les hashes des démos dans le manifeste et le contrat concordent",()=>{
 assert.equal(manifest.demo.sha256,contract.demo.sha256);
 assert.equal(manifest.demo.pages,contract.demo.pages);
 const forged=structuredClone(manifest);forged.demo.sha256="0".repeat(64);
 assert.ok(check(report,forged).errors.includes("BOOK1_DEMO_SCOPE"));
});
test("le contrat de diffusion intégrale reste privé et non activé",()=>{
 const x=check();
 assert.equal(contract.publication_state,"not_activated");
 assert.equal(contract.full_edition.delivery,"authenticated_private_storage_only");
 assert.equal(report.books[0].release.private_delivery_activated,false);
 assert.equal(report.books[0].release.public_full_manuscript_allowed,false);
 assert.equal(x.human_approval_required,true);
});
test("une livraison publique déclarée active est rejetée",()=>{
 change(x=>x.books[0].release.private_delivery_activated=true,"BOOK1_RELEASE_NOT_APPROVED");
 change(x=>x.books[0].release.public_full_manuscript_allowed=true,"BOOK1_RELEASE_NOT_APPROVED");
});
test("une fausse date ou un faux paiement est rejeté",()=>{
 change(x=>x.books[0].release.commercial_release_date_confirmed="2026-12-01",
  "BOOK1_RELEASE_NOT_APPROVED");
 change(x=>x.books[0].release.paid_sales_activated=true,"BOOK1_RELEASE_NOT_APPROVED");
});
test("une fausse validation de la relecture éditoriale est refusée",()=>{
 change(x=>x.books[0].release.editorial_final_signoff_documented=true,
  "BOOK1_RELEASE_NOT_APPROVED");
 change(x=>x.books[0].completion.manuscript_editorial_completion_percent=100,
  "BOOK1_FALSE_COMPLETION");
});
test("une réservation de précommande n'est pas une vente",()=>{
 assert.equal(report.books[0].release.reservation_is_purchase,false);
 change(x=>x.books[0].release.reservation_is_purchase=true,
  "BOOK1_RELEASE_NOT_APPROVED");
});
test("l'édition intégrale privée ne doit jamais devenir un asset statique",()=>{
 change(x=>x.privacy_and_commerce.private_manuscript_content_not_embedded=false,
  "PRIVACY_OR_PERCENT_POLICY");
 assert.equal(manifest.book.public_repository,false);
 assert.equal(contract.full_edition.public_static_url_allowed,false);
});
test("un hash privé ne doit pas être recopié dans les métadonnées d'avancement",()=>{
 const s=JSON.stringify(report);
 assert.equal(s.includes(contract.full_edition.sha256),false);
 change(x=>x.books[0].source_master_hash=contract.full_edition.sha256,
  "PRIVATE_CONTENT_EXPOSED");
});
test("la cible de chapitres du Livre II reste inconnue",()=>{
 const x=check();
 assert.equal(x.book2.verified_chapter_target,null);
 assert.equal(x.book2.verified_chapters_completed,null);
 assert.equal(x.book2.verified_editorial_completion_percent,null);
});
test("le Livre II ne reçoit pas 50 ou 100 % sans comptage de manuscrit",()=>{
 change(x=>x.books[1].completion.manuscript_editorial_completion_percent=50,
   "BOOK2_UNPROVEN_PROGRESS");
 change(x=>x.books[1].completion.declared_chapter_count_coverage_percent=100,
   "BOOK2_UNPROVEN_PROGRESS");
});
test("une fausse date de lancement du Livre II est refusée",()=>{
 change(x=>x.books[1].release.publication_date_confirmed="2026-12-01",
   "BOOK2_FALSE_RELEASE");
 change(x=>x.books[1].release.paid_sales_activated=true,
   "BOOK2_FALSE_RELEASE");
});
test("un faux objectif de 30 chapitres pour le Livre II est refusé",()=>{
 change(x=>x.books[1].declared_structure.chapters=30,
   "BOOK2_UNPROVEN_PROGRESS");
});
test("un changement de chiffres au Livre I doit être réconcilié au manifeste",()=>{
 change(x=>x.books[0].declared_structure.full_pages=530,
   "BOOK1_MANUSCRIPT_DECLARATION");
 change(x=>x.books[0].public_excerpt.pages=200,"BOOK1_DEMO_SCOPE");
});
test("une ligne manquante, un statut corrompu ou un projet absent échouent",()=>{
 const c=structuredClone(report);c.books.pop();
 assert.ok(check(c).errors.includes("SCHEMA"));
 change(x=>x.books[1].publicly_confirmed_status="EDITION_PUBLIEE",
   "BOOK2_UNPROVEN_PROGRESS");
 assert.ok(check(null).errors.includes("SCHEMA"));
});
test("la suite des étapes éditoriales est documentée sans contenu privé",()=>{
 const x=check();
 assert.equal(x.ok,true);
 assert.equal(report.books[0].next_gates.length,4);
 assert.equal(report.books[1].next_gates.length,4);
 assert.equal(report.privacy_and_commerce.no_unverified_completion_percent,true);
});
test("la bibliothèque montre distinctement les deux livres et les limites des %",async()=>{
 const html=await readFile(new URL("../../projets/sinjira/romans/index.html",import.meta.url),"utf8");
 const start=html.indexOf('id="etat-production-romans"');
 const end=html.indexOf("</section>",start);
 assert.ok(start>0&&end>start);
 const section=html.slice(start,end);
 for(const term of ["520 pages","30 chapitres","82 pages","15,8 %","pourcentage éditorial",
  "Le Sang du Sauveur","non mesurable","non activée"]){
  assert.ok(section.includes(term),term);
 }
 assert.ok(section.includes("avancement-editorial-2026-11-08.json"));
});
test("la fiche du Livre II ne prétend ni manuscrit terminé ni sortie annoncée",async()=>{
 const html=await readFile(new URL("../../projets/sinjira/romans/le-sang-du-sauveur/index.html",import.meta.url),"utf8");
 assert.ok(html.includes('id="production-livre-ii"'));
 assert.match(html,/pourcentage[^<]*non mesurable/);
 assert.ok(!html.includes("100 % du Livre II"));
});

test("la grille éditoriale couvre prologue, 30 chapitres et épilogue sans texte privé",async()=>{
 const track=await load("docs/sinjira/suivi-chapitres-livre-i-2026-11-08.json");
 assert.equal(track.schema,"sinjira-livre-i-chapter-editorial-tracker/v1");
 assert.equal(track.units.length,32);
 assert.equal(track.units.filter(u=>u.kind==="chapter").length,30);
 assert.equal(track.units[0].id,"prologue");
 assert.equal(track.units.at(-1).id,"epilogue");
 assert.equal(new Set(track.units.map(u=>u.id)).size,32);
 assert.equal(track.declared_structure.chapters,manifest.book.chapters);
});
test("aucune des 32 relectures n'est présentée comme acquise sans une preuve",async()=>{
 const track=await load("docs/sinjira/suivi-chapitres-livre-i-2026-11-08.json");
 for(const unit of track.units){
  assert.equal(unit.manuscript_section_verified,false);
  assert.equal(unit.continuity_review,"NON_EVALUEE");
  assert.equal(unit.structural_review,"NON_EVALUEE");
  assert.equal(unit.copy_edit,"NON_EVALUEE");
  assert.equal(unit.proof_read,"NON_EVALUEE");
  assert.equal(unit.author_signoff,"NON_EVALUE");
  assert.equal(unit.reviewed_on,null);
  assert.equal(unit.review_evidence_ref,null);
 }
 assert.equal(track.progress.editorial_units_fully_validated,0);
 assert.equal(track.progress.editorial_completion_percentage,null);
});
test("le sommaire publié de la démo ne certifie que sa portée, pas la relecture",async()=>{
 const track=await load("docs/sinjira/suivi-chapitres-livre-i-2026-11-08.json");
 assert.deepEqual(track.units.filter(u=>u.declared_in_free_demo).map(u=>u.id),
 ["prologue","chapter-01","chapter-02","chapter-03"]);
 assert.equal(track.progress.manuscript_verified_percentage,null);
});
test("le suivi des chapitres ne divulgue ni texte ni hash du livre intégral",async()=>{
 const track=await load("docs/sinjira/suivi-chapitres-livre-i-2026-11-08.json");
 assert.ok(Object.values(track.security).every(v=>v===false));
 assert.equal(JSON.stringify(track).includes(contract.full_edition.sha256),false);
 assert.ok(track.units.every(u=>u.private_master_page_reference===null&&u.chapter_title_verified===null));
});
test("aucun objectif de chapitre ni pourcentage fictif n'est assigné au Livre II",async()=>{
 const track=await load("docs/sinjira/suivi-chapitres-livre-i-2026-11-08.json");
 assert.equal(track.book_two.target_chapters,null);
 assert.equal(track.book_two.chapters_written_confirmed,null);
 assert.equal(track.book_two.validated_percentage,null);
});
test("le suivi éditorial reste exclu du rendu Jekyll d'urgence",async()=>{
 const config=await readFile(new URL("../../_config.yml",import.meta.url),"utf8");
 assert.match(config,/\n  - "docs"\n/);
 const html=await readFile(new URL("../../projets/sinjira/romans/index.html",import.meta.url),"utf8");
 assert.ok(!html.includes('href="avancement-editorial-2026-11-08.json"'));
 assert.ok(html.includes("github.com/M0rdr3x/BenoitCantin/blob/main/docs/sinjira/avancement-editorial-2026-11-08.json"));
});
