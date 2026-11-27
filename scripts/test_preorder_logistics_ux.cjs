const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-admin-preorder-workflow-v24-5-36.js'),'utf8').replace(/^import [^\n]+\n/,'').replace(/\ninit\(\);\s*$/,'');
const nodes=new Map(),calls=[];
for(const name of ['list','refresh','export','print','prev','next','page','filter','status','paper','shipping','pickup','undecided'])nodes.set('[data-pa-logistics-'+name+']',{dataset:{},setAttribute(k,v){this[k]=v;}});
const node=name=>nodes.get('[data-pa-logistics-'+name+']');
const api=vm.runInNewContext(source+'\n({loadLogistics,renderLogistics,filteredLogisticsRows,logisticsPageSlice,exportLogisticsCsv,printLogisticsSheet,setPage(v){logisticsPage=v}})',{
 document:{querySelector:k=>nodes.get(k)||null},getSupabase:()=>({rpc(name,args){assert.equal(name,'admin_preorder_logistics_queue');assert.equal(args.p_limit,500);return new Promise(resolve=>calls.push(resolve));}}),escapeHtml:String,friendlyBackendMessage:(e,f)=>f,Intl,Date
});
const rows=Array.from({length:51},(_,i)=>({reservation_reference:'Fixture-'+i,preferred_format:'paper',quantity:1,preorder_status:'reserved'}));
(async()=>{
 const first=api.loadLogistics();assert.equal(node('export').disabled,true);assert.equal(node('print').disabled,true);
 api.exportLogisticsCsv();api.printLogisticsSheet();
 const second=api.loadLogistics();calls[1]({data:rows});await second;
 calls[0]({data:[]});await first;
 assert.equal(api.filteredLogisticsRows().length,51);assert.equal(node('paper').textContent,'51');
 assert.match(node('page').textContent,/1–25 sur 51/);assert.equal(node('prev').disabled,true);
 api.setPage(2);api.renderLogistics();assert.match(node('page').textContent,/51–51 sur 51/);
 assert.equal(node('next').disabled,true);assert.equal(node('export').disabled,false);
 assert.equal(api.filteredLogisticsRows().length,51);
 const failed=api.loadLogistics();calls[2]({error:new Error('fixture')});await failed;
 assert.equal(node('export').disabled,true);assert.equal(node('print').disabled,true);assert.equal(node('paper').textContent,'—');
 assert.equal(node('list')['aria-busy'],'false');
 console.log('OK logistique : pagination, compteurs complets, réponses obsolètes et verrou export.');
})().catch(error=>{console.error(error);process.exitCode=1;});
