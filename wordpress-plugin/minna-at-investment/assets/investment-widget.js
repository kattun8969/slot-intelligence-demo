/* WordPress front-end adapter. ① submits model data; ② reviews and activates.
 * Targets Lycoris existing form or future data-minna-ev-tool forms. */
(function () {
  "use strict";
  function selectInside(root, selector) {
    try { return selector ? root.querySelector(selector) : null; } catch (_) { return null; }
  }
  function loanCoins(root) {
    const explicit = selectInside(root, "[data-minna-loan-coins]");
    if (explicit) {
      const n = Number(explicit.value);
      return Number.isFinite(n) && n > 0 ? n : null;
    }
    const selects = Array.from(root.querySelectorAll("select"));
    const rate = selects.find(el => Array.from(el.options || []).some(o => o.value === "50/50"));
    if (!rate) return null;
    if (rate.value === "custom") {
      const custom = selectInside(root, ".ly-custom input[type='number']");
      const n = custom ? Number(custom.value) : NaN;
      return Number.isFinite(n) && n > 0 ? n : null;
    }
    const n = Number(String(rate.value).split("/")[0]);
    return Number.isFinite(n) && n > 0 ? n : null;
  }
  const format = (value, unit) => Math.ceil(value).toLocaleString("ja-JP") + unit;
  function makeText(tag, value, className) {
    const el = document.createElement(tag);
    el.textContent = value;
    if (className) el.className = className;
    return el;
  }
  function init(root, config) {
    if (root.querySelector(".minna-at-investment, #ly-investment-estimate")) return;
    const scenario = selectInside(root, root.dataset.minnaScenarioSelector || "#ly-scenario");
    const current = selectInside(root, root.dataset.minnaCurrentSelector || "#ly-current");
    if (!scenario || !current) return;
    const section = document.createElement("section");
    section.className = "minna-at-investment";
    section.setAttribute("aria-label", "ATまでの投入相当額と所要時間");
    section.appendChild(makeText("strong", "ATまでの平均投資・80%到達目安"));
    const output = makeText("div", "投資目安データ確認中", "minna-at-investment__body");
    output.setAttribute("role", "status");
    output.setAttribute("aria-live", "polite");
    section.appendChild(output);
    section.appendChild(makeText("small",
      "期待収支とは別の指標です。80%到達予算はAT到達ゲーム数の分布に基づく投入相当額です。勝率・利益確率や、途中の払出・持ちメダル・再プレイを反映した現金準備額を表すものではありません。",
      "minna-at-investment__note"));
    const details = root.querySelector("details");
    if (details) root.insertBefore(section, details);
    else root.appendChild(section);
    const scenarios = config && config.approved === true && config.scenarios ? config.scenarios : {};
    function update() {
      output.replaceChildren();
      const id = String(scenario.value);
      const model = Object.prototype.hasOwnProperty.call(scenarios, id) ? scenarios[id] : null;
      const isLycoris = root.id === "ly-calculator";
      const option = scenario.selectedOptions?.[0];
      const counter = isLycoris ? "data-counter G" : root.dataset.minnaCounter;
      const endpoint = option?.dataset.minnaEndpoint || root.dataset.minnaEndpoint;
      if ((isLycoris && (!["0", "1", "2"].includes(id) || !option?.textContent.includes("／ATまで"))) ||
          (endpoint && endpoint !== "first AT") || (model && model.endpoint !== "first AT")) {
        output.textContent = "この条件はAT初当たりまでの投資目安の対象外です。";
        return;
      }
      if (!model || !model.byCurrentG ||
          !["measured", "estimated"].includes(model.method) ||
          typeof model.sourceUrl !== "string" || !/^https:\/\//.test(model.sourceUrl) ||
          !/^20\d\d-\d\d-\d\d$/.test(model.checkedOn || "") ||
          typeof model.counter !== "string" || !model.counter.trim() || (counter && model.counter !== counter) ||
          typeof model.startingState !== "string" || !model.startingState.trim()) {
        output.textContent = "投資目安データ確認中";
        return;
      }
      const g = Number(current.value);
      if (current.value === "" || !Number.isSafeInteger(g) || g < 0) {
        output.textContent = "現在のゲーム数を入力してください。";
        return;
      }
      const dist = Object.prototype.hasOwnProperty.call(model.byCurrentG, String(g)) ? model.byCurrentG[String(g)] : null;
      const result = window.MinnaAtInvestment && window.MinnaAtInvestment.estimate({
        endpoint: model.endpoint, distribution: dist, coinBasePer50: model.coinBasePer50,
        spinsPerHour: model.spinsPerHour, loanCoinsPer1000: loanCoins(root)
      });
      if (!result) { output.textContent = "この状態・現在G数の投資目安は確認中です。"; return; }
      const grid = document.createElement("div");
      grid.className = "minna-at-investment__grid";
      [
        ["平均投入枚数",format(result.average.inputCoins,"枚")],
        ["平均投入相当額",format(result.average.equivalentYen,"円")],
        ["平均所要時間",format(result.average.minutes,"分")],
        ["80%到達時点の投入枚数",format(result.p80.inputCoins,"枚")],
        ["80%到達時点の投入相当額",format(result.p80.equivalentYen,"円")],
        ["80%到達時点の時間",format(result.p80.minutes,"分")]
      ].forEach(([label,value]) => {
        const cell = document.createElement("div");
        cell.className = "minna-at-investment__cell";
        cell.appendChild(makeText("small",label));
        cell.appendChild(makeText("b",value));
        grid.appendChild(cell);
      });
      output.appendChild(grid);
      output.appendChild(makeText("small",
        "平均残り"+format(result.average.remainingG,"G")+"／80%点"+format(result.p80.remainingG,"G")+
        "・"+(model.method==="measured"?"実測":"推定")+"／確認日："+model.checkedOn+
        "。80%はAT到達ゲーム数の分位点であり勝率ではありません。",
        "minna-at-investment__note"));
      const link = document.createElement("a");
      link.href = model.sourceUrl; link.target = "_blank"; link.rel = "noopener noreferrer";
      link.textContent = "投資目安の出典・算出条件";
      output.appendChild(link);
    }
    root.addEventListener("input", update);
    root.addEventListener("change", update);
    update();
  }
  function start() {
    const config = window.MINNA_AT_INVESTMENT_CONFIG || {approved:false,scenarios:{}};
    document.querySelectorAll("#ly-calculator, [data-minna-ev-tool]").forEach(el => init(el,config));
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
