// Cloudflare Worker + D1. Configure DB binding and ALLOWED_ORIGIN before deployment.
const json=(data,status=200,origin='')=>new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store',...(origin?{'access-control-allow-origin':origin,'vary':'Origin'}:{})}});
const hash=async value=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))).map(b=>b.toString(16).padStart(2,'0')).join('');
const utcDate=()=>new Date().toISOString();
async function snapshot(env){
 const rows=await env.DB.prepare("SELECT machine,condition_key,vote,result,COUNT(*) AS n FROM reports WHERE status='accepted' GROUP BY machine,condition_key,vote,result").all();
 const timestamp=utcDate();
 await env.DB.batch([
 env.DB.prepare("DELETE FROM aggregate_snapshots"),
 ...rows.results.map(r=>env.DB.prepare("INSERT INTO aggregate_snapshots(machine,condition_key,vote,result,n,generated_at) VALUES(?,?,?,?,?,?)").bind(r.machine,r.condition_key,r.vote,r.result,r.n,timestamp))
 ]);
 return {count:rows.results.length,generatedAt:timestamp};
}
const validString=(v,max=80)=>typeof v==='string'&&v.length>0&&v.length<=max;
const int=(v,min,max)=>Number.isInteger(v)&&v>=min&&v<=max;
function validate(c){return c&&validString(c.machine,100)&&['at','cz','reset','other'].includes(c.origin)&&int(c.games,0,100000)&&
(c.difference===null||(int(c.difference,-100000,100000)&&['daily','section'].includes(c.differenceKind)))&&
(c.cycle===null||int(c.cycle,0,1000))&&(c.points===null||int(c.points,0,100000))&&
['unknown','mode','setting','other'].includes(c.hint)}
function validateReport(result,net){if(!['','big-plus','plus','zero','minus','big-minus'].includes(result))return false;if(net!==null&&!int(net,-100000,100000))return false;if(net!==null&&result==='zero'&&net!==0)return false;if(net!==null&&['plus','big-plus'].includes(result)&&net<=0)return false;if(net!==null&&['minus','big-minus'].includes(result)&&net>=0)return false;return true}
export default {async fetch(request,env){
const origin=request.headers.get('origin')||'';
const allowed=env.ALLOWED_ORIGIN||'';
if(!allowed||!env.DB)return json({error:'service_not_configured'},503);
const url=new URL(request.url),path=url.pathname;
if(request.method==='GET'&&path==='/api/health')return json({ok:true,service:'minna-community-api',databaseBinding:true},200);
if(origin!==allowed)return json({error:'origin_not_allowed'},403);
if(request.method==='OPTIONS')return new Response(null,{status:204,headers:{'access-control-allow-origin':origin,'access-control-allow-methods':'GET,POST,PATCH,DELETE,OPTIONS','access-control-allow-headers':'content-type,authorization','access-control-max-age':'600','vary':'Origin'}});

if(request.method==='GET'&&path==='/api/analysis'){
 const machine=url.searchParams.get('machine');
 if(!validString(machine,100))return json({error:'invalid_machine'},400,origin);
 return json({machine,available:false,rating:null,expectedMedals:null,medianMedals:null,source:null,analysisVersion:null,reason:'verified_condition_specific_analysis_not_loaded'},200,origin);
}
if(request.method==='GET'&&path==='/api/summary'){
const machine=url.searchParams.get('machine');if(!validString(machine,100))return json({error:'invalid_machine'},400,origin);
const rows=await env.DB.prepare("SELECT condition_key,vote,result,n,generated_at FROM aggregate_snapshots WHERE machine=?").bind(machine).all();
return json({machine,groups:rows.results,updatedAt:rows.results[0]?.generated_at??null,note:'投稿の判断割合であり、期待値や勝率ではありません。集計はJST 10/16/22時に更新します'},200,origin)}
if(!['GET','POST','PATCH','DELETE'].includes(request.method))return json({error:'not_found'},404,origin);
const token=(request.headers.get('authorization')||'').replace(/^Bearer /,'');
if(!/^[a-f0-9]{64}$/.test(token))return json({error:'invalid_edit_token'},401,origin);
const tokenHash=await hash(token);
if(request.method==='POST'&&path==='/api/reports'){
let body;try{if(Number(request.headers.get('content-length')||0)>12000)return json({error:'too_large'},413,origin);body=await request.json()}catch{return json({error:'invalid_json'},400,origin)}
if(!validate(body?.condition)||!['play','skip'].includes(body.vote))return json({error:'invalid_input'},400,origin);
const recent=await env.DB.prepare("SELECT COUNT(*) n FROM reports WHERE owner_hash=? AND created_at>datetime('now','-1 hour')").bind(tokenHash).first();
if(recent.n>=3)return json({error:'rate_limited'},429,origin);
const c=body.condition,conditionKey=await hash(JSON.stringify([c.machine,c.origin,c.games,c.difference,c.differenceKind,c.cycle,c.points,c.hint]));
const duplicate=await env.DB.prepare("SELECT id FROM reports WHERE owner_hash=? AND condition_key=? AND status='accepted'").bind(tokenHash,conditionKey).first();
if(duplicate)return json({error:'already_submitted',id:duplicate.id},409,origin);
const id=crypto.randomUUID();
const burst=await env.DB.prepare("SELECT COUNT(*) n FROM reports WHERE condition_key=? AND vote=? AND created_at>datetime('now','-10 minutes')").bind(conditionKey,body.vote).first();
const status=burst.n>=12?'quarantined':'accepted';
await env.DB.prepare("INSERT INTO reports(id,owner_hash,machine,condition_key,condition_json,vote,analysis_json,status) VALUES(?,?,?,?,?,?,?,?)").bind(id,tokenHash,c.machine,conditionKey,JSON.stringify(c),body.vote,JSON.stringify({rating:null,expectedMedals:null,median:null,version:null}),status).run();
if(status==='quarantined')await env.DB.prepare("INSERT INTO moderation_events(report_id,reason,previous_status,new_status) VALUES(?,?,?,?)").bind(id,'identical_condition_vote_burst','new','quarantined').run();
return json({id,status},201,origin)}
const match=path.match(/^\/api\/reports\/([a-f0-9-]{36})$/);if(!match)return json({error:'not_found'},404,origin);
const row=await env.DB.prepare('SELECT * FROM reports WHERE id=? AND owner_hash=?').bind(match[1],tokenHash).first();
if(!row)return json({error:'not_found'},404,origin);
if(request.method==='GET')return json({id:row.id,condition:JSON.parse(row.condition_json),vote:row.vote,result:row.result,net:row.net,status:row.status,updatedAt:row.updated_at},200,origin);
if(request.method==='DELETE'){await env.DB.prepare("UPDATE reports SET status='withdrawn',updated_at=CURRENT_TIMESTAMP WHERE id=?").bind(row.id).run();return json({id:row.id,status:'withdrawn'},200,origin)}
let body;try{body=await request.json()}catch{return json({error:'invalid_json'},400,origin)}
if(row.status==='withdrawn')return json({error:'withdrawn'},409,origin);
const c=body?.condition??JSON.parse(row.condition_json);
const vote=body?.vote??row.vote;
if(!validate(c)||!['play','skip'].includes(vote))return json({error:'invalid_input'},400,origin);
const conditionKey=await hash(JSON.stringify([c.machine,c.origin,c.games,c.difference,c.differenceKind,c.cycle,c.points,c.hint]));
const result=body?.result??row.result,net=body?.net===undefined?row.net:body.net;if(!validateReport(result,net))return json({error:'invalid_result'},400,origin);
const previous=await env.DB.prepare('SELECT COUNT(*) n FROM revisions WHERE report_id=?').bind(row.id).first();
if(previous.n>=20)return json({error:'edit_limit'},429,origin);
await env.DB.batch([
env.DB.prepare('INSERT INTO revisions(report_id,previous_json) VALUES(?,?)').bind(row.id,JSON.stringify({condition:JSON.parse(row.condition_json),vote:row.vote,result:row.result,net:row.net,updated_at:row.updated_at})),
env.DB.prepare("UPDATE reports SET machine=?,condition_key=?,condition_json=?,vote=?,result=?,net=?,updated_at=CURRENT_TIMESTAMP WHERE id=?").bind(c.machine,conditionKey,JSON.stringify(c),vote,result,net,row.id)
]);return json({id:row.id,status:row.status},200,origin)
},async scheduled(event,env){if(!env.DB)return;await snapshot(env)}
};
