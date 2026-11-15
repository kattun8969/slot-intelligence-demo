const test=require('node:test'),assert=require('node:assert/strict');const {compare}=require('./archive-diff');const empty={schema_version:1,records:[],contexts:[]};
const row={id:'1',type:'social_report',store_id:'s',machine_id:'m',source_id:'x',source_url:'https://example.org',event_date:'2026-11-01',published_date:'2026-11-02',collected_date:'2026-11-03',rights:'verified',verification:'reported'};
test('reports added evidence',()=>assert.equal(compare(empty,{...empty,records:[row]}).evidence.added.length,1));
test('reports removed evidence',()=>assert.equal(compare({...empty,records:[row]},empty).evidence.removed.length,1));
test('reports edited evidence',()=>assert.equal(compare({...empty,records:[row]},{...empty,records:[{...row,contradicts:true}]}).evidence.modified.length,1));
test('does not invent changes',()=>assert.equal(compare(empty,empty).evidence.added.length,0));
