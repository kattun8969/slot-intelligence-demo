/* Append-only source revisions: never silently overwrite conflicting evidence. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./local-archive'):root.SlotLocalArchive);if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotRevisionHistory=api;})(typeof globalThis!=='undefined'?globalThis:this,function(archive){
'use strict';
const VERSION=1,MAX=20000;
function identity(x){return x.original_post_id?x.type+'|'+x.original_post_id:x.source_id+'|'+x.id;}
function contextIdentity(x){return JSON.stringify([x.store_id,x.machine_id,x.as_of]);}
function canonical(x){if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';if(x&&typeof x==='object')return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';return JSON.stringify(x);}
function snapshot(a){const valid=archive.checked(a);return {records:valid.records,contexts:valid.contexts};}
function checked(h){if(!h||h.schema_version!==VERSION||!Array.isArray(h.entries)||h.entries.length>MAX)throw Error('invalid history');for(const e of h.entries){if(!e||!['record','context'].includes(e.kind)||!['added','updated','removed'].includes(e.action)||typeof e.key!=='string'||typeof e.observed_at!=='string'||!/^\d{4}-\d{2}-\d{2}T/.test(e.observed_at))throw Error('invalid history entry');}return h;}
function record(h,before,after,observedAt){const old=snapshot(before),next=snapshot(after);if(!Number.isFinite(Date.parse(observedAt))||!/^\d{4}-\d{2}-\d{2}T/.test(observedAt))throw Error('invalid observation time');
 const entries=[...checked(h).entries];
 for(const [kind,oldRows,newRows,key] of [['record',old.records,next.records,identity],['context',old.contexts,next.contexts,contextIdentity]]){
  const prev=new Map(oldRows.map(x=>[key(x),x])),curr=new Map(newRows.map(x=>[key(x),x]));
  for(const k of new Set([...prev.keys(),...curr.keys()])){
   const a=prev.get(k),b=curr.get(k);if(a&&b&&canonical(a)===canonical(b))continue;
   entries.push({kind,key:k,action:!a?'added':!b?'removed':'updated',observed_at:observedAt,previous:a??null,current:b??null});
  }
 }
 return checked({schema_version:VERSION,entries});
}
function merge(current,imported){
 const a=checked(current),b=checked(imported);
 const seen=new Set(a.entries.map(canonical));
 const entries=[...a.entries];
 for(const e of b.entries){const key=canonical(e);if(!seen.has(key)){seen.add(key);entries.push(e);}}
 return checked({schema_version:VERSION,entries});
}
function empty(){return {schema_version:VERSION,entries:[]};}
return {empty,checked,record,merge};
});
