# CSV → 正規化 → イベント監査：統合仕様

`scripts/ev_csv_audit_bridge.py` は、PR #45 のCSV取込、PR #33 の正規化、PR #42 の入出力アダプター、PR #34 の監査を依存性注入で連結する。

## 使用例（統合後）
```python
from scripts.ev_hall_csv_import import import_observations_csv
from scripts.ev_counter_normalizer import normalize
from scripts.ev_contract_adapters import observation_to_audit
from scripts.ev_episode_audit import audit_event_stream
from scripts.ev_csv_audit_bridge import process_csv_to_audit

result = process_csv_to_audit(
    csv_text, rules=reviewed_rules,
    intake=import_observations_csv, normalize=normalize,
    to_audit=observation_to_audit, audit=audit_event_stream,
)
```

ルール未確認の行は隔離。ルールの確認は人手で行い、原データ出典・利用条件を別途審査する。CSVの行にある許諾ラベルだけで利用許諾が確定したとは扱わない。

**安全上の境界**: 店舗の履歴だけから実投資・回収・打ち始めの選択条件を復元しない。結果の `estimate_candidates` は必ず空で、公開サイト更新も行わない。

本PRは新規ファイルのみ。実店舗のデータ収集・実測EV算出・機種ページ変更なし。統合用テストは別の検証専用ブランチで実行する。
