/* Preview conflicting imports before replacing previously accepted source records. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./local-archive'):root.SlotLocalArchive);if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotImportReview=api;})(typeof globalThis!=='undefined'?globalThis:this,function(archive){
'use strict';
const id=r=>r.original_post_id?r.type+'|'+r.original_post_id:r.source_id+'|'+r.id;
const ctxId=r=>JSON.stringify([r.store_id,r.machine_id,r.as_of]);
const equal=(a,b)=>JSON.stringify(Object.keys(a).sort().map(k=>[k,a[k]]))===JSON.stringify(Object.keys(b).sort().map(k=>[k,b[k]]));
function preview(existing,incoming){
 const a=archive.checked(existing),b=archive.checked(incoming);
 const conflicts=[],added={records:0,contexts:0},unchanged={records:0,contexts:0};
 for(const [kind,prior,next,key] of [['records',a.records,b.records,id],['contexts',a.contexts,b.contexts,ctxId]]){
  const old=new Map(prior.map(x=>[key(x),x]));
  for(const row of next){const k=key(row);if(!old.has(k))added[kind]++;else if(equal(old.get(k),row))unchanged[kind]++;else conflicts.push({kind,key:k,previous:old.get(k),incoming:row});}
 }
 return {conflicts,added,unchanged};
}
function apply(existing,incoming,approved=[]){
 const a=archive.checked(existing),b=archive.checked(incoming),allow=new Set(approved.map(x=>x.kind+'|'+x.key));
 const result={schema_version:1,records:[],contexts:[]};
 for(const [kind,key] of [['records',id],['contexts',ctxId]]){
  const rows=new Map(a[kind].map(x=>[key(x),x]));
  for(const x of b[kind]){const k=key(x);if(!rows.has(k)||allow.has(kind+'|'+k))rows.set(k,x);}
  result[kind]=[...rows.values()];
 }
 return archive.checked(result);
}
return {preview,apply};
});
