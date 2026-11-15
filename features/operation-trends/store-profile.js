/* Join historical machine characteristics with dated evidence, without causal claims. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./machine-evidence'):root.SlotMachineEvidence,typeof module==='object'&&module.exports?require('./machine-context'):root.SlotMachineContext);if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotStoreProfile=api;})(typeof globalThis!=='undefined'?globalThis:this,function(evidence,context){
'use strict';
function profile(records,contexts,options={}){
 const comparison=evidence.compareMachines(records,options);
 const active=context.latest(contexts,options.asOf).filter(x=>x.store_id===options.store_id);
 const map=new Map(active.map(x=>[x.machine_id,x]));
 const ids=new Set([...comparison.rows.map(x=>x.machine_id),...active.map(x=>x.machine_id)]);
 const evidenceMap=new Map(comparison.rows.map(x=>[x.machine_id,x]));
 const rows=[...ids].sort().map(machine_id=>{
  const e=evidenceMap.get(machine_id)||null,c=map.get(machine_id)||null;
  const notes=[];
  if(c)notes.push(...c.hypotheses);
  if(e&&e.recent_evidence>e.previous_evidence)notes.push('直近の根拠件数が過去期間の件数を上回る。ただし比較期間の長さが異なるため投入増とは判断できない');
  if(e&&e.contradictions)notes.push('矛盾報告あり：根拠の再確認が必要');
  if(!e||!e.recent_evidence)notes.push('直近の取材・確定報告は登録されていない');
  return {machine_id,context_as_of:c?.as_of??null,installed_units:c?.installed_units??null,placement:c?.placement??'unknown',volatility:c?.volatility??'unknown',recent_evidence:e?.recent_evidence??0,independent_sources:e?.independent_sources??0,contradictions:e?.contradictions??0,hypotheses:notes,setting_probability:null,prospective_signal:'判断不可'};
 });
 return {schema_version:1,store_id:options.store_id,as_of:options.asOf,description:'店舗別の機種特性と公開根拠の照合。予測順位ではない。',rows};
}
return {profile};
});
