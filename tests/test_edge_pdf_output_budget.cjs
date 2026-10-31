'use strict';
// Teste directement les fonctions TS livrées, sans authentification ni accès réseau.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'../supabase/functions');
const src=name=>fs.readFileSync(path.join(root,name,'index.ts'),'utf8');
const CAP=20*1024*1024;

function reportHandler(body){
  const source=src('send-game-report');
  const start=source.indexOf('Deno.serve(async (req) => {');
  assert.ok(start>=0);
  let handler;
  const calls={user:0,pdf:0};
  const deno={serve(fn){handler=fn;},env:{get(){throw Error('MUST_NOT_LOOKUP_EMAIL_SECRET');}}};
  new Function('Deno','corsHeaders','privateJson','readLimitedJson',
    'optionalUser','sanitizeSheet','buildPdf','recordDelivery',
    'toBase64','PAID_EXTERNAL_SERVICES_ENABLED','FUNCTION_VERSION',
    source.slice(start))(
      deno,{},(payload,status=200)=>({status,payload}),
      async()=>({body}),async()=>{calls.user++;return null;},
      fields=>fields,async()=>{calls.pdf++;return Uint8Array.of(37,80,68,70,45);},
      async()=>{throw Error('MUST_NOT_RECORD');},
      ()=>'JVBERi0=',false,'test');
  return {handler,calls};
}
test('la demande courriel publique désactivée ne charge aucun PDF ni identité',async()=>{
  const {handler,calls}=reportHandler({mode:'email'});
  const response=await handler({method:'POST'});
  assert.equal(response.status,503);
  assert.equal(response.payload.code,'PAID_EXTERNAL_SERVICE_DISABLED');
  assert.equal(calls.pdf,0,'Aucune opération PDF lorsque le courriel est fermé');
  assert.equal(calls.user,0,'Aucune consultation d’identité inutile');
});
test('le mode téléchargement gratuit continue de fonctionner',async()=>{
  const {handler,calls}=reportHandler({mode:'download',sheet_data:{}});
  const response=await handler({method:'POST'});
  assert.equal(response.status,200);
  assert.equal(response.payload.pdf_base64,'JVBERi0=');
  assert.equal(calls.pdf,1);
});
function builder(name,returnedLength){
  const code=src(name);
  const start=name==='send-game-report'
    ? code.indexOf('async function buildPdf(')
    : code.indexOf('async function buildPlayerSheet(');
  const end=name==='send-game-report'
    ? code.indexOf('\nasync function recordDelivery',start)
    : code.indexOf('\nDeno.serve(',start);
  assert.ok(start>=0&&end>start,'Fonction PDF attendue : '+name);
  const fn=code.slice(start,end).replace(
    /async function buildPdf\(sheet: Record<string, string \| boolean>\)/,
    'async function buildPdf(sheet)').replace(
    /async function buildPlayerSheet\(mode:'solo'\|'standard',fields:Record<string,unknown>\)/,
    'async function buildPlayerSheet(mode,fields)');
  const pdf={
    getForm:()=>({
      updateFieldAppearances(){},
      getTextField(){throw Error('MUST_NOT_ACCESS_FIELDS');}
    }),
    async embedFont(){return {};},
    async save(){return new Uint8Array(returnedLength);}
  };
  const PDFDocument={async load(){return pdf;}};
  const mk=new Function('PDFDocument','fetchTemplateBytes','StandardFonts',
    'CHECKBOXES','MAX_GENERATED_PDF_BYTES','MAX_TEXT',fn+
    '\nreturn '+(name==='send-game-report'?'buildPdf':'buildPlayerSheet')+';');
  return mk(PDFDocument,async()=>Uint8Array.of(37,80,68,70,45),
    {Helvetica:'Helvetica'},new Set(),CAP,6000);
}
for(const [name,args] of [
  ['send-game-report',[{}]],
  ['send-player-sheet',['standard',{}]]
]){
  test(name+' refuse le PDF sérialisé de 20 Mio + 1 octet',async()=>{
    await assert.rejects(builder(name,CAP+1)(...args),/OUTPUT_TOO_LARGE/);
  });
  test(name+' accepte la limite de 20 Mio',async()=>{
    const result=await builder(name,CAP)(...args);
    assert.equal(result.byteLength,CAP);
  });
  test(name+' refuse un PDF sérialisé vide',async()=>{
    await assert.rejects(builder(name,0)(...args),/OUTPUT_TOO_LARGE/);
  });
}
