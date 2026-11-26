const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx={};vm.runInNewContext(fs.readFileSync('wordpress-assets/at-investment-core.js','utf8'),ctx);
const e=ctx.MinnaAtInvestment.estimate;
const data={endpoint:'first AT',distribution:[[100,0.2],[200,0.5],[300,0.3]],coinBasePer50:35,spinsPerHour:700,loanCoinsPer1000:46};
const ok=e(data);
assert.ok(ok);assert.equal(ok.average.remainingG,210);assert.equal(ok.p80.remainingG,300);
assert.ok(Math.abs(ok.average.inputCoins-300)<1e-7);
assert.equal(e({...data,endpoint:'first CZ'}),null);
assert.equal(e({...data,distribution:[[100,0.2],[300,0.2]]}),null);
assert.equal(e({...data,coinBasePer50:0}),null);
assert.equal(e({...data,distribution:[[300,0.3],[100,0.7]]}),null);
console.log('AT investment core tests passed');
const ceiling = ctx.MinnaAtInvestment.estimateCeiling;
const budget = ctx.MinnaAtInvestment.assessBudget;
const terms = {currentG:650,ceilingG:1000,coinBasePer50:31.8,spinsPerHour:800,loanCoinsPer1000:50};
const max = ceiling(terms);
assert.equal(max.remainingG,350);
assert.equal(Math.ceil(max.inputCoins),551);
assert.equal(max.minutes,26.25);
assert.equal(ceiling({...terms,currentG:1000}),null);
assert.equal(ceiling({...terms,loanCoinsPer1000:null}).equivalentYen,null);
for (const [cash,coins,yen,medals] of [[0,0,12000,551],[10000,0,2000,51],[10000,100,0,0],[10500,0,1500,51],[0,551,0,0]]) {
  const r=budget(max.inputCoins,coins,cash,50);
  assert.equal(r.extraYen,yen);
  assert.equal(r.missingCoins,medals);
}
console.log('Ceiling and available-budget tests passed');
