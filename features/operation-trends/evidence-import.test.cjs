const test=require('node:test'),assert=require('node:assert/strict');
const {importRecords}=require('./evidence-import');
const base={id:'1',type:'official_event_result',store_id:'store',machine_id:'machine',source_id:'source',source_url:'https://example.org/result',event_date:'2026-11-01',published_date:'2026-11-02',collected_date:'2026-11-03',rights:'verified',verification:'reported',announcement_timing:'postevent'};
test('accept verified post-event result without treating it as a confirmed setting',()=>{const r=importRecords([base]);assert.equal(r.accepted_count,1);assert.equal(r.accepted[0].type,'official_event_result');});
test('reject unknown rights',()=>assert.equal(importRecords([{...base,rights:'unverified'}]).rejected_count,1));
test('reject missing timing',()=>assert.equal(importRecords([{...base,announcement_timing:undefined}]).rejected_count,1));
test('reject dangerous URLs',()=>assert.equal(importRecords([{...base,source_url:'javascript:alert(1)'}]).rejected_count,1));
test('require confirmation basis',()=>assert.equal(importRecords([{...base,type:'confirmed_setting',verification:'verified',confirmation_basis:undefined}]).rejected_count,1));
test('keep valid rows and report rejected rows',()=>{const r=importRecords([base,{...base,id:''}]);assert.equal(r.accepted_count,1);assert.deepEqual(r.rejected.map(x=>x.row),[2]);});
