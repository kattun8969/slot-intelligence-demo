const test=require('node:test'),assert=require('node:assert/strict');const x=require('./import-review');const row={id:'1',type:'social_report',store_id:'s',machine_id:'m',source_id:'x',source_url:'https://example.org',event_date:'2026-11-01',published_date:'2026-11-02',collected_date:'2026-11-03',rights:'verified',verification:'reported'};const a={schema_version:1,records:[row],contexts:[]},b={schema_version:1,records:[{...row,contradicts:true}],contexts:[]};
test('conflicting revision is detected',()=>assert.equal(x.preview(a,b).conflicts.length,1));
test('unapproved revision preserves original',()=>assert.equal(x.apply(a,b).records[0].contradicts,undefined));
test('approved revision replaces original',()=>assert.equal(x.apply(a,b,[{kind:'records',key:'x|1'}]).records[0].contradicts,true));
test('new evidence can be added without approval',()=>assert.equal(x.apply(a,{...b,records:[{...row,id:'2'}]}).records.length,2));
test('unchanged evidence does not trigger conflict',()=>assert.equal(x.preview(a,a).conflicts.length,0));

test('individual approval does not approve unrelated conflict',()=>{
 const old={...a,records:[row,{...row,id:'2'}]};
 const next={...a,records:[{...row,contradicts:true},{...row,id:'2',contradicts:true}]};
 const result=x.apply(old,next,[{kind:'records',key:'x|1'}]);
 assert.equal(result.records[0].contradicts,true);
 assert.equal(result.records[1].contradicts,undefined);
});
test('context change requires separate approval',()=>{
 const ctx={store_id:'s',machine_id:'m',as_of:'2026-11-01',source_url:'https://example.org',rights:'verified',placement:'main',volatility:'stable',installed_units:5};
 const before={schema_version:1,records:[],contexts:[ctx]},after={...before,contexts:[{...ctx,installed_units:6}]};
 assert.equal(x.preview(before,after).conflicts.length,1);
 assert.equal(x.apply(before,after).contexts[0].installed_units,5);
 const key=JSON.stringify(['s','m','2026-11-01']);
 assert.equal(x.apply(before,after,[{kind:'contexts',key}]).contexts[0].installed_units,6);
});
