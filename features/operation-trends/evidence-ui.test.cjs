const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
test('evidence page inline JavaScript parses',()=>{
 const html=fs.readFileSync(path.join(__dirname,'evidence.html'),'utf8');
 const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]).filter(Boolean);
 assert.ok(scripts.length,'inline script missing');
 for(const script of scripts)new vm.Script(script,{filename:'evidence.html'});
});
test('individual review UI has actionable controls',()=>{
 const html=fs.readFileSync(path.join(__dirname,'evidence.html'),'utf8');
 for(const id of ['reviewPanel','reviewItems','reviewApply','reviewCancel','restoreFile','saveArchive'])assert.match(html,new RegExp('id="'+id+'"'));
});

test('evidence page scripts reference existing local modules',()=>{
 const html=fs.readFileSync(path.join(__dirname,'evidence.html'),'utf8');
 const srcs=[...html.matchAll(/<script\\s+src="([^"]+)"\\s*><\\/script>/g)].map(x=>x[1]);
 assert.ok(srcs.length>5);
 for(const src of srcs){assert.ok(src.startsWith('./'),'only local scripts permitted');assert.ok(fs.existsSync(path.join(__dirname,src)),'missing script: '+src);}
});
test('evidence page has unique element IDs',()=>{
 const html=fs.readFileSync(path.join(__dirname,'evidence.html'),'utf8');
 const ids=[...html.matchAll(/\\bid="([^"]+)"/g)].map(x=>x[1]);
 assert.equal(ids.length,new Set(ids).size);
});
