/* Evidence engine v1: no network, no assumptions of confirmed settings. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotEvidence=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const TYPES=new Set(['official_event_result','confirmed_setting','social_report','public_machine_data','store_event','machine_context']);
const iso=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s+'T00:00:00Z').toISOString().slice(0,10)===s;
const safeUrl=s=>{try{return ['https:','http:'].includes(new URL(s).protocol);}catch(_){return false;}};
function validate(e){
 if(!e||typeof e!=='object'||!TYPES.has(e.type))throw Error('unknown evidence type');
 for(const k of ['id','store_id','machine_id','source_id'])if(typeof e[k]!=='string'||!e[k].trim())throw Error('missing '+k);
 for(const k of ['event_date','published_date','collected_date'])if(!iso(e[k]))throw Error('invalid '+k);
 if(e.published_date>e.collected_date)throw Error('published after collected');
 if(!safeUrl(e.source_url))throw Error('invalid source_url');
 if(!['verified','unverified','prohibited'].includes(e.rights))throw Error('invalid rights');
 if(!['verified','reported','inferred','unknown'].includes(e.verification))throw Error('invalid verification');
 if(e.type==='confirmed_setting'&&e.verification==='verified'&&(!e.confirmation_basis||!e.confirmation_basis.trim()))throw Error('confirmation basis required');
 if(e.type==='public_machine_data'){
  if(!Number.isFinite(e.games)||e.games<0||!Number.isFinite(e.net_coins))throw Error('invalid machine data');
 }
 return true;
}
function deduplicate(records){
 const seen=new Set(),result=[];
 for(const e of records){validate(e);const key=e.original_post_id?e.type+'|'+e.original_post_id:e.source_id+'|'+e.id;if(seen.has(key))continue;seen.add(key);result.push(e);}
 return result;
}
function assess(records,options={}){
 const asOf=options.asOf||new Date().toISOString().slice(0,10);if(!iso(asOf))throw Error('invalid asOf');
 const windowDays=options.windowDays===undefined?28:options.windowDays;
 if(!Number.isInteger(windowDays)||windowDays<1||windowDays>3650)throw Error('invalid window');
 const store=options.store_id,machine=options.machine_id;
 const cutoff=new Date(asOf+'T00:00:00Z');cutoff.setUTCDate(cutoff.getUTCDate()-windowDays+1);
 const from=cutoff.toISOString().slice(0,10);
 const eligible=deduplicate(records).filter(e=>e.event_date>=from&&e.event_date<=asOf&&e.published_date<=asOf&&e.collected_date<=asOf&&e.rights==='verified'&&(!store||e.store_id===store)&&(!machine||e.machine_id===machine));
 const independent=new Set(eligible.map(e=>e.source_id));
 const confirmations=eligible.filter(e=>e.type==='confirmed_setting'&&e.verification==='verified');
 const eventResults=eligible.filter(e=>e.type==='official_event_result');
 const reports=eligible.filter(e=>e.type==='social_report');
 const machineData=eligible.filter(e=>e.type==='public_machine_data');
 const counterEvidence=eligible.filter(e=>e.contradicts===true);
 const quality=eligible.length>=12&&independent.size>=4?'中':eligible.length>=5&&independent.size>=2?'低':'不足';
 // Do not infer setting probabilities from social chatter or net coins.
 return {schema_version:1,as_of:asOf,from,store_id:store||null,machine_id:machine||null,
  evidence_count:eligible.length,independent_source_count:independent.size,
  confirmed_report_count:confirmations.length,event_result_count:eventResults.length,
  social_report_count:reports.length,machine_data_count:machineData.length,
  counter_evidence_count:counterEvidence.length,evidence_quality:quality,
  historical_evidence:confirmations.length?'確認報告あり（根拠の個別確認が必要）':eventResults.length?'取材結果あり（設定確定ではない）':'設定確定の根拠なし',
  prospective_signal:'判断不可',setting_probability:null,
  supporting_ids:eligible.filter(e=>!e.contradicts).map(e=>e.id),
  contradicting_ids:counterEvidence.map(e=>e.id),
  excluded_count:records.length-eligible.length,
  limitations:['情報源の独立性はsource_id単位','未公開・未取得・利用不可のデータは除外','投入率・設定確率の推定は未実装']};
}
return {validate,deduplicate,assess};
});
