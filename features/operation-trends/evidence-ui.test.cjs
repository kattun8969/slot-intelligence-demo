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
