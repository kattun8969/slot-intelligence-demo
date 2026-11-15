# 実測収支の選択バイアス監査

勝った実戦だけが投稿されたデータは、件数が多くても平均収支を上方に歪める。実測エピソードの厳格な出典検証に加えて、**取得対象となった全実戦数**と**収集方法**を外部マニフェストとして確認する。

`audit_sampling(rows, manifest, min_samples=30)` の `manifest` に以下を指定する。

- `capture_method`: `consecutive_all_eligible` / `random_sample` / `voluntary_submission` / `selected_winners` / `unknown`
- `eligible_episode_count`: 収集対象になった実戦の総件数（観測数より少なくできない）
- `capture_protocol_predeclared`: 収集ルールを事前に決めたか
- `all_outcomes_reported`: 勝ち負けを問わず結果を収録したか
- `setting_distribution_status`: `verified` または `unknown`

不足件数、勝ち実戦の選別、任意投稿、設定配分の不明、収集ルールの事後決定を警告する。**このマニフェストは自己申告なので、警告ゼロでも偏りがない証明にはならない**。サンプル数が多いだけでは攻略期待値として公開せず、`strategy_ev_verified=false` と `publication_status=research_only` を維持する。

今回の実装では実店舗のデータ収集・期待値公開は行わない。
