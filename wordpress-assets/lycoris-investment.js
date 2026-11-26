/* Lycoris Recoil investment estimate add-on. Does not modify the existing EV tool.
   Data must be reviewed and provided separately by editor.
   No AT arrival distribution => no investment numbers. */
(() => {
  "use strict";
  const root = document.getElementById("ly-calculator");
  if (!root || document.getElementById("ly-investment-estimate")) return;
  const scenario = root.querySelector("#ly-scenario");
  const current = root.querySelector("#ly-current");
  if (!scenario || !current) return;

  const section = document.createElement("section");
  section.id = "ly-investment-estimate";
  section.setAttribute("aria-label", "ATまでの投資と所要時間");
  section.style.cssText = "margin:10px 0;padding:12px;border:1px solid #dbe5e9;background:#fff;border-radius:8px;color:#15334c";
  section.innerHTML = '<strong>ATまでの平均投資・80%到達目安</strong><div id="ly-investment-body" role="status" aria-live="polite" style="font-size:14px;line-height:1.7;margin-top:8px"></div><small style="display:block;margin-top:8px;color:#546575">期待収支と投入相当額は異なります。実際の現金投資は途中の払出・持ちメダル等で変動します。</small>';
  const details = root.querySelector("details");
  if (details) root.insertBefore(section, details);
  else root.appendChild(section);
  const output = section.querySelector("#ly-investment-body");
  const models = window.MINNA_LY_INVESTMENT_MODELS || {};
  const safe = str => String(str).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const fmt = (n, unit) => Math.ceil(n).toLocaleString("ja-JP") + unit;
  function validDistribution(dist) {
    if (!Array.isArray(dist) || dist.length === 0) return false;
    let total = 0, previous = -1;
    for (const pair of dist) {
      if (!Array.isArray(pair) || pair.length !== 2) return false;
      const [g,p] = pair;
      if (!(Number.isFinite(g) && Number.isInteger(g) && g>=0 && g>previous && Number.isFinite(p) && p>0 && p<=1)) return false;
      previous=g; total+=p;
    }
    return Math.abs(total-1)<0.00001;
  }
  function loanCoins() {
    const select = Array.from(root.querySelectorAll("select")).find(el => el !== scenario && Array.from(el.options).some(o => o.value === "50/50"));
    if (!select) return null;
    if (select.value === "custom") {
      const first = root.querySelector(".ly-custom input[type=number]");
      const n = Number(first && first.value);
      return Number.isFinite(n) && n>0 ? n : null;
    }
    const n = Number(select.value.split("/")[0]);
    return Number.isFinite(n) && n>0 ? n : null;
  }
  function show() {
    if (!["0","1","2"].includes(scenario.value)) {
      output.textContent = "CZまで・ゾーン終了までの条件はAT到達投資の対象外です。"; return;
    }
    const g = Number(current.value);
    if (current.value === "" || !Number.isInteger(g) || g<0) {
      output.textContent = "現在のデータカウンターG数を入力してください。"; return;
    }
    const m = models[scenario.value];
    const dist = m && m.byCurrentG && m.byCurrentG[String(g)];
    if (!m || m.endpoint!=="first AT" || m.counter!=="data-counter G" ||
        !["measured","estimated"].includes(m.method) ||
        !/^https:\/\//.test(m.sourceUrl || "") ||
        !/^\d{4}-\d{2}-\d{2}$/.test(m.checkedOn || "") ||
        !Number.isFinite(m.coinBasePer50) || m.coinBasePer50<=0 ||
        !Number.isFinite(m.spinsPerHour) || m.spinsPerHour<=0 ||
        !validDistribution(dist)) {
      output.textContent = "この台状態・現在G数のAT到達分布は未検証です。金額や時間を推測表示しません。"; return;
    }
    const averageG = dist.reduce((sum,[x,p])=>sum+x*p,0);
    let cumulative=0, q80=null;
    for (const [x,p] of dist) { cumulative+=p; if (cumulative>=0.8-1e-10) { q80=x; break; } }
    if (q80 === null) { output.textContent = "分布データを確認してください。"; return; }
    const meanCoins = averageG * 50 / m.coinBasePer50;
    const p80Coins = q80 * 50 / m.coinBasePer50;
    const loan = loanCoins();
    const money = n => loan ? fmt(n*1000/loan,"円") : "貸出枚数の設定が必要";
    const cells = [
      ["平均投入枚数",fmt(meanCoins,"枚")],
      ["平均投入相当額",money(meanCoins)],
      ["平均所要時間",fmt(averageG*60/m.spinsPerHour,"分")],
      ["80%到達時点の投入相当枚数",fmt(p80Coins,"枚")],
      ["80%到達時点の投入相当額",money(p80Coins)],
      ["80%到達時点の所要時間",fmt(q80*60/m.spinsPerHour,"分")]
    ];
    output.innerHTML = '<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px">' +
      cells.map(([a,b])=>'<div style="min-width:0;border:1px solid #e2e8ef;border-radius:6px;padding:7px"><small>'+safe(a)+'</small><div style="font-weight:700;overflow-wrap:anywhere">'+safe(b)+'</div></div>').join("") + '</div>' +
      '<small>残り平均'+fmt(averageG,"G")+'／80%点'+fmt(q80,"G")+'・'+(m.method==="measured"?"実測":"推定")+'／確認日'+safe(m.checkedOn)+'。80%はAT到達ゲーム数の分位点であり、勝率・利益確率ではありません。</small>' +
      '<div><a target="_blank" rel="noopener noreferrer" href="'+safe(m.sourceUrl)+'">算出根拠と条件</a></div>';
  }
  root.addEventListener("input",show);
  root.addEventListener("change",show);
  show();
})();