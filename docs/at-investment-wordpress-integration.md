# AT投資目安｜WordPress共通プラグインの導入

適用先：kajiplus.infoの機種ページ。公開判断とプラグインの導入は②Workのみ。旧GitHub Pagesに触れない。

## 配布するファイル
- wordpress-plugin/minna-at-investment/minna-at-investment.php（WPプラグイン）
- wordpress-plugin/minna-at-investment/assets/at-investment-core.js（共通計算）
- wordpress-plugin/minna-at-investment/assets/investment-widget.js（汎用UI）
- wordpress-plugin/minna-at-investment/assets/investment.css（320/375px対応）

## ②Workの実装手順
1. WordPressの公開機種ページをバックアップ。リコリコの期待値/PAPIMO/投票/示唆/狙い目は改変しない。
2. 上記のフォルダを同名でZIP化してプラグイン管理画面から導入（またはwp-content/plugins/minna-at-investment内に配置）して有効化。
3. リコリコの #ly-calculator を検出し、フォームの既存入力（#ly-scenario / #ly-current / 貸出率）に連動して「平均投資・80%到達目安」を挿入する。計算用ソースがない時は「確認中」を表示する。これが初期状態。
4. 数値の根拠が揃ったら機種の投稿編集画面に表示される「AT投資目安：検証済みJSON」メタボックスへレビュー済みJSONを登録。モデルは対象機種のシナリオ/カウンター/起点/ATまでの残りゲーム数分布、50枚回転率、1時間実消化数、出典URL、確認日、実測/推定を含む。
5. WordPress本番の機種ページで入力・レート切替・出典リンク・320pxと375px表示を確認。従来の期待収支・PAPIMO・投票が保持されることを確認。異常があればプラグインを無効化（本文は無変更）。
6. 新規機種は期待値フォームの親要素に data-minna-ev-tool と data-minna-scenario-selector="#scenario-id" / data-minna-current-selector="#current-id" を指定する。1000円あたり貸出枚数の入力/セレクトに data-minna-loan-coins を指定すると共通UIを自動接続できる。リコリコは専用セレクタを標準認識する。
7. PR #306の先行リコリコ専用JSを同時に読み込まない（二重表示防止）。

## 入力JSONの構造（ダミー値。本番へ転記禁止）
    {
      "approved": true,
      "scenarios": {
        "0": {
          "startingState": "lower AT ended",
          "endpoint": "first AT",
          "counter": "data-counter G",
          "method": "measured",
          "sourceUrl": "https://example.org/reference",
          "checkedOn": "2026-11-27",
          "coinBasePer50": 35,
          "spinsPerHour": 700,
          "byCurrentG": {"300": [[100,0.2],[200,0.5],[300,0.3]]},
          "notes": "data conditions and sample"
        }
      }
    }

このJSON中のゲーム数、確率、回転率、速度は**架空のテスト数値**。実機データと認めず公開計算には使わない。現在Gごとの条件付きAT到達分布（残G、確率、昇順、合計1）を収集しない限り数値を表示しない。期待収支・天井値を投資額へ逆算しない。

平均G = 確率で重み付けした残Gの平均。80%点 = 累積当選確率0.8に到達する最初の残G。投入相当枚数 = 残G×50÷50枚あたり回転数。投入相当円 = 枚数×1000÷1000円の貸出枚数。時間 = 残G×60÷実消化G/時。

途中払出・持ちメダル・再プレイ等を反映した現金準備額ではなく、80%点も勝率ではない。グラフから分布を外挿しない。未検証は表示しないか「確認中」。

## 検証範囲
空欄、0/300G、範囲外、AT/CZ/ゾーン、46/50・50/50・カスタム貸出、出典URL、データ欠損、分布不正、320/375pxの改行、二重読込、既存機能保持を検証する。②の公開確認前に実装済みと報告しない。
