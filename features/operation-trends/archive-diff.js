/* Compare archive snapshots without persisting personal browsing history. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./local-archive'):root.SlotLocalArchive);if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotArchiveDiff=api;})(typeof globalThis!=='undefined'?globalThis:this,function(archive){
'use strict';
const key=e=>e.original_post_id?e.type+'|'+e.original_post_id:e.source_id+'|'+e.id;
const contextKey=c=>JSON.stringify([c.store_id,c.machine_id,c.as_of]);
function compare(before,after){
 const a=archive.checked(before),b=archive.checked(after),ar=new Map(a.records.map(x=>[key(x),x])),br=new Map(b.records.map(x=>[key(x),x]));
 const ac=new Map(a.contexts.map(x=>[contextKey(x),x])),bc=new Map(b.contexts.map(x=>[contextKey(x),x]));
 const changes=(oldMap,newMap)=>({added:[...newMap.keys()].filter(k=>!oldMap.has(k)),removed:[...oldMap.keys()].filter(k=>!newMap.has(k)),modified:[...newMap.keys()].filter(k=>oldMap.has(k)&&JSON.stringify(oldMap.get(k))!==JSON.stringify(newMap.get(k)))});
 return {schema_version:1,evidence:changes(ar,br),machine_context:changes(ac,bc),description:'同一IDの内容変更を検出。出典内容の真偽や変更理由は自動判定しない。'};
}
return {compare};
});
