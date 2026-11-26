/* Shared AT arrival investment math for WordPress machine pages.
   No DOM access, no defaults for missing probabilities or rates. */
(function(root) {
  "use strict";
  function estimate(input) {
    if (!input || input.endpoint !== "first AT") return null;
    const {distribution, coinBasePer50, spinsPerHour, loanCoinsPer1000} = input;
    if (![coinBasePer50,spinsPerHour,loanCoinsPer1000].every(x=>Number.isFinite(x)&&x>0)) return null;
    if (!Array.isArray(distribution) || !distribution.length) return null;
    let sum=0,prior=-1;
    for(const pair of distribution) {
      if (!Array.isArray(pair) || pair.length!==2) return null;
      const [g,p]=pair;
      if (!Number.isSafeInteger(g) || g<=prior || g<0 || !Number.isFinite(p) || p<=0 || p>1) return null;
      prior=g;sum+=p;
    }
    if (Math.abs(sum-1)>1e-6) return null;
    const averageG = distribution.reduce((a,[g,p])=>a+g*p,0);
    let running=0, p80G=null;
    for(const [g,p] of distribution) {
      running+=p;
      if(running >= 0.8-1e-10){p80G=g;break;}
    }
    if(p80G===null) return null;
    const amounts=(g)=>({
      remainingG:g,
      inputCoins:g*50/coinBasePer50,
      equivalentYen:g*50/coinBasePer50*1000/loanCoinsPer1000,
      minutes:g*60/spinsPerHour
    });
    return {average:amounts(averageG),p80:amounts(p80G),
      caveat:"投入相当額であり、途中の払出・持ちメダル・再プレイ等を反映した現金準備額ではありません。"};
  }
  root.MinnaAtInvestment = Object.freeze({estimate});
})(typeof window!=="undefined" ? window : globalThis);
