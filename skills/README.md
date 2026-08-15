# Manabi Skills

エージェント向けの移植可能な Agent Skills の正本置き場。各 Skill は `SKILL.md`(YAML frontmatter 付き)を持つディレクトリで、名前は小文字・数字・ハイフンのみ(spec §12)。

初期 Skill(Phase 3 で実装予定):

- `resolving-curriculum/` — トピックをカリキュラムコードへ解決し、引用付きブリーフを作成
- `authoring-math-items/` — 承認済みブリーフから独自の数学 ItemSpec を作成
- `verifying-mathematics/` — 独立に解いて答え・定義域・一意性を検証
- `reviewing-materials/` — ルーブリックに基づくレビューと構造化された指摘記録
- `publishing-tex/` — テンプレート選択・TeX ビルド・リリースマニフェスト作成

設計規則: SKILL.md は簡潔に、詳細は `references/` へ、決定論的処理はリポジトリのスクリプトへ。公開する Skill には最低 3 つの評価ケースを付ける。
