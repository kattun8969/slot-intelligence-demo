/* Temporal comparison of evidence, not a setting-probability estimator. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./evidence-engine'):root.SlotEvidence);if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotTrend=api;})(typeof globalThis!=='undefined'?globalThis:this,function(engine){
'use strict';
const dateOK=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))&&new Date(s+'T00:00:00Z').toISOString().slice(0,10)===s;
function shift(date,days){const d=new Date(date+'T00:00:00Z');d.setUTCDate(d.getUTCDate()+days);return d.toISOString().slice(0,10);}
function summarize(records,opts={}){
 const asOf=opts.asOf;if(!dateOK(asOf))throw Error('asOf required');
 const recentDays=opts.recentDays??28,baselineDays=opts.baselineDays??90;
 if(!Number.isInteger(recentDays)||recentDays<1||!Number.isInteger(baselineDays)||baselineDays<recentDays||baselineDays>3650)throw Error('invalid windows');
 const oldEnd=shift(asOf,-recentDays),oldStart=shift(oldEnd,-baselineDays+1);
 const recentStart=shift(asOf,-recentDays+1);
 const eligible=engine.deduplicate(records).filter(e=>e.rights==='verified'&&e.published_date<=asOf&&e.collected_date<=asOf&&e.event_date<=asOf&&(!opts.store_id||e.store_id===opts.store_id)&&(!opts.machine_id||e.machine_id===opts.machine_id));
 const window=(from,to)=>{const rows=eligible.filter(e=>e.event_date>=from&&e.event_date<=to);
  const sourceCount=new Set(rows.map(e=>e.source_id)).size;
  const confirmations=rows.filter(e=>e.type==='confirmed_setting'&&e.verification==='verified').length;
  const eventTargets=rows.filter(e=>e.type==='official_event_result').length;
  const social=rows.filter(e=>e.type==='social_report').length;
  const contradicting=rows.filter(e=>e.contradicts===true).length;
  const observed=rows.filter(e=>e.type==='public_machine_data');
  const games=observed.reduce((n,e)=>n+e.games,0),coins=observed.reduce((n,e)=>n+e.net_coins,0);
  return {from,to,records:rows.length,days:new Set(rows.map(e=>e.event_date)).size,independent_sources:sourceCount,confirmed_reports:confirmations,event_targets:eventTargets,social_reports:social,contradictions:contradicting,observations:observed.length,total_games:games,avg_net_coins:observed.length?coins/observed.length:null};
 };
 const recent=window(recentStart,asOf),baseline=window(oldStart,oldEnd);
 // Counts from unequal windows are not comparable without normalization.
 const rate=(w,calendarDays)=>(w.confirmed_reports+w.event_targets)/calendarDays;
 const a=rate(recent,recentDays),b=rate(baseline,baselineDays);
 let direction='判断不可';
 // This is a change in reported evidence frequency, not change in setting probability.
 if(recent.days>=5&&baseline.days>=5&&recent.independent_sources>=2&&baseline.independent_sources>=2&&a!==null&&b!==null){
  if(a===0&&b===0)direction='変化を示す証拠なし';
  else if(a>b*1.5)direction='根拠報告が増加';
  else if(a<b/1.5)direction='根拠報告が減少';
  else direction='根拠報告は概ね横ばい';
 }
 return {schema_version:1,as_of:asOf,store_id:opts.store_id??null,machine_id:opts.machine_id??null,recent,baseline,reported_evidence_direction:direction,recent_reports_per_calendar_day:a,baseline_reports_per_calendar_day:b,setting_probability:null,prospective_signal:'判断不可',disclaimer:'公開済み根拠の報告頻度の比較。高設定投入率・今後の投入確率ではない。報告件数は暦日で正規化。観測日の偏り・媒体数・公開バイアスに注意。'};
}
return {summarize};
});
