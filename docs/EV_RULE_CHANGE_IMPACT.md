# カウンタールールの変更影響監査

同じルールID・バージョンの内容を後から書き換えると、過去の観測データの解釈が変わる危険がある。次のコマンドで台帳の旧版と新版を比較する。

```bash
python -m scripts.ev_rule_change_impact old-counter-rules.json new-counter-rules.json
```

- 新しいルール版の追加：`requires_manual_review=true`。追加のみなら履歴再解釈を自動禁止しないが、出典と許諾は別途確認する。
- 既存ID・版の内容変更、削除：`historical_reinterpretation_blocked=true`、終了コード2。
- 確認済みルールの適用期間重複：履歴再解釈を禁止する。
- 変更がない場合：変更影響の監査を通過するが、実測EVの公開可否とは無関係。

既存の観測記録は当時のルール版とSHA-256で固定して保存すること。ルールを修正する場合は**既存のID・版を書き換えず、新しい版と適用期間を追加**する。公開サイトには影響しない。
