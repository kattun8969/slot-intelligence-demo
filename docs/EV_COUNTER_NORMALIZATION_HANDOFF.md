# 店舗データカウンター正規化仕様 v0.1

このPRは独自期待値の**データ取り込み前の意味づけ**だけを実装します。サイトの機種ページ・公開期待値・既存の収集ワークフローは変更しません。

## 対応範囲
- 店舗ID・提供元ID・機種ID・型式・有効日付・表示カウンター名・表示イベント名をキーに、**確認済みのルール**だけ適用。
- `at_games`、`cz_games`、`bonus_games`、`cycle_number`、`cycle_games`、`screen_points`、`daily_difference_medals`、`section_difference_medals` を区別。
- カウンター起点（前回AT/CZ/ボーナス終了、開店時、周期開始、有利区間開始）を別項目で記録。
- 元のラベル・元の値・適用ルールIDと版・根拠URLを残す。
- 同じ条件に複数の確認済みルールが適用される場合は `ambiguous` とし、最新ルールを勝手に採用しない。
- 未確認の店舗や型式、規則の適用期間外は `unmapped` とし、内部状態の推測を行わない。
- 単発・駆け抜け・リセットなどの**表示イベント**は確定内部状態と別扱い。確認済みラベルでも `state=unverified` とする。

## ファイル
- `scripts/ev_counter_normalizer.py`：共通正規化ロジック
- `data/ev/counter-rules.json`：ルール台帳。初期状態は0件（根拠のないマッピングを登録しない）
- `tests/test_ev_counter_normalizer.py`：店舗・型式・日付の混同、曖昧ルール、未検証状態のテスト

## 使用方法
```python
from pathlib import Path
from scripts.ev_counter_normalizer import load_rules, normalize
rules = load_rules(Path("data/ev/counter-rules.json"))
observation = {
    "source_id": "example", "venue_id": "venue-01",
    "machine_id": "ggo", "model_revision": "rev-A",
    "observed_date": "2026-11-15",
    "counter_label": "現在G", "event_label": "大当り",
    "counter_value": 350, "evidence_url": "https://example.org/record",
}
print(normalize(observation, rules).to_dict())
# 未登録なら review_status='unmapped', counter_type='unknown'
```

## 次の段階への引き継ぎ
機種ページ担当に渡す数値は**まだありません**。公開サイトへの組み込みは不要です。今後、提供元の仕様を確認してルールを登録し、監査済みの観測記録から実戦エピソードを作成する段階へ進めます。PR #32の研究用期待値エンジンとは独立しており、双方がレビュー後に合流できる構造です。

現時点の対応機種は**特定機種なし（共通形式のみ）**、実店舗の確認済みルール0件、実測期待値0件です。
