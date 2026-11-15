# 店舗観測データCSV取り込み v0.1

## 目的
店舗の履歴・カウンター観測情報を**許諾を確認したCSV**として受け取り、欠損・重複・不正な形式を隔離する。Webスクレイピング、データ取得API呼び出し、公開ページ変更は実施しない。

## CSV必須列
`source_id,venue_id,machine_id,model_revision,machine_number,observed_date,observed_at,event_order,counter_label,event_label,counter_value,evidence_url,source_permission,permission_evidence,source_record_id`

- `observed_at`: `2026-11-15T10:00:00+09:00` のようにタイムゾーン必須。
- `observed_date`: 観測日時の暦日。店舗の**営業日**ではない。営業日変換は別途店舗ルールで扱う。
- `source_record_id`: データ提供元の一意なイベントID。提供元・店舗・IDの重複を隔離。
- `source_permission`: `user_owned`, `permitted_csv`, `official_api`, `manual_public_record` のいずれか。
- `permission_evidence`: データ利用根拠へのHTTPSリンク。入力値があるだけで法的な利用許諾を証明できるわけではない。
- `evidence_url`: 元の観測データの出典。カウンター定義の根拠URLとは区別する。

## 出力
`accepted`（取り込み可能な観測行）と `quarantine`（行番号・隔離理由）を分ける。1行不正でも他の有効行は処理する。最大5MB・2万行。値の推測・補完はしない。

## 制限と次の段階
- 日別差枚が負数となる表示は現在のカウンター非負制約と不整合。差枚用に符号付き値の別ルールを追加するまで隔離。
- 15列はイベント履歴用。実投資・実回収額がないため、期待値は算出できない。
- CSV取り込み→PR #33の店舗別正規化→PR #34の監査→PR #37のパイプラインを次に接続する。
- CSV中の許諾フラグは自己申告。出典・利用条件は人が確認する。
- 実店舗データ0件。すべて架空テスト用。
