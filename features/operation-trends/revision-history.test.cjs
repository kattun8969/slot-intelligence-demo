const test=require('node:test'),assert=require('node:assert/strict');const h=require('./revision-history');const empty={schema_version:1,records:[],contexts:[]};const row={id:'1',type:'social_report',store_id:'s',machine_id:'m',source_id:'x',source_url:'https://example.org',event_date:'2026-11-01',published_date:'2026-11-02',collected_date:'2026-11-03',rights:'verified',verification:'reported'};const at='2026-11-15T04:00:00.000Z';
test('records first import',()=>assert.equal(h.record(h.empty(),empty,{...empty,records:[row]},at).entries[0].action,'added'));
test('records changes with prior and current versions',()=>{const x=h.record(h.empty(),{...empty,records:[row]},{...empty,records:[{...row,contradicts:true}]},at);assert.equal(x.entries[0].action,'updated');assert.equal(x.entries[0].previous.contradicts,undefined);assert.equal(x.entries[0].current.contradicts,true);});
test('records removals',()=>assert.equal(h.record(h.empty(),{...empty,records:[row]},empty,at).entries[0].action,'removed'));
test('unchanged data does not add entries',()=>assert.equal(h.record(h.empty(),empty,empty,at).entries.length,0));
test('invalid history rejected',()=>assert.throws(()=>h.checked({schema_version:1,entries:[{}]})));

test('merge retains distinct imported history and ignores exact duplicates',()=>{
 const one=h.record(h.empty(),empty,{...empty,records:[row]},at);
 const two=h.record(h.empty(),empty,{...empty,records:[{...row,id:'2'}]},at);
 const combined=h.merge(one,two);
 assert.equal(combined.entries.length,2);
 assert.equal(h.merge(combined,one).entries.length,2);
});
test('merge rejects malformed imported history without mutating current',()=>{
 const one=h.record(h.empty(),empty,{...empty,records:[row]},at);
 assert.throws(()=>h.merge(one,{schema_version:1,entries:[{}]}));
 assert.equal(one.entries.length,1);
});

test('nested object key order is not recorded as an update',()=>{
 const before={...empty,records:[{...row,metadata:{one:1,two:{a:2,b:3}}}]};
 const after={...empty,records:[{...row,metadata:{two:{b:3,a:2},one:1}}]};
 assert.equal(h.record(h.empty(),before,after,at).entries.length,0);
});
