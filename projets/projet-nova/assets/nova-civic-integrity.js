/* Projet Nova — validation partagée des corpus électoraux.
   Fonction pure, aucune requête réseau, aucune collecte de réponses. */
(function(root){
 "use strict";
 const isObj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
 const text=x=>typeof x==="string"&&x.trim().length>0;
 const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 const POLL_IDS=Object.freeze(["q02","q09","q17","q22","q29","q33","q47","q61"]);
 const POLL_VALUES=Object.freeze([-2,-1,0,1,2,9]);
 const POLL_LABELS=Object.freeze(["Tout à fait en désaccord","Plutôt en désaccord",
   "Ni d’accord ni en désaccord","Plutôt d’accord","Tout à fait d’accord","Sans opinion / passer"]);
 const POLL_CANONICAL=Object.freeze([{"id":"q02","text":"Le gouvernement du Québec devrait réduire les restrictions à l’entrée de nouvelles entreprises dans les secteurs actuellement réglementés.","axis":"economy"},{"id":"q09","text":"La majorité des soins de première ligne financés par l’État devrait être fournie par des établissements publics.","axis":"health"},{"id":"q17","text":"Le gouvernement du Québec devrait augmenter le financement consacré aux logements sociaux, coopératifs et sans but lucratif.","axis":"housing"},{"id":"q22","text":"Le gouvernement du Québec devrait renoncer à une nouvelle norme environnementale si son analyse d’impact prévoit une hausse du coût de biens essentiels.","axis":"environment"},{"id":"q29","text":"Les organismes publics ne devraient pas pouvoir élargir la surveillance numérique sans autorisation judiciaire préalable, sauf dans une urgence prévue par la loi.","axis":"liberties"},{"id":"q33","text":"Une pétition atteignant un seuil prévu par la loi devrait pouvoir déclencher un référendum provincial obligatoire.","axis":"democracy"},{"id":"q47","text":"Le gouvernement du Québec devrait préparer les conditions permettant la tenue d’un référendum sur la souveraineté.","axis":"quebec"},{"id":"q61","text":"Toute décision administrative importante prise à l’aide d’un système d’IA devrait pouvoir être expliquée à la personne concernée.","axis":"digital"}]);
 const QUALITY=Object.freeze(["singlePolicyDecision","explicitActor","neutralTone",
   "noPartyReference","noIdeologicalLabel","noPresumedMotive",
   "reviewedForDoubleBarrel","reviewedForUndefinedQualifier"]);
 const response=(issues)=>Object.freeze({ok:issues.length===0,issues});
 function inspectCompass(c){
   const issues=[];
   if(!isObj(c)||c.version!=="2.2.0"||c.locale!=="fr-CA"||
     !Array.isArray(c.axes)||c.axes.length!==16||
     !Array.isArray(c.questions)||c.questions.length!==64||
     !isObj(c.methodology)||!isObj(c.partyComparison))return response(["SCHEMA"]);
   const axes=new Set();
   for(const a of c.axes){
     if(!isObj(a)||!text(a.id)||!/^[a-z][a-z-]*$/.test(a.id)||axes.has(a.id)||
       !text(a.title)||!text(a.negative)||!text(a.positive))
       issues.push("AXES");
     else axes.add(a.id);
   }
   if(axes.size!==16)issues.push("AXIS_COUNT");
   const m=c.methodology;
   if(m.profile!=="multidimensional"||m.responseScale?.min!==-3||m.responseScale?.max!==3||
      !equal(m.importanceWeights,{faible:0.5,normal:1,forte:1.5})||
      m.axisMinimumAnswered!==2||m.minimumAnsweredRatio!==0.5||c.partyComparison.enabled!==false||
      c.partyComparison.unknownPolicy!=="Unknown party positions are excluded from distance and always disclosed.")
     issues.push("CALCULATION_OR_NEUTRALITY_RULE");
   const byAxis=new Map([...axes].map(id=>[id,{negative:0,positive:0}]));
   const ids=new Set();
   c.questions.forEach((q,i)=>{
     const id="q"+String(i+1).padStart(2,"0");
     if(!isObj(q)||q.id!==id||ids.has(q.id)||!axes.has(q.axis)||
       !text(q.text)||![-1,1].includes(q.direction)||
       !isObj(q.quality)||QUALITY.some(k=>q.quality[k]!==true)){
       issues.push("QUESTION_"+id);return;
     }
     ids.add(q.id);
     const bucket=byAxis.get(q.axis);
     bucket[q.direction===1?"positive":"negative"]++;
     if(!Array.isArray(q.loadings)||q.loadings.length<1||q.loadings.length>2||
       !isObj(q.loadings[0])||q.loadings[0].axis!==q.axis||
       q.loadings[0].weight!==1||q.loadings[0].direction!==q.direction)
       issues.push("PRIMARY_LOADING_"+id);
     if(q.loadings.length===2){
       const sec=q.loadings[1];
       if(!isObj(sec)||!axes.has(sec.axis)||sec.axis===q.axis||
         !Number.isFinite(sec.weight)||sec.weight<=0||sec.weight>0.4||
         ![-1,1].includes(sec.direction))issues.push("SECONDARY_LOADING_"+id);
     }
   });
   for(const [id,v] of byAxis){
     if(v.negative!==2||v.positive!==2)issues.push("UNBALANCED_AXIS_"+id);
   }
   return response([...new Set(issues)]);
 }
 function inspectPoll(c){
   const issues=[];
   if(!isObj(c)||c.version!=="nova-consultation-v1"||
     typeof c.published!=="boolean"||
     c.format!=="consultation_ouverte_non_probabiliste"||
     c.eligibility!=="18+"||!Array.isArray(c.questions)||c.questions.length!==8||
     !Array.isArray(c.options)||c.options.length!==6)return response(["SCHEMA"]);
   c.questions.forEach((q,i)=>{
     if(!isObj(q)||q.id!==POLL_IDS[i]||q.ordinal!==i+1||
       q.text!==POLL_CANONICAL[i].text||q.axis!==POLL_CANONICAL[i].axis||
       !text(q.text)||!text(q.axis)||!/^[a-z][a-z-]*$/.test(q.axis))
       issues.push("QUESTION_"+String(i+1));
   });
   if(!c.options.every((o,i)=>isObj(o)&&
     o.value===POLL_VALUES[i]&&o.label===POLL_LABELS[i]))
     issues.push("OPTIONS");
   return response(issues);
 }
 function inspectPollCompassBinding(poll,compass){
   const errors=[...inspectPoll(poll).issues,...inspectCompass(compass).issues];
   if(!isObj(poll)||!Array.isArray(poll.questions)||
      !isObj(compass)||!Array.isArray(compass.questions))return response([...new Set(errors)]);
   const questions=new Map(compass.questions.map(q=>[q.id,q]));
   for(const q of poll.questions){
     const master=questions.get(q.id);
     if(!master||q.text!==master.text||q.axis!==master.axis)
       errors.push("SOURCE_MISMATCH_"+q.id);
   }
   return response(errors);
 }

 // Le calcul officiel de la boussole est pur et reproductible :
 // aucune écriture réseau, aucun profil utilisateur partagé.
 function scoreCompass(c,answers){
   if(!inspectCompass(c).ok) throw new Error("QUESTIONNAIRE_INVALID");
   if(!answers||typeof answers.get!=="function"||typeof answers.entries!=="function")
     throw new TypeError("ANSWERS_MAP_REQUIRED");
   const questionIds=new Set(c.questions.map(q=>q.id));
   const importanceWeights=c.methodology.importanceWeights;
   for(const [id,answer] of answers.entries()){
     if(!questionIds.has(id)||!isObj(answer)||
        (answer.value!==null&&(!Number.isInteger(answer.value)||answer.value< -3||answer.value>3))||
        !Object.hasOwn(importanceWeights,answer.importance))
       throw new Error("INVALID_ANSWER");
   }
   const axes=new Map(c.axes.map(axis=>[axis.id,{
     axis,sum:0,max:0,primaryAnswered:0,primaryTotal:0,evidenceWeight:0
   }]));
   for(const question of c.questions){
     const primary=axes.get(question.axis);
     primary.primaryTotal++;
     const answer=answers.get(question.id);
     if(!answer||answer.value===null)continue;
     primary.primaryAnswered++;
     const userWeight=importanceWeights[answer.importance];
     for(const loading of question.loadings){
       const bucket=axes.get(loading.axis);
       bucket.sum+=answer.value*loading.direction*userWeight*loading.weight;
       bucket.max+=3*userWeight*loading.weight;
       bucket.evidenceWeight+=loading.weight;
     }
   }
   return [...axes.values()].map(bucket=>({
     ...bucket.axis,
     score:bucket.max>0&&bucket.primaryAnswered>=c.methodology.axisMinimumAnswered
       ?Math.round(bucket.sum/bucket.max*100):null,
     answered:bucket.primaryAnswered,total:bucket.primaryTotal,
     coverage:bucket.primaryTotal?Math.round(bucket.primaryAnswered/bucket.primaryTotal*100):0,
     evidenceWeight:Math.round(bucket.evidenceWeight*100)/100
   }));
 }
 root.__NOVA_CIVIC_INTEGRITY=Object.freeze({
   inspectCompass,inspectPoll,inspectPollCompassBinding,scoreCompass,
   pollIds:POLL_IDS,values:POLL_VALUES
 });
})(typeof window!=="undefined"?window:(typeof globalThis!=="undefined"?globalThis:{}));
