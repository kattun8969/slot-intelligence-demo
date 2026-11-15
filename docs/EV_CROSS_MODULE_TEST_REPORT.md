# 独自期待値：複数モジュール実接続テスト記録（2026-11-15）

## GitHub Actions
- 検証用PR #43（**マージ禁止**）
- 成功run: https://github.com/kattun8969/slot-intelligence-demo/actions/runs/43671216942
- テストファイル9件、テストケース57件、失敗0件
- 追加テスト: `tests/test_ev_cross_module_integration.py`

## 実際に接続した経路
1. `ev_counter_normalizer.normalize` → `ev_contract_adapters.observation_to_audit` → `ev_episode_audit.audit_event_stream` → `ev_research_pipeline.run_pipeline`
2. `ev_engine_core.summarize_episodes` → `ev_contract_adapters.estimate_to_comparison` → `ev_reference_compare.compare_exact`
3. 同じ架空の完結実戦データを `ev_holdout_validation.validate_holdout` に渡し、期間別の平均収支を確認

## 注意点
- データはすべてテスト用の架空レコード。公開期待値や実測収支の実データは含まない。
- 店舗イベント履歴だけでは完結実戦収支を復元せず、期待値算出に進めない。
- 初回run 43671177947 はホールドアウト用の架空レコードに `counter_origin` がなく失敗。テスト入力を修正したrun 43671216942で全件成功。
- この検証はユニットテストと限定的な複数モジュール連携テスト。データ利用許諾、統計的妥当性、外部ソースとの一致、サイト表示、全データ経路の本番E2Eを保証しない。
- PR #43はマージ禁止。統合テストを本体へ移す際は、個別PRを安全に統合した後に取り込む。
