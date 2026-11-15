const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'evidence.html'),'utf8');
test('inline JavaScript parses',()=>{
 const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]).filter(Boolean);
 assert.ok(scripts.length,'inline script missing');
 for(const script of scripts)new vm.Script(script,{filename:'evidence.html'});
});
test('individual review UI has actionable controls',()=>{
 for(const id of ['reviewPanel','reviewItems','reviewApply','reviewCancel','restoreFile','saveArchive'])assert.match(html,new RegExp('id="'+id+'"'));
});
test('page references existing local JavaScript modules',()=>{
 const srcs=[...html.matchAll(/<script\s+src="([^"]+)"\s*><\/script>/g)].map(x=>x[1]);
 assert.ok(srcs.length>5);
 for(const src of srcs){assert.ok(src.startsWith('./'),'only local scripts permitted');assert.ok(fs.existsSync(path.join(__dirname,src)),'missing script: '+src);}
});
test('element IDs are unique',()=>{
 const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);
 assert.ok(ids.length>10);
 assert.equal(ids.length,new Set(ids).size);
});

test('backup carries revision history and restore defers it during review',()=>{
 assert.match(html,/revision_history:SlotRevisionHistory\.checked\(history\)/);
 assert.match(html,/pendingReview\.importedHistory=importedHistory/);
 assert.match(html,/mergeImportedHistory\(importedHistory\)/);
});
test('pending review blocks deleting local archive',()=>{
 assert.match(html,/if\(pendingReview\)\{\$\('status'\)\.textContent='変更確認を完了してから削除してください'/);
});
