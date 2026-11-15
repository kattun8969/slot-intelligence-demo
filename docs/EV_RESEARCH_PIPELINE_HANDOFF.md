# 独自期待値：共通処理パイプライン v0.1

## 変更範囲
- `scripts/ev_research_pipeline.py`（新規）
- `tests/test_ev_research_pipeline.py`（新規）
- 本書 `docs/EV_RESEARCH_PIPELINE_HANDOFF.md`（新規）

**機種ページ、公開期待値、既存データ、GitHub Pages、他チャットのPRは変更しない。**

## データの流れ
```
店舗・提供元からの観測データ
  → 提供元別正規化（PR #33）
  → 不明マッピングを隔離
  → 台番号・型式・時刻順のイベント監査（PR #34）
  → 監査レポート（期待値は作らない）

別途、実際の着席条件・投資・回収・終了が記録された実戦エピソード
  → 完結性・重複・根拠検証（PR #32）
  → 研究用平均純収支・標準誤差・信頼区間
  → 公開判断は保留
```

## インターフェース
`run_pipeline(raw_observations, normalize=..., audit=..., episodes=..., summarize=...)`

- `normalize` は店舗ごとのマッピング規則を適用した辞書を返す関数。原文の意味が未確認なら `review_status=unmapped`。
- `audit` は時系列監査を行う関数。監査通過でも `ev_ready=false`。
- `episodes` は**観測イベントから自動生成しない**。実際の投資・回収がある独立記録を入力する。
- `summarize` は独立した研究用計算器。公開可の出力は受け付けず、`publication_status=research_only` を強制する。

## PRの統合手順
1. PR #32、#33、#34 のテストとレビューを実施する。
2. 正規化結果に `machine_number`、`observed_at`、`event_order` を保持するアダプターを追加する。元のカウンター値は `original_value` として維持。
3. `normalize=lambda raw: {**normalize(raw, rules).to_dict(), ...}` として注入する。イベント監査器は `audit_event_stream` を指定。
4. `summarize=summarize_episodes` は**別途記録した完結実戦**がある場合だけ指定する。
5. 実店舗の許諾とデータカウンター定義が確認されるまで、すべての出力は研究専用。

## 現状
機種依存なし。実店舗の収集データ0件、独自期待値表0件。サンプル数・比較値は存在しない。別チャットによる機種ページ組み込みは不要。
