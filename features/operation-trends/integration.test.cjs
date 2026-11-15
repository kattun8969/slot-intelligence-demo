const test=require('node:test'),assert=require('node:assert/strict');
const importer=require('./evidence-import'),archive=require('./local-archive'),review=require('./import-review'),history=require('./revision-history'),trend=require('./temporal-trends');
const row={id:'r1',type:'social_report',store_id:'shop-a',machine_id:'machine-a',source_id:'source-a',source_url:'https://example.org/post',event_date:'2026-11-01',published_date:'2026-11-02',collected_date:'2026-11-03',rights:'verified',verification:'reported'};
const blank={schema_version:1,records:[],contexts:[]},observed='2026-11-15T04:00:00.000Z';
test('integration: import, approve correction, archive save/load, history, analysis',()=>{
 const imported=importer.importRecords([row]);assert.equal(imported.rejected_count,0);
 const initial=review.apply(blank,{...blank,records:imported.accepted});
 assert.equal(initial.records.length,1);
 let log=history.record(history.empty(),blank,initial,observed);assert.equal(log.entries.length,1);
 const changed={...row,contradicts:true},incoming={...blank,records:importer.importRecords([changed]).accepted};
 const pending=review.preview(initial,incoming);assert.equal(pending.conflicts.length,1);
 assert.equal(review.apply(initial,incoming).records[0].contradicts,undefined);
 const approved=review.apply(initial,incoming,[{kind:'records',key:'source-a|r1'}]);
 assert.equal(approved.records[0].contradicts,true);
 log=history.record(log,initial,approved,observed);assert.equal(log.entries[1].action,'updated');
 assert.equal(log.entries[1].previous.contradicts,undefined);
 const mem=new Map(),storage={getItem:k=>mem.get(k)??null,setItem:(k,v)=>mem.set(k,v),removeItem:k=>mem.delete(k)};
 archive.save(storage,approved);const restored=archive.load(storage);
 assert.equal(restored.records[0].contradicts,true);
 const result=trend.summarize(restored.records,{asOf:'2026-11-15',store_id:'shop-a'});
 assert.ok(result&&typeof result==='object');
});
test('integration: invalid archive is rejected without changing original',()=>{
 const original={...blank,records:[row]};
 assert.throws(()=>review.preview(original,{...blank,records:[{...row,source_url:'javascript:alert(1)'}]}));
 assert.equal(original.records[0].source_url,'https://example.org/post');
});
