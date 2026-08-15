# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

**Manabi Forge** — 日本の高校向け学習教材(初期は数学I)を、AI 支援で作成・検証・組版・公開するオープンな制作基盤。**正式仕様は `docs/spec.md`(全体像・データモデル・ロードマップ)であり、判断に迷ったら必ず spec を参照すること。**

3 層構成(意図的に分離):

- **Manabi Core** (`python/`): カリキュラム取込・教材バリデーション・数学検証・レビュー・TeX レンダリング・カタログ生成。uv 管理の単一 Python プロジェクト。CLI 名は `manabi`(現在は `doctor` / `version` のみ実装)。
- **Manabi Skills** (`skills/`): エージェント向けの移植可能な Agent Skills(SKILL.md + references + scripts)。Phase 3 で実装予定。
- **Manabi Library** (`web/`): React + Vite の静的サイト。検索・フィルタ・PDF プレビュー・ダウンロード。バックエンドなし、生成済み静的 JSON(catalog.json)を読むだけ。

その他: `curriculum/`(カリキュラム知識ベース)、`schemas/`(Pydantic から生成する JSON Schema — 手書き編集禁止)、`templates/`(LuaLaTeX テンプレート)、`materials/`(教材ソース)、`docs/adr/`(ADR-001〜007 済み)。

### 現在の状態

Phase 0(リポジトリ基盤)完了。次は spec §24–25, §30 の順で: Pydantic モデル(material/item/review/provenance)→ JSON Schema 生成 → TeX vertical slice(guided-example と common-test の各 1 教材)→ カリキュラムスナップショット → カタログ生成と Library ページ。

## コミット・Issue・PR の言語規則

- **コミットメッセージのタイトル、Issue タイトル、PR タイトルは英語**。本文(コミットボディ、Issue/PR の説明)は**日本語**で書く。
- コミット形式: `<type>: <description>`(type: feat, fix, refactor, docs, test, chore, perf, ci)。
- 例:

```
feat: add material manifest Pydantic model

MaterialManifest モデルと ID/パス整合性チェックを追加。
schemas/material.schema.json は本モデルから生成される。
```

## コマンド

ルートは pnpm workspace で、`pnpm <task>:web` / `pnpm <task>:py` のエイリアスを持つ(root package.json 参照)。

Web(`web/`、Manabi Library):

```bash
pnpm install                 # ルートで実行(workspace)
pnpm dev:web                 # 開発サーバー起動
pnpm build:web               # tsc -b + vite build
pnpm test:web                # Vitest 一括実行
pnpm --dir web test src/App.test.tsx   # 単一テストファイル実行
pnpm lint:web                # Biome check(lint + format 検査)
pnpm format:web              # Biome check --write(自動修正)
pnpm typecheck:web           # tsc --noEmit
```

- パッケージマネージャは **pnpm**(Node >= 20)。npm/yarn は使わない。
- Lint/Format は **Biome**(ESLint/Prettier は導入しない)。ローカルフックは pre-commit(`cd python && uv run pre-commit install`)。
- UI: Tailwind CSS v4 + shadcn/ui(`pnpm dlx shadcn@latest add <component>` → `web/src/components/ui/` に配置、`@/` エイリアスで import)。

Python(`python/`、Manabi Core、spec §9.2):

```bash
cd python
uv sync --locked --all-groups
uv run manabi doctor         # 環境診断(--json 対応)
uv run ruff check --config ruff.toml src tests
uv run ruff format --check --config ruff.toml src tests
uv run ty check              # 型チェッカーは ty(mypy/Pyright は併用しない)
uv run pytest                # 単一テスト: uv run pytest tests/test_doctor.py
```

Python バージョン(3.12)は `.python-version` / `requires-python` / Ruff `target-version` / ty `python-version` の 4 箇所で一致必須(CI で検査)。変更は 1 つの PR でまとめて行う。

## アーキテクチャ上の原則(spec §6, §26 ADR)

- **決定論的コア・確率的エッジ**: LLM は下書き・提案のみ。バリデーション、状態遷移、リリース判断、成果物命名はファイルと明示的コマンドで行う決定論的コアが所有する。
- **人間による公開ゲート**: 自動チェック全通過でも公開不可。人間レビュアーの承認なしに教材を `approved`/`published` にしてはならない(ADR-004)。
- **禁止依存**: Next.js / vinext / LangChain / LangGraph / 常駐バックエンド / ホスト型 DB は導入しない(ADR-001, 003)。Web は静的ビルドのまま保つ。
- **PDF は派生物**: 正本は構造化メタデータ(YAML)+ TeX ソース + レビュー/来歴レコード。ビルド成果物(`build/`、PDF)はコミットせず GitHub Releases に置く(ADR-005)。
- **TeX**: LuaLaTeX + latexmk(luatexja で日本語組版)。shell escape は無効。
- **データモデル**: Pydantic が正、JSON Schema 2020-12 はモデルから生成してコミット(再生成で差分が出たら CI 失敗)。
- 教材 ID は `<course>-<unit>-<format>-<serial>` 形式(例: `math1-qf-common-0001`)、小文字 ASCII で改版しても不変。

## コンテンツ・権利に関する厳守事項(spec §4, §20)

- **公式過去問 PDF・教科書スキャン・OCR・問題文のコピーをリポジトリに置かない**(一時的にも不可)。リンク・メタデータ・独自作成の分析のみ可。
- **商用シリーズ名を書式名・カテゴリ名・ブランドに使わない**。ガイド型教材は「段階解説型 / guided example」等の中立名で呼ぶ。
- 教材は学習目標とブリーフから独自に作成する(既存問題の言い換えから始めない)。
- ライセンス境界: コード = Apache-2.0、教材コンテンツ = CC BY 4.0(最終決定は ADR で)。
- 公開物には非公式教材である旨のディスクレーマーを必ず含める。

## CI

`.github/workflows/ci.yml` に web / python の 2 ジョブ。Actions は**フルコミット SHA でピン留め**(spec §19.2)し、`permissions: contents: read` を維持する。新しい Action を足すときも同様にピン留めすること。CI は `uv sync --locked` を使う — 依存を変えたら `uv.lock` を必ずコミットする。
