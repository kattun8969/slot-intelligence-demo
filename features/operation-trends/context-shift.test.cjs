const test=require('node:test'),assert=require('node:assert/strict');const {compare}=require('./context-shift');
const base={store_id:'s',machine_id:'m',as_of:'2026-07-01',source_url:'https://example.org',rights:'verified',placement:'variety',volatility:'stable',installed_units:1,popularity:0.3};
test('captures machine growth',()=>{const r=compare([base,{...base,as_of:'2026-11-15',installed_units:5,placement:'main'}],{store_id:'s',asOf:'2026-11-15'});assert.ok(r.rows[0].changes.some(x=>x.includes('1→5')));});
test('missing earlier data is not removal',()=>{const r=compare([{...base,as_of:'2026-11-15'}],{store_id:'s',asOf:'2026-11-15'});assert.ok(r.rows[0].changes.includes('過去時点の設置情報なし'));assert.equal(r.rows[0].allocation_shift,'未判定');});
test('future context excluded',()=>{const r=compare([{...base,as_of:'2026-12-01'}],{store_id:'s',asOf:'2026-11-15'});assert.equal(r.rows.length,0);});
test('rejects missing store',()=>assert.throws(()=>compare([],{asOf:'2026-11-15'})));
test('rejects invalid date',()=>assert.throws(()=>compare([],{store_id:'s',asOf:'2026-02-30'})));
