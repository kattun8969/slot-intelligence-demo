# WordPress更新パイプライン（段階導入）
対象 https://kajiplus.info/ 。②編集者の最終公開判断、リコリコ基準、既存機能の保護を優先する。

## Stage 1 — ニュースの下書き登録（このPR）
- WordPress REST APIの既存GitHub Secrets `WP_BASE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD` を利用する。秘匿値をリポジトリに書かない。
- ②編集者が事前確認したJSONを `wordpress-queue/news/<英数字ファイル名>.json` に登録する（記事の本文は独自執筆、公開可能な出典のみ）。
- GitHub Actions `WordPress news draft staging (editor reviewed)` の `Run workflow` を手動で実行し、`article_path` に対象JSONを指定。WP通常投稿（posts）の**下書きだけ**を作成する。公開済み記事や既存下書きはslug衝突で変更しない。
- `environment: wordpress-editor` を指定。Environment保護者/承認ルールが必要ならGitHub側で設定してから運用する。環境がない場合でも通常のSecretsだけで下書き作成が可能な場合があるため、保護設定を明示的に確認する。
- WP側で下書きを確認し、②だけが最終公開判断・操作。320px/375pxの表示、見出し、出典、重複、リンクを確認する。失敗時は成功と報告しない。

### 入稿用JSON例（実記事ではない。サンプルをそのまま実行しない）
```json
{
  "slug": "news-example-announcement-20261125",
  "title": "【サンプル】ニュースの見出し",
  "announced_on": "2026-11-25",
  "source_checked_at": "2026-11-25",
  "source_url": "https://example.org/source",
  "content_html": "<p>一次情報を確認した独自文章を入力。</p>",
  "editor_reviewed": true
}
```
※ Public GitHubに原稿を置く運用なので、非公開資料や権利処理が済んでいない画像・本文を入れないこと。

## Stage 2 — ニュースの自動更新
- 10時/18時ニュース制作の提出稿について、ソース日付・重複・出典・見出しを検査する。
- 本番公開は②の事前承認ポリシーが確立した案件に限定する。承認済みフラグだけで無条件公開しない（mainへの書込制限・GitHub Environment承認を含めて設計）。
- 実行履歴にWordPress記事ID、公開URL、検証日時を記録する。失敗時は下書きのまま、ロールバック可能な設計。

## Stage 3 — TOP更新履歴
- WordPress自身の公開日時・更新日時・機種・更新箇所アンカーから最新8件を表示。履歴対象をWordPressで確定し、GitHub Actionsを毎回起動しない。
- ニュース投稿と機種記事更新を区別し、更新日時の空振りを履歴に混ぜない。

## Stage 4 — 機種ページ定型差分更新
- 投稿タイプ/ID/権限のREST API検証後、既存の本文・メタ・投票・PAPIMO・期待値フォームのバックアップを保存。
- ①の提出HTMLを②が指定した既存セクションに限って差分置換。既存本文全体を自動上書きしない。
- リコリコ完成見本との乖離、スマホ320px/375px、出典/示唆/機能をWorkが検査してから公開。

## Workデザイン品質保証
- ②Workの既存一括編集タスク（11時・16時）で、複数機種をまとめてリコリコ基準と照合。
- 単に記事が公開されたことを品質完了としない。欠落（筐体画像/期待値/PAPIMO/狙い目/重要示唆）、順序、スマホでの読みにくさ、投票等の機能を明示的にチェックし、改修後の実URLで検証。
- 調査・原稿制作は①③に戻す。Workは差分編集、画面検証、公開判断に集中。Work枠が不足したら優先ページから順に検証し、残件をIssue管理。

## 安全・公開判定
- このPRは下書き専用。自動公開・既存ページ上書き・GitHub Pages変更は含まない。
- 作業完了は②が実URLで表示/動作を確認した時点。PR作成や下書きは「公開済み」ではない。
- 関連：#250、#256、#292、docs/publication-policy.md、docs/wordpress-machine-page-standard.md
