/* Qualitative context: hypotheses, not machine-setting probabilities. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SlotMachineContext=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const types=new Set(['main','variety','unknown']),volatility=new Set(['stable','volatile','unknown']);
function normalize(row){
 if(!row||typeof row!=='object')throw Error('invalid context');
 for(const k of ['store_id','machine_id','as_of','source_url'])if(typeof row[k]!=='string'||!row[k].trim())throw Error('missing '+k);
 if(!/^\d{4}-\d{2}-\d{2}$/.test(row.as_of)||Number.isNaN(Date.parse(row.as_of))||new Date(row.as_of+'T00:00:00Z').toISOString().slice(0,10)!==row.as_of)throw Error('invalid as_of');
 try{if(!['https:','http:'].includes(new URL(row.source_url).protocol))throw Error('invalid URL');}catch{throw Error('invalid URL');}
 if(row.rights!=='verified')throw Error('rights not verified');
 if(!types.has(row.placement)||!volatility.has(row.volatility))throw Error('invalid category');
 if(!Number.isInteger(row.installed_units)||row.installed_units<1)throw Error('invalid installed_units');
 if(row.popularity!==null&&row.popularity!==undefined&&(!Number.isFinite(row.popularity)||row.popularity<0||row.popularity>1))throw Error('invalid popularity');
 return {...row};
}
function describe(row){
 const v=normalize(row),hypotheses=[];
 if(v.placement==='variety')hypotheses.push('バラエティ設置：投入が少ない可能性があるが店舗次第');
 if(v.placement==='main')hypotheses.push('主力設置：見せ台として活用される可能性がある');
 if(v.volatility==='stable')hypotheses.push('安定型：出玉が目立ちにくい一方、見せ台・利益管理の両面が考えられる');
 if(v.volatility==='volatile')hypotheses.push('荒波型：出玉訴求の一方、差枚だけでは設定が判別しづらい');
 if(v.popularity!==null&&v.popularity!==undefined)hypotheses.push('人気指標は店舗固有の実績と照合する必要がある');
 return {store_id:v.store_id,machine_id:v.machine_id,as_of:v.as_of,installed_units:v.installed_units,placement:v.placement,volatility:v.volatility,popularity:v.popularity??null,hypotheses,setting_probability:null,source_url:v.source_url};
}
function latest(rows,asOf){const map=new Map();for(const r of rows){const v=normalize(r);if(v.as_of>asOf)continue;const k=v.store_id+'|'+v.machine_id;if(!map.has(k)||map.get(k).as_of<v.as_of)map.set(k,v);}return [...map.values()].map(describe);}
return {normalize,describe,latest};
});
