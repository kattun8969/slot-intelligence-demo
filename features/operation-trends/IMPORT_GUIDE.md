# SNS・取材答え合わせの入力仕様

自動収集はまだ行わない。情報源の規約と転載許可を確認し、権利確認済みの構造化レコードのみ evidence-import.js で受け入れる。

```json
[
  {
    "id": "sample-event-001",
    "type": "official_event_result",
    "store_id": "sample-store",
    "machine_id": "sample-machine",
    "source_id": "sample-event-organizer",
    "source_url": "https://example.org/result",
    "event_date": "2026-11-01",
    "published_date": "2026-11-02",
    "collected_date": "2026-11-03",
    "rights": "verified",
    "verification": "reported",
    "announcement_timing": "postevent",
    "contradicts": false
  }
]
```

※上記は架空の例であり、実在する取材・店舗の情報ではない。

- 取材の対象台公開は「設定確定」ではない。後日公開の答え合わせは、公開日以前の予測に使わない。
- SNSは original_post_id でリポストを同一報告として扱う。投稿者が異なる場合も同じ元投稿なら重複排除。
- 設定確定情報は演出の内容と確認根拠を別途保存し、単なるSNSの「高設定っぽい」は reported のまま。
- 取材媒体の掲載可否、公式API規約、転載・画像利用の条件は情報源ごとに確認する。
- 地域・店舗固有の癖、バラエティ/主力、人気、見せ台適性、機種の世代交代は今後の予測特徴量として扱う。現時点では重み付け未実装。
