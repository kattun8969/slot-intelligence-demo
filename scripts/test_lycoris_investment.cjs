// Standalone DOM-lite regression checks. Run: node scripts/test_lycoris_investment.cjs
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('wordpress-assets/lycoris-investment.js','utf8');
function run(state='0',g='300',models={}) {
  const events={};const body={textContent:'',innerHTML:''};
  const scenario={value:state,options:[]},current={value:g},loan={value:'46/50',options:[{value:'50/50'},{value:'46/50'}]};
  const root={
    querySelector(q){return {'#ly-scenario':scenario,'#ly-current':current,'details':null}[q]||null;},
    querySelectorAll(q){return q==='select'?[scenario,loan]:[];},
    appendChild(el){this.child=el;},addEventListener(k,fn){events[k]=fn;}
  };
  const document={getElementById(id){return id==='ly-calculator'?root:null;},
    createElement(){return {setAttribute(){},style:{},
      set innerHTML(value){this.html=value;},
      querySelector(q){return q==='#ly-investment-body'?body:null;}
    };}};
  vm.runInNewContext(src,{document,window:{MINNA_LY_INVESTMENT_MODELS:models}});
  return {body,events,scenario,current,loan};
}
const source={sourceUrl:'https://example.org/reference',checkedOn:'2026-11-27',counter:'data-counter G',endpoint:'first AT',method:'measured',coinBasePer50:35,spinsPerHour:700,byCurrentG:{'300':[[100,.2],[200,.5],[300,.3]]}};
assert.match(run().body.textContent,/未検証/);
const ok=run('0','300',{'0':source});
assert.match(ok.body.innerHTML,/平均投入相当額/);
assert.match(ok.body.innerHTML,/80%到達時点/);
assert.match(ok.body.innerHTML,/300G/);
ok.scenario.value='3';ok.events.change();assert.match(ok.body.textContent,/対象外/);
assert.match(run('0','300',{'0':{...source,byCurrentG:{'300':[[100,.2],[300,.2]]}}}).body.textContent,/未検証/);
assert.match(run('0','301',{'0':source}).body.textContent,/未検証/);
console.log('Lycoris investment add-on offline tests passed');
