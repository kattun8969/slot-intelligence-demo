const test=require('node:test'),assert=require('node:assert/strict');const {normalize,describe,latest}=require('./machine-context');
const base={store_id:'store',machine_id:'machine',as_of:'2026-11-01',source_url:'https://example.org/store',rights:'verified',placement:'variety',volatility:'stable',installed_units:1,popularity:null};
test('accept context with provenance',()=>assert.equal(normalize(base).installed_units,1));
test('reject unknown rights',()=>assert.throws(()=>normalize({...base,rights:'unverified'})));
test('reject non-http URL',()=>assert.throws(()=>normalize({...base,source_url:'javascript:alert(1)'})));
test('reject invalid popularity',()=>assert.throws(()=>normalize({...base,popularity:2})));
test('hypotheses do not assert setting probability',()=>{const v=describe(base);assert.equal(v.setting_probability,null);assert.ok(v.hypotheses.some(x=>x.includes('バラエティ')));});
test('latest context is as-of bounded',()=>{const v=latest([base,{...base,as_of:'2026-11-20',installed_units:4}], '2026-11-15');assert.equal(v[0].installed_units,1);});
test('invalid dates rejected',()=>assert.throws(()=>normalize({...base,as_of:'2026-02-30'})));
