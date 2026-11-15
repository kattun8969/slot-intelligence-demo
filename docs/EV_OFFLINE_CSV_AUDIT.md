# 許諾済みCSVのオフライン監査

店舗データ提供元から許諾を得たCSV、または自身が権利を持つCSVをローカルで検査するためのコマンドです。ネットワーク取得・スクレイピング・公開サイト更新は行いません。

```bash
python -m scripts.ev_csv_audit_cli path/to/authorized.csv --summary-only
python -m scripts.ev_csv_audit_cli path/to/authorized.csv --rules data/ev/counter-rules.json
```

既定のルール台帳は空のため、実データを投入してもカウンターの意味が確認されるまでは隔離されます。CSVは15列を必要とし、仕様は `scripts/ev_hall_csv_import.py` の `FIELDS` を参照してください。出典URLと利用許諾申告だけで法的許諾を証明するわけではありません。

出力は研究用JSONで、CSV受理件数、監査済み件数、隔離理由、出典ルールのハッシュ、イベント監査を含みます。標準出力に識別子が含まれる場合があるため、共有時は `--summary-only` を使ってください。元CSVを変更せず、期待値を計算・公開しません。
