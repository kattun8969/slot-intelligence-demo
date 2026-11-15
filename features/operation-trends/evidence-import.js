/* Import normalized, rights-reviewed event and social evidence. No scraping. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotEvidenceImport=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const allowed=new Set(['official_event_result','confirmed_setting','social_report','public_machine_data','store_event','machine_context']);
const urlOK=s=>{try{return ['https:','http:'].includes(new URL(s).protocol);}catch{return false;}};
function normalize(row){
 if(!row||typeof row!=='object'||!allowed.has(row.type))throw Error('invalid type');
 const required=['id','type','store_id','machine_id','source_id','source_url','event_date','published_date','collected_date','rights','verification'];
 for(const k of required)if(row[k]===undefined||row[k]===null||String(row[k]).trim()==='')throw Error('missing '+k);
 if(!urlOK(row.source_url))throw Error('invalid URL');
 if(row.rights!=='verified')throw Error('source usage rights not verified');
 if(row.type==='confirmed_setting'&&row.verification==='verified'&&!row.confirmation_basis)throw Error('missing setting confirmation basis');
 if(row.type==='official_event_result'&&!['preannounced','postevent','unknown'].includes(row.announcement_timing))throw Error('event announcement timing required');
 return {...row,import_schema_version:1};
}
function importRecords(input){if(!Array.isArray(input))throw Error('expected array');const accepted=[],rejected=[];
 for(let i=0;i<input.length;i++){try{accepted.push(normalize(input[i]));}catch(e){rejected.push({row:i+1,reason:e.message});}}
 return {accepted,rejected,accepted_count:accepted.length,rejected_count:rejected.length};
}
return {normalize,importRecords};
});
