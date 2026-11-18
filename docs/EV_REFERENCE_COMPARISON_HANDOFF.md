# 独自期待値と公開期待値の条件一致比較 v0.1

この機能は研究用であり、機種ページや公開サイトを変更しません。

## 追加ファイル
- `scripts/ev_reference_compare.py`: 条件完全一致のみ比較
- `tests/test_ev_reference_compare.py`: 混同防止・出典・サンプル件数のテスト
- `docs/EV_REFERENCE_COMPARISON_HANDOFF.md`: 本書

## 入力と比較の条件
公開値は `provenance=published_reference`、独自の実戦平均は `provenance=observed_episodes` として分離。公開値は出典URL・確認日、実測平均はサンプル件数・`publication_status=research_only` を必須とする。

以下が**すべて一致**する場合だけ比較する。

1. 機種IDと型式
2. AT間・CZ間・周期などのカウンター種別と起点
3. 開始時点のカウンター値
4. 状態（駆け抜け後・通常・設定変更後など）
5. 交換率・貸出条件
6. やめどき・集計終了条件

一致しないものは `unmatched` に理由を残す。公開表の未掲載Gを線形補間したり、違う条件の金額を横流ししたりしない。

## 出力
- `published_ev_yen`: 公開期待値
- `observed_mean_net_yen`: 完結した実戦の平均純収支
- `difference_yen`: 独自平均 − 公開期待値
- `sample_size`、`sample_threshold_met`: 件数と最低件数の充足
- `comparison_status=research_only`: 公開判断は保留

平均差が小さくても、設定配分、稼働者の選択、打ち切り、状態推定の誤りなどが残るため「精度が確認された」とは判断しない。

## 他チャットへの引き継ぎ
**対象機種**：全機種共通の比較ロジック。実データ0件、実比較0件。
**入力**：機種ID、型式、状態、カウンターと起点、交換率、終了条件、出典、件数。
**期待値表**：未生成。現時点では公開機種ページへの組み込み不要。
**他PR**：#32 の研究用期待値計算器の出力に `counter_origin` と `provenance` を付与するアダプターを今後作成。#33 の正規化、#34 の履歴監査、#37 のパイプラインとは独立した新規ファイルのみ。
