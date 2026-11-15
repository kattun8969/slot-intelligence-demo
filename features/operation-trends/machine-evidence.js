/* Compare evidence coverage by machine, not inferred setting strength. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./temporal-trends'):root.SlotTrend);if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotMachineEvidence=api;})(typeof globalThis!=='undefined'?globalThis:this,function(trends){
'use strict';
function compareMachines(records,options={}){
 const asOf=options.asOf,store_id=options.store_id;
 if(typeof store_id!=='string'||!store_id.trim())throw Error('store_id required');
 const ids=[...new Set(records.filter(x=>x&&x.store_id===store_id&&typeof x.machine_id==='string').map(x=>x.machine_id))].sort();
 const rows=ids.map(machine_id=>{
  const t=trends.summarize(records,{asOf,store_id,machine_id,recentDays:options.recentDays??28,baselineDays:options.baselineDays??90});
  const recent=t.recent,old=t.baseline;
  const evidenceCount=recent.confirmed_reports+recent.event_targets;
  const independent=recent.independent_sources;
  // No claim about high-setting allocation; only strength of documented evidence.
  const coverage=evidenceCount>=3&&independent>=2&&recent.days>=2?'複数日・複数情報源':evidenceCount?'限定的な根拠':'対象期間の根拠なし';
  return {machine_id,store_id,as_of:asOf,recent_evidence:evidenceCount,previous_evidence:old.confirmed_reports+old.event_targets,
   recent_social_reports:recent.social_reports,independent_sources:independent,contradictions:recent.contradictions,
   reported_evidence_direction:t.reported_evidence_direction,evidence_coverage:coverage,
   prospective_signal:'判断不可',setting_probability:null};
 });
 // Sort by independently corroborated evidence coverage, not by estimated setting probability.
 rows.sort((a,b)=>b.recent_evidence-a.recent_evidence||b.independent_sources-a.independent_sources||a.machine_id.localeCompare(b.machine_id,'ja'));
 return {schema_version:1,store_id,as_of:asOf,ranking_type:'根拠の掲載状況（設定投入期待度ではない）',rows};
}
return {compareMachines};
});
