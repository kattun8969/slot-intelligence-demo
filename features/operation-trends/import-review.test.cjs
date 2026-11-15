const test=require('node:test'),assert=require('node:assert/strict');const x=require('./import-review');const row={id:'1',type:'social_report',store_id:'s',machine_id:'m',source_id:'x',source_url:'https://example.org',event_date:'2026-11-01',published_date:'2026-11-02',collected_date:'2026-11-03',rights:'verified',verification:'reported'};const a={schema_version:1,records:[row],contexts:[]},b={schema_version:1,records:[{...row,contradicts:true}],contexts:[]};
test('conflicting revision is detected',()=>assert.equal(x.preview(a,b).conflicts.length,1));
test('unapproved revision preserves original',()=>assert.equal(x.apply(a,b).records[0].contradicts,undefined));
test('approved revision replaces original',()=>assert.equal(x.apply(a,b,[{kind:'records',key:'x|1'}]).records[0].contradicts,true));
test('new evidence can be added without approval',()=>assert.equal(x.apply(a,{...b,records:[{...row,id:'2'}]}).records.length,2));
test('unchanged evidence does not trigger conflict',()=>assert.equal(x.preview(a,a).conflicts.length,0));
