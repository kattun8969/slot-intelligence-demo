/* Explain changes in store machine mix without claiming setting allocations. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./machine-context'):root.SlotMachineContext);if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotContextShift=api;})(typeof globalThis!=='undefined'?globalThis:this,function(context){
'use strict';
function compare(rows,opts={}){
 const {store_id,asOf}=opts,previousDays=opts.previousDays??90;
 if(typeof store_id!=='string'||!store_id.trim())throw Error('store_id required');
 if(!/^\d{4}-\d{2}-\d{2}$/.test(asOf||'')||!Number.isInteger(previousDays)||previousDays<1||previousDays>3650)throw Error('invalid comparison');
 const date=new Date(asOf+'T00:00:00Z');if(!Number.isFinite(date.getTime())||date.toISOString().slice(0,10)!==asOf)throw Error('invalid asOf');
 date.setUTCDate(date.getUTCDate()-previousDays);const priorDate=date.toISOString().slice(0,10);
 const recent=context.latest(rows,asOf).filter(x=>x.store_id===store_id),previous=context.latest(rows,priorDate).filter(x=>x.store_id===store_id);
 const current=new Map(recent.map(x=>[x.machine_id,x])),prior=new Map(previous.map(x=>[x.machine_id,x]));
 const result=[...new Set([...current.keys(),...prior.keys()])].sort().map(machine_id=>{
  const a=current.get(machine_id),b=prior.get(machine_id);
  const changes=[];
  if(!b)changes.push('過去時点の設置情報なし');
  if(!a)changes.push('現在時点の設置情報なし');
  if(a&&b){
   if(a.installed_units!==b.installed_units)changes.push('設置台数 '+b.installed_units+'→'+a.installed_units);
   if(a.placement!==b.placement)changes.push('設置区分 '+b.placement+'→'+a.placement);
   if(a.popularity!==null&&b.popularity!==null&&a.popularity!==b.popularity)changes.push('人気指標の変化（測定条件の一致確認が必要）');
  }
  return {machine_id,previous_as_of:b?.as_of??null,current_as_of:a?.as_of??null,previous_units:b?.installed_units??null,current_units:a?.installed_units??null,changes,setting_probability:null,allocation_shift:'未判定'};
 });
 return {schema_version:1,store_id,as_of:asOf,previous_as_of:priorDate,description:'設置・人気の変化と設定配分の変化は別。情報がない機種を撤去と断定しない。',rows:result};
}
return {compare};
});
