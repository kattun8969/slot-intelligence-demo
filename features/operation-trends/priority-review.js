/* Distinguish evidence changes from changes in store machine mix. No setting prediction. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./evidence-shift'):root.SlotEvidenceShift,typeof module==='object'&&module.exports?require('./context-shift'):root.SlotContextShift);if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotPriorityReview=api;})(typeof globalThis!=='undefined'?globalThis:this,function(evidence,context){
'use strict';
function review(records,contexts,options={}){
 const e=evidence.compare(records,options),c=context.compare(contexts,options);
 const cm=new Map(c.rows.map(x=>[x.machine_id,x])),em=new Map(e.rows.map(x=>[x.machine_id,x]));
 const ids=[...new Set([...cm.keys(),...em.keys()])].sort();
 const rows=ids.map(machine_id=>{
  const a=em.get(machine_id),b=cm.get(machine_id),reasons=[];
  const changedMix=!!b&&b.changes.some(x=>x.startsWith('設置台数')||x.startsWith('設置区分')||x.startsWith('人気指標'));
  if(changedMix)reasons.push('設置構成または人気指標が変化');
  if(!b||b.previous_units===null||b.current_units===null)reasons.push('前後の設置情報が揃っていない');
  if(!a||a.change==='判断不可')reasons.push('報告頻度の比較に必要な独立情報源・日数が不足');
  const increase=!!a&&a.change==='根拠報告増加',decrease=!!a&&a.change==='根拠報告減少';
  if(increase)reasons.push('取材・確定報告の頻度が増加');
  if(decrease)reasons.push('取材・確定報告の頻度が減少');
  let classification='根拠不足';
  if(increase&&changedMix)classification='報告増加と設置変化が同時発生';
  else if(increase&&b&&b.previous_units!==null&&b.current_units!==null&&!changedMix)classification='設置変化を伴わない報告増加';
  else if(increase)classification='報告増加・設置情報不足';
  else if(decrease)classification='報告減少';
  else if(a&&a.change==='概ね横ばい')classification='報告は概ね横ばい';
  return {machine_id,classification,change:a?.change??'判断不可',mix_changed:changedMix,reasons,setting_probability:null,priority_shift:'未判定'};
 });
 return {schema_version:1,store_id:options.store_id,as_of:options.asOf,description:'報告増加と設置・人気変化の交絡を整理する参考分類。設定投入先の変更を証明しない。',rows};
}
return {review};
});
