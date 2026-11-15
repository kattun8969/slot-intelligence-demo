const test=require('node:test'),assert=require('node:assert/strict');
const {summarize}=require('./temporal-trends');
const base={id:'x',type:'official_event_result',store_id:'s',machine_id:'m',source_id:'a',source_url:'https://example.com',event_date:'2026-10-01',published_date:'2026-10-02',collected_date:'2026-10-03',rights:'verified',verification:'reported'};
test('disjoint recent and historical windows',()=>{
 const x=summarize([base,{...base,id:'y',event_date:'2026-11-01',published_date:'2026-11-02',collected_date:'2026-11-03'}],{asOf:'2026-11-15'});
 assert.equal(x.recent.records,1);assert.equal(x.baseline.records,1);assert.equal(x.setting_probability,null);
});
test('future publication excluded even if event occurred earlier',()=>{
 const x=summarize([{...base,published_date:'2026-11-20',collected_date:'2026-11-21'}],{asOf:'2026-11-15'});
 assert.equal(x.recent.records+x.baseline.records,0);
});
test('no evidence is not a negative setting prediction',()=>{
 const x=summarize([],{asOf:'2026-11-15'});
 assert.equal(x.reported_evidence_direction,'判断不可');assert.equal(x.prospective_signal,'判断不可');
});
test('source rights are enforced',()=>{
 const x=summarize([{...base,rights:'unverified'}],{asOf:'2026-11-15'});
 assert.equal(x.baseline.records,0);
});
test('windows must be valid',()=>assert.throws(()=>summarize([],{asOf:'2026-11-15',recentDays:90,baselineDays:28})));
test('store and machine filtering',()=>{
 const x=summarize([base,{...base,id:'z',store_id:'other'}],{asOf:'2026-11-15',store_id:'s',machine_id:'m'});
 assert.equal(x.baseline.records,1);
});
