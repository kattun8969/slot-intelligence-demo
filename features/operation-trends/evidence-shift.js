/* Historical shifts in documented evidence, not setting allocations. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./temporal-trends'):root.SlotTrend);if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotEvidenceShift=api;})(typeof globalThis!=='undefined'?globalThis:this,function(trend){
'use strict';
function compare(records,options={}){
 const {store_id,asOf}=options;
 if(typeof store_id!=='string'||!store_id.trim())throw Error('store_id required');
 const machines=[...new Set(records.filter(x=>x&&x.store_id===store_id&&typeof x.machine_id==='string').map(x=>x.machine_id))].sort();
 const rows=machines.map(machine_id=>{
  const t=trend.summarize(records,{asOf,store_id,machine_id,recentDays:options.recentDays??28,baselineDays:options.baselineDays??90});
  const a=t.recent.confirmed_reports+t.recent.event_targets,b=t.baseline.confirmed_reports+t.baseline.event_targets;
  const recentRate=t.recent_reports_per_calendar_day,baselineRate=t.baseline_reports_per_calendar_day;
  const coverage=t.recent.independent_sources>=2&&t.baseline.independent_sources>=2&&t.recent.days>=5&&t.baseline.days>=5;
  const change=coverage?(recentRate>baselineRate*1.5?'根拠報告増加':recentRate<baselineRate/1.5?'根拠報告減少':'概ね横ばい'):'判断不可';
  return {machine_id,recent_reports:a,previous_reports:b,recent_per_day:recentRate,previous_per_day:baselineRate,recent_sources:t.recent.independent_sources,previous_sources:t.baseline.independent_sources,change,setting_probability:null};
 });
 return {schema_version:1,store_id,as_of:asOf,description:'取材・設定確定報告の公開件数推移。設定投入の増減を直接示さない。',rows};
}
return {compare};
});
