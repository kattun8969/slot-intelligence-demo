const test=require('node:test'),assert=require('node:assert/strict');const {compare}=require('./evidence-shift');
const base={id:'1',type:'official_event_result',store_id:'s',machine_id:'m',source_id:'source',source_url:'https://example.org',event_date:'2026-11-01',published_date:'2026-11-02',collected_date:'2026-11-03',rights:'verified',verification:'reported'};
test('requires store',()=>assert.throws(()=>compare([],{asOf:'2026-11-15'})));
test('does not imply setting probabilities',()=>{const x=compare([base],{store_id:'s',asOf:'2026-11-15'});assert.equal(x.rows[0].setting_probability,null);assert.equal(x.rows[0].change,'判断不可');});
test('exclude other store',()=>{const x=compare([base,{...base,id:'2',store_id:'other',machine_id:'other'}],{store_id:'s',asOf:'2026-11-15'});assert.equal(x.rows.length,1);});
test('future publication does not enter history',()=>{const x=compare([{...base,published_date:'2026-11-20',collected_date:'2026-11-21'}],{store_id:'s',asOf:'2026-11-15'});assert.equal(x.rows[0].recent_reports,0);});
