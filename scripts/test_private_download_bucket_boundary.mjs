import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {isVerifiedPrivateDocumentBucket} from '../supabase/functions/_shared/private-document-storage.mjs';

for(const [endpoint,location] of [['get-document-url','doc.storage_bucket'],['get-novel-file-url','novel.private_storage_bucket'],['get-private-book-url','storage.bucket']]){
  test(endpoint+' refuses public, mismatched or unverifiable buckets',async()=>{
    const source=readFileSync(new URL('../supabase/functions/'+endpoint+'/index.ts',import.meta.url),'utf8');
    const guard=endpoint==='get-document-url'
      ? '    const {data:bucketMetadata,error:bucketMetadataError}=await service.storage.getBucket('+location+');'
      : '    const {data:bucket,error:bucketError}=await service.storage.getBucket('+location+');';
    const start=source.indexOf(guard);
    const end=source.indexOf('    const {data:signed,error:signedError}',start);
    assert.ok(start>=0&&end>start,'private bucket guard before signing');
    const code='(async()=>{'+source.slice(start,end)+'\nreturn {status:200};})()';
    for(const [data,error,expected] of [
      [{id:'private-test',public:false},null,200],
      [{id:'private-test',public:true},null,503],
      [{id:'private-test',public:'false'},null,503],
      [{id:'private-test'},null,503],
      [{id:'other',public:false},null,503],
      [null,null,503],
      [{id:'private-test',public:false},{code:'FAILED'},503],
    ]){
      const context={doc:{storage_bucket:'private-test'},novel:{private_storage_bucket:'private-test'},storage:{bucket:'private-test'},
        service:{storage:{async getBucket(id){assert.equal(id,'private-test');return {data,error};}}},
        isVerifiedPrivateDocumentBucket, console:{error(){}},
        json:(payload,status)=>({payload,status}),privateJson:(payload,status)=>({payload,status})};
      const result=await vm.runInNewContext(code,context,{timeout:1000});
      assert.equal(result.status,expected);
      if(expected!==200){assert.equal(result.payload.ok,false);assert.equal('url' in result.payload,false);}
    }
  });
}
