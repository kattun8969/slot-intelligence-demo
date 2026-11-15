const test=require('node:test'),assert=require('node:assert/strict');const {compareMachines}=require('./machine-evidence');
const base={id:'a',type:'official_event_result',store_id:'s',machine_id:'m1',source_id:'source1',source_url:'https://example.org/a',event_date:'2026-11-01',published_date:'2026-11-02',collected_date:'2026-11-03',rights:'verified',verification:'reported'};
test('requires store scope',()=>assert.throws(()=>compareMachines([],{asOf:'2026-11-15'})));
test('reports coverage without setting probability',()=>{const x=compareMachines([base],{asOf:'2026-11-15',store_id:'s'});assert.equal(x.rows[0].recent_evidence,1);assert.equal(x.rows[0].setting_probability,null);});
test('sorts by recent documented event evidence',()=>{const x=compareMachines([base,{...base,id:'b',machine_id:'m2',source_id:'source2'},{...base,id:'c',machine_id:'m2',source_id:'source3'}],{asOf:'2026-11-15',store_id:'s'});assert.equal(x.rows[0].machine_id,'m2');});
test('other store excluded',()=>{const x=compareMachines([base,{...base,id:'z',store_id:'other',machine_id:'other'}],{asOf:'2026-11-15',store_id:'s'});assert.equal(x.rows.length,1);});
test('future-published event not counted',()=>{const x=compareMachines([{...base,published_date:'2026-11-20',collected_date:'2026-11-21'}],{asOf:'2026-11-15',store_id:'s'});assert.equal(x.rows[0].recent_evidence,0);});
