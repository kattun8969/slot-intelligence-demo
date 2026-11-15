const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
test('homepage links to operation trends features',()=>{
 const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
 for(const href of ['./features/operation-trends/index.html','./features/operation-trends/evidence.html']){
  assert.ok(html.includes('href="'+href+'"'),'missing homepage link: '+href);
  assert.ok(fs.existsSync(path.resolve(root,href)),'missing destination: '+href);
 }
});
test('homepage keeps existing on-site input and notes tools',()=>{
 const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
 for(const id of ['tier','machine'])assert.ok(html.includes('id="'+id+'"'),'missing existing control: '+id);
 assert.ok(html.includes('feature-navigation'),'missing feature navigation');
});
