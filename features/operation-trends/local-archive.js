/* Local-only evidence archive. Storage is supplied by caller; no network or auto-sync. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./evidence-engine'):root.SlotEvidence,typeof module==='object'&&module.exports?require('./machine-context'):root.SlotMachineContext);if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotLocalArchive=api;})(typeof globalThis!=='undefined'?globalThis:this,function(evidence,context){
'use strict';
const KEY='slot-intelligence.operation-trends.archive.v1',MAX=10000;
function checked(data){
 if(!data||data.schema_version!==1||!Array.isArray(data.records)||!Array.isArray(data.contexts))throw Error('invalid archive schema');
 if(data.records.length>MAX||data.contexts.length>MAX)throw Error('archive too large');
 for(const r of data.records){evidence.validate(r);if(r.rights!=='verified')throw Error('archive includes unverified rights');}
 const records=evidence.deduplicate(data.records);
 const contexts=data.contexts.map(context.normalize);
 return {schema_version:1,records,contexts};
}
function merge(existing,incoming){
 const a=checked(existing),b=checked(incoming);
 const records=evidence.deduplicate([...a.records,...b.records]);
 const contexts=new Map();
 for(const c of [...a.contexts,...b.contexts])contexts.set(JSON.stringify([c.store_id,c.machine_id,c.as_of]),c);
 return checked({schema_version:1,records,contexts:[...contexts.values()]});
}
function restore(existing,backup){const incoming=checked(backup),prior=checked(existing),merged=merge(prior,incoming);return {archive:merged,added_records:merged.records.length-prior.records.length,added_contexts:merged.contexts.length-prior.contexts.length};}
function load(storage){const raw=storage.getItem(KEY);return raw?checked(JSON.parse(raw)):{schema_version:1,records:[],contexts:[]};}
function save(storage,data){const valid=checked(data);storage.setItem(KEY,JSON.stringify(valid));return {records:valid.records.length,contexts:valid.contexts.length};}
function clear(storage){storage.removeItem(KEY);}
return {KEY,checked,merge,restore,load,save,clear};
});
