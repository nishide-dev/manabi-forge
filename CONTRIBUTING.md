# Contributing to Manabi Forge

貢献ありがとうございます。詳細なワークフローは [docs/spec.md](docs/spec.md) を参照してください。

## 言語規則

- **コミットメッセージ・Issue・PR のタイトルは英語**、本文は日本語で書く。
- コミット形式: `<type>: <description>`(type: feat, fix, refactor, docs, test, chore, perf, ci)。

## 開発の前提

```bash
pnpm install                      # Web 依存
cd python && uv sync --locked --all-groups   # Python 依存
uv run manabi doctor              # 環境診断
```

ローカルフックは pre-commit で管理します:

```bash
cd python && uv run pre-commit install
```

## PR チェックリスト

- [ ] `pnpm lint:web` / `pnpm typecheck:web` / `pnpm test:web` が通る(Web 変更時)
- [ ] `ruff check` / `ruff format --check` / `ty check` / `pytest` が通る(Python 変更時)
- [ ] 新しいグローバルな lint 抑制を「PR を通すためだけ」に追加していない
- [ ] 権利・来歴に関わる変更は [AI_USAGE_POLICY.md](AI_USAGE_POLICY.md) と spec §20 に従っている

## 絶対に持ち込んではいけないもの

- 公式過去問の PDF・OCR・問題文のコピー(一時的にも不可)
- 教科書・市販参考書のスキャンや OCR
- API キーやプロンプト原文などの秘匿情報
- 商用シリーズ名を使った書式名・カテゴリ名

## レビューと公開

自動チェックが全て通っても、人間レビュアーの承認なしに教材は公開されません(spec §6.4)。レビューは構造化されたレビューレコードとして記録します。
