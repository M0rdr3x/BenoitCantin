// Contrôle de production éditoriale SINJIRA : ne confond jamais manuscrit déclaré
// terminé, démo publique, disponibilité privée et édition prête pour publication.
const isObject=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const isString=x=>typeof x==="string"&&x.trim().length>0;
const assertFields=(obj,fields)=>fields.every(k=>Object.hasOwn(obj,k));
const pct=(n,d)=>Math.round(n/d*1000)/10;
export const NOVEL_IDS=Object.freeze([
 "sinjira-livre-01-la-cendre-du-jugement",
 "sinjira-livre-02-le-sang-du-sauveur"
]);
export function inspectSinjiraNovelEditorialReadiness(report,manifest,contract){
 const errors=[],fail=x=>errors.push(x);
 if(!isObject(report)||!isObject(manifest)||!isObject(contract)||
    !Array.isArray(report.books)||report.books.length!==2||
    !isObject(report.percent_policy)||!isObject(report.privacy_and_commerce))
   return {ok:false,errors:["SCHEMA"],books:[],readiness_confirmed:false};
 if(report.schema!=="sinjira-roman-editorial-readiness/v1"||
    report.updated_on!=="2026-11-08"||
    report.scope!=="SINJIRA_ROMANS_EDITORIAL_AND_RELEASE_ONLY"||
    !isString(report.origin))
   fail("REPORT_PROVENANCE");
 if(!NOVEL_IDS.every((id,i)=>report.books[i]?.id===id)||
    new Set(report.books.map(b=>b?.id)).size!==2)
   fail("BOOK_IDENTITIES");
 if(!Object.values(report.privacy_and_commerce).every(x=>x===true)||
    !Object.values(report.percent_policy).every(x=>x===true||isString(x)))
   fail("PRIVACY_OR_PERCENT_POLICY");

 const one=report.books[0],two=report.books[1];
 if(!isObject(one)||!isObject(two)||!isObject(one.declared_structure)||
    !isObject(one.public_excerpt)||!isObject(one.completion)||
    !isObject(one.release)||!isObject(one.sources)||
    !isObject(two.declared_structure)||!isObject(two.completion)||
    !isObject(two.release)||!isObject(two.sources)||
    !Array.isArray(one.next_gates)||!Array.isArray(two.next_gates))
   return {ok:false,errors:[...new Set([...errors,"SCHEMA"])],books:[],
    readiness_confirmed:false};
 if(manifest.schema!=="sinjira-book-release-manifest-v1"||
    contract.schema!=="sinjira.livre-i.delivery.v1"||
    !isObject(manifest.book)||!isObject(manifest.demo)||
    !isObject(contract.full_edition)||!isObject(contract.demo))
   fail("SOURCE_CONTRACT_INVALID");
 if(one.title!=="La Cendre du Jugement"||one.volume!=="I"||
    one.edition!=="2026"||
    one.id!==contract.full_edition.product_slug||
    one.publicly_confirmed_status!=="EDITION_INTEGRALE_DECLARÉE_MANUSCRIT_CORRIGÉ"||
    one.official_page!=="/projets/sinjira/romans/"||
    one.sources.public_manifest!=="/projets/sinjira/romans/livre-1-release.json"||
    one.sources.private_delivery_contract!=="/projets/sinjira/codex/livre-i-delivery-contract.json"||
    one.sources.public_demo!=="/projets/sinjira/romans/lire-demo.html")
   fail("BOOK1_IDENTITY_OR_SOURCE");
 if(manifest.book?.title!==one.title||manifest.book?.volume!=="Livre I"||
    manifest.book?.pages!==520||manifest.book?.chapters!==30||
    manifest.book?.epilogue!==true||manifest.book?.publication!=="private-authenticated"||
    manifest.book?.public_repository!==false||
    one.declared_structure.full_pages!==manifest.book?.pages||
    one.declared_structure.chapters!==manifest.book?.chapters||
    one.declared_structure.epilogue!==manifest.book?.epilogue||
    one.declared_structure.full_manuscript_declared!==true||
    contract.full_edition?.pages!==520||
    contract.full_edition?.public_repository_allowed!==false||
    contract.full_edition?.public_static_url_allowed!==false||
    contract.full_edition?.activation_requires_explicit_human_decision!==true)
   fail("BOOK1_MANUSCRIPT_DECLARATION");
 if(manifest.demo?.pages!==82||contract.demo?.pages!==82||
    manifest.demo?.sha256!==contract.demo?.sha256||
    manifest.demo?.free!==true||
    one.public_excerpt.pages!==82||one.public_excerpt.free!==true||
    one.public_excerpt.prologue_and_chapters!=="Prologue et chapitres 1 à 3")
   fail("BOOK1_DEMO_SCOPE");
 if(one.completion.declared_chapter_count_coverage_percent!==100||
    one.completion.manuscript_editorial_completion_percent!==null||
    one.completion.all_release_steps_completion_percent!==null||
    one.completion.full_text_independently_read_and_verified!==false)
   fail("BOOK1_FALSE_COMPLETION");
 if(one.release.manuscript_private!==true||
    one.release.public_full_manuscript_allowed!==false||
    one.release.private_delivery_activated!==false||
    one.release.entitlement_server_validation_required!==true||
    one.release.human_publication_approval_documented!==false||
    ["editorial_final_signoff_documented","proof_reading_final_documented",
      "layout_and_print_proof_approved","commercial_release_date_confirmed"]
      .some(k=>one.release[k]!==null)||
    one.release.paid_sales_activated!==false||
    one.release.reservation_is_purchase!==false||
    one.date_of_completion!==null||
    contract.publication_state!=="not_activated"||
    contract.human_gate_required!==true||
    contract.full_edition?.delivery!=="authenticated_private_storage_only"||
    contract.full_edition?.entitlement_table!=="user_entitlements"||
    contract.full_edition?.entitlement_client_mutation_allowed!==false||
    contract.full_edition?.entitlement_anonymous_read_allowed!==false)
   fail("BOOK1_RELEASE_NOT_APPROVED");
 if(two.id!=="sinjira-livre-02-le-sang-du-sauveur"||
    two.title!=="Le Sang du Sauveur"||two.volume!=="II"||
    two.official_page!=="/projets/sinjira/romans/le-sang-du-sauveur/"||
    two.sources.public_page!==two.official_page||
    two.publicly_confirmed_status!=="EN_PRODUCTION_EDITORIALE"||
    !Object.values(two.declared_structure).every(v=>v===null)||
    two.completion.declared_chapter_count_coverage_percent!==null||
    two.completion.manuscript_editorial_completion_percent!==null||
    two.completion.all_release_steps_completion_percent!==null||
    two.completion.chapter_target_verified!==false||
    two.completion.chapters_approved_verified!==false||
    two.date_of_completion!==null)
   fail("BOOK2_UNPROVEN_PROGRESS");
 if(two.release.manuscript_private!==true||
    two.release.no_manuscript_download_on_public_page!==true||
    two.release.final_edition_confirmed!==false||
    ["editorial_final_signoff_documented","proof_reading_final_documented",
      "publication_date_confirmed"].some(k=>two.release[k]!==null)||
    two.release.paid_sales_activated!==false||
    two.release.human_publication_approval_documented!==false)
   fail("BOOK2_FALSE_RELEASE");
 if(one.next_gates.length!==4||two.next_gates.length!==4||
    ![...one.next_gates,...two.next_gates].every(s=>isString(s)&&s.length>=45))
   fail("EDITORIAL_WORKPLAN_MISSING");
 // La copie publique ne doit jamais embarquer un manuscrit ou un jeton signé.
 const json=JSON.stringify(report);
 if(json.includes(contract.full_edition?.sha256||"___absent___")||
    /%PDF-|\b(?:eyJ[A-Za-z0-9_-]{20,})\b|\/storage\/v1\/object\/sign\//.test(json))
   fail("PRIVATE_CONTENT_EXPOSED");
 const ok=errors.length===0;
 return {ok,errors:[...new Set(errors)],
   book1:{
    declared_manuscript_pages:520,declared_chapters:30,declared_epilogue:true,
    declared_chapter_coverage_percent:100,
    demo_pages:82,public_excerpt_page_share_percent:pct(82,520),
    verified_editorial_completion_percent:null,
    verified_release_completion_percent:null,full_edition_publicly_released:false
   },
   book2:{
    status:"EN_PRODUCTION_EDITORIALE",
    verified_chapter_target:null,verified_chapters_completed:null,
    verified_editorial_completion_percent:null,verified_release_completion_percent:null,
    release_date:null
   },
   readiness_confirmed:false,
   human_approval_required:true};
}
