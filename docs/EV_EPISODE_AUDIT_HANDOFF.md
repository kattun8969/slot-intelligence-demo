# 独自期待値：時系列イベント監査 v0.1

## 対象と分離
独自期待値エンジンの前処理。機種ページ、公開期待値、狙い目、公開サイト、既存PRには変更を加えない。

## 新規ファイル
- `scripts/ev_episode_audit.py`: イベント順序、重複、カウンターの減少、状態不明、左右打ち切り、24時間超の観測空白、日跨ぎを検出。
- `tests/test_ev_episode_audit.py`: 架空データによる回帰テスト。

## 入力
1件ごとに `source_id`, `venue_id`, `machine_id`, `model_revision`, `machine_number`, `observed_at` (タイムゾーン付き), `event_order`, `event_type`, `counter_type`, `counter_value`, `counter_origin`, `review_status`, `source_url` を記録。

`event_type` は `at_start`、`at_end`、`cz_start`、`cz_end`、`bonus`、`single_hit_claim`、`runthrough_claim`、`reset_claim`、`display_difference`、`unknown` を区別する。店舗の表示をそのまま「駆け抜け確定」に変換しない。

## 出力
`audit_event_stream(records)` は店舗・機種・型式・台番号別に時系列を監査し、`flags` に不明点を列挙する。全グループ `ev_ready=false` として返す。

**注意**：イベントの始端がAT開始、終端がAT終了でも、プレイヤーがどのG数で打ち始めたか、投資・獲得額、設定、当日の欠損は確定しない。イベント監査を通過しただけで実戦期待値に転用しない。

### 現在の未実装事項
- AT/CZ間のカウンター起点を、機種ごとの実機仕様で検証したイベント再構成
- 店舗の営業日と時刻の照合、データカウンターがボーナスでリセットされる仕様の反映
- 有利区間切断・上位AT・引き戻しなどの確定状態の根拠収集
- 投資・回収と着席時点が分かる実戦データの取得
- 期待値表の推定と公開期待値との条件一致比較

## 引き継ぎ
現時点では機種IDを固定せず全機種共通の監査器を用意した段階。独自期待値表は未生成、実データ0件、公開サイトへの反映不要。PR #32（研究用収支集計）、PR #33（カウンター正規化）と競合しない新規ファイルだけを追加。
