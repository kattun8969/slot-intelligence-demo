/* Ceiling budget adapter for WordPress machine pages. */
(function () {
  "use strict";
  const endpoints = new Map([
    ["first AT", "AT"], ["first bonus", "ボーナス"], ["first ST", "ST"], ["first CZ", "CZ"]
  ]);

  function selectInside(root, selector) {
    try { return selector ? root.querySelector(selector) : null; } catch (_) { return null; }
  }

  function loanCoins(root) {
    const explicit = root.querySelector("[data-minna-loan-coins]");
    if (explicit) return Number(explicit.value);
    const select = Array.from(root.querySelectorAll("select")).find(el =>
      Array.from(el.options).some(option => option.value === "50/50"));
    if (!select) return null;
    if (select.value === "custom") return root.querySelector(".ly-custom input[type=number]")?.valueAsNumber;
    return Number(select.value.split("/")[0]);
  }

  const format = (value, unit) => Math.ceil(value).toLocaleString("ja-JP") + unit;
  function makeText(tag, value, className) {
    const el = document.createElement(tag);
    el.textContent = value;
    if (className) el.className = className;
    return el;
  }

  function init(root, scenarios) {
    if (root.querySelector(".minna-at-investment, #ly-investment-estimate")) return;
    const isLycoris = root.id === "ly-calculator";
    const scenario = selectInside(root, root.dataset.minnaScenarioSelector || "#ly-scenario");
    const current = selectInside(root, root.dataset.minnaCurrentSelector || "#ly-current");
    if (!scenario || !current) return;

    const section = document.createElement("section");
    section.className = "minna-at-investment";
    const heading = makeText("strong", "天井までの投資・時間の目安");
    const output = makeText("div", "", "minna-at-investment__body");
    output.setAttribute("role", "status");
    const budget = document.createElement("details");
    budget.className = "minna-at-investment__budget";
    budget.appendChild(makeText("summary", "手持ち資金で足りるか確認"));
    function budgetField(labelText) {
      const label = makeText("label", labelText);
      const field = document.createElement("input");
      field.type = "number";
      field.inputMode = "numeric";
      field.min = "0";
      field.step = "1";
      label.appendChild(field);
      budget.appendChild(label);
      return field;
    }
    const cash = budgetField("使える現金（円）");
    const coins = budgetField("使えるメダル・再プレイ枚数");
    const budgetResult = makeText("p", "", "minna-at-investment__budget-result");
    budgetResult.setAttribute("role", "status");
    budget.appendChild(budgetResult);
    budget.appendChild(makeText("small", "現金は1,000円単位の貸出で計算。再プレイは店の上限内で今使える枚数を入力してください。", "minna-at-investment__note"));
    section.append(heading, output, budget);
    const details = root.querySelector("details");
    root.insertBefore(section, details);

    function update() {
      output.replaceChildren();
      budget.hidden = true;
      heading.textContent = "天井までの投資・時間の目安";
      const id = scenario.value;
      const model = Object.prototype.hasOwnProperty.call(scenarios, id) ? scenarios[id] : null;
      const option = scenario.selectedOptions?.[0];
      const endpoint = isLycoris && option?.textContent.includes("／ATまで")
        ? "first AT" : option?.dataset.minnaEndpoint || root.dataset.minnaEndpoint;
      const counter = isLycoris ? "data-counter G" : option?.dataset.minnaCounter || root.dataset.minnaCounter;
      if (!model || !Number.isSafeInteger(model.ceilingG) || !counter || model.counter !== counter ||
          endpoint !== model.endpoint || !endpoints.has(endpoint) || !["verified", "assumed"].includes(model.basis)) {
        output.textContent = "この条件の天井時の投資目安は確認中です。";
        return;
      }

      const target = endpoints.get(endpoint);
      heading.textContent = target + "までの最大投資目安";
      const assumed = model.basis === "assumed";
      const limit = format(model.ceilingG, "G");
      const basis = (assumed ? "想定上限 " : "対象天井 ") + limit +
        (counter === "data-counter G" ? "（データカウンター）" : "");
      if (!Number.isSafeInteger(current.valueAsNumber) || current.valueAsNumber < 0) {
        output.textContent = "現在のゲーム数を入力してください。";
      } else if (current.valueAsNumber >= model.ceilingG) {
        output.textContent = basis + "以上です。台の状態とカウンターを確認してください。";
        return;
      } else {
        const result = window.MinnaAtInvestment?.estimateCeiling({
          currentG: current.valueAsNumber, ceilingG: model.ceilingG,
          coinBasePer50: model.coinBasePer50, spinsPerHour: model.spinsPerHour,
          loanCoinsPer1000: loanCoins(root)
        });
        if (!result) {
          output.textContent = "この条件の天井時の投資目安は確認中です。";
          return;
        }

        const grid = document.createElement("div");
        grid.className = "minna-at-investment__grid";
        [
          ["当たらず天井まで", format(result.remainingG, "G")],
          ["投入相当枚数", "約" + format(result.inputCoins, "枚")],
          ["貸出換算額", result.equivalentYen === null ? "貸出枚数を設定" : "約" + format(result.equivalentYen, "円")],
          ["消化時間", "約" + format(result.minutes, "分")]
        ].forEach(([label, value]) => {
          const cell = document.createElement("div");
          cell.className = "minna-at-investment__cell";
          cell.append(makeText("small", label), makeText("b", value));
          grid.appendChild(cell);
        });
        output.appendChild(grid);

        budget.hidden = false;
        const ready = cash.value !== "" || coins.value !== "";
        const availableYen = cash.value === "" ? 0 : cash.valueAsNumber;
        const availableCoins = coins.value === "" ? 0 : coins.valueAsNumber;
        const assess = window.MinnaAtInvestment.assessBudget;
        if (!ready) {
          budgetResult.textContent = "使える金額や枚数を入力すると、想定天井までに足りるか表示します。";
        } else if (![availableYen, availableCoins].every(n => Number.isSafeInteger(n) && n >= 0) ||
            cash.validity.badInput || coins.validity.badInput) {
          budgetResult.textContent = "現金とメダルは0以上の整数で入力してください。";
        } else if (availableCoins >= Math.ceil(result.inputCoins)) {
          budgetResult.textContent = "想定天井まで、手持ちメダルの範囲内です。";
        } else if (result.equivalentYen === null) {
          budgetResult.textContent = "手持ちメダルだけでは約" +
            format(result.inputCoins - availableCoins, "枚") + "不足。現金も含めるには貸出枚数を設定してください。";
        } else {
          const remaining = assess(result.inputCoins, availableCoins, availableYen, loanCoins(root));
          budgetResult.textContent = remaining.missingCoins > 0
            ? "想定天井まで、あと約" + format(remaining.extraYen, "円") + "、または約" +
              format(remaining.missingCoins, "枚") + "不足する目安です。"
            : "想定天井まで、入力した手持ち資金の範囲内です。";
        }
      }

      output.appendChild(makeText("small",
        basis + "。50枚で" + model.coinBasePer50 + "G、1時間" + model.spinsPerHour +
        "Gで換算。途中の払い出しや前兆などで実際の投資・時間は変わります。" +
        (assumed ? "想定値のため、実際の上限を保証するものではありません。" : ""),
        "minna-at-investment__note"));
    }

    root.addEventListener("input", update);
    root.addEventListener("change", update);
    update();
  }

  function start() {
    const config = window.MINNA_AT_INVESTMENT_CONFIG;
    const scenarios = config?.approved === true ? config.scenarios || {} : {};
    document.querySelectorAll("#ly-calculator, [data-minna-ev-tool]").forEach(root => init(root, scenarios));
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
