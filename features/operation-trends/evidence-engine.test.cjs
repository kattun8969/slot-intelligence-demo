const assert=require('node:assert/strict');
const test=require('node:test');
const {validate,deduplicate,assess}=require('./evidence-engine');
const base={id:'1',type:'social_report',store_id:'shop',machine_id:'machine',source_id:'user1',source_url:'https://example.org/post',event_date:'2026-11-01',published_date:'2026-11-02',collected_date:'2026-11-03',rights:'verified',verification:'reported'};
test('valid evidence',()=>assert.equal(validate(base),true));
test('reject missing provenance',()=>assert.throws(()=>validate({...base,source_url:'javascript:alert(1)'})));
test('reject invalid calendar dates',()=>assert.throws(()=>validate({...base,event_date:'2026-02-30'})));
test('verified setting requires basis',()=>assert.throws(()=>validate({...base,type:'confirmed_setting',verification:'verified'})));
test('social reposts are deduplicated',()=>assert.equal(deduplicate([{...base,original_post_id:'abc'},{...base,id:'2',original_post_id:'abc'}]).length,1));
test('future-published evidence is excluded from backtest',()=>{
 const result=assess([base,{...base,id:'2',published_date:'2026-11-12',collected_date:'2026-11-13'}],{asOf:'2026-11-10'});
 assert.equal(result.evidence_count,1);assert.equal(result.prospective_signal,'判断不可');
});
test('prohibited and unverified rights excluded',()=>{
 const result=assess([base,{...base,id:'2',rights:'prohibited'},{...base,id:'3',rights:'unverified'}],{asOf:'2026-11-10'});
 assert.equal(result.evidence_count,1);
});
test('reported settings are not confirmed',()=>{
 const result=assess([{...base,type:'confirmed_setting',verification:'reported'}],{asOf:'2026-11-10'});
 assert.equal(result.confirmed_report_count,0);assert.equal(result.setting_probability,null);
});
test('confirmed event target is not a confirmed setting',()=>{
 const result=assess([{...base,type:'official_event_result'}],{asOf:'2026-11-10'});
 assert.equal(result.event_result_count,1);assert.equal(result.confirmed_report_count,0);
});
test('date and store filtering',()=>{
 const result=assess([base,{...base,id:'2',store_id:'other'},{...base,id:'3',event_date:'2026-09-01'}],{asOf:'2026-11-10',store_id:'shop',windowDays:28});
 assert.equal(result.evidence_count,1);
});
test('contradicting reports retained',()=>{
 const result=assess([{...base,contradicts:true}],{asOf:'2026-11-10'});
 assert.deepEqual(result.contradicting_ids,['1']);
});
