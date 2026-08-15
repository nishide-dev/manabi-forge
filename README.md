# Manabi Forge

**Curriculum-aware tools for creating reliable learning materials.**

学習内容に基づき、問題・教材・組版をつくり、検証し、公開するオープンな制作基盤。

Manabi Forge は、日本の高校向け学習教材(初期は数学I)を AI 支援で作成しつつ、カリキュラム整合・数学的正しさ・編集品質・来歴・ライセンス・組版を明示的に管理するための再現可能なワークフローを提供します。詳細な仕様とロードマップは [docs/spec.md](docs/spec.md) を参照してください。

## 構成

| ディレクトリ | 役割 |
|---|---|
| `python/` | **Manabi Core** — カリキュラム取込・検証・レビュー・TeX レンダリング・カタログ生成(uv 管理、CLI: `manabi`) |
| `web/` | **Manabi Library** — 教材の検索・プレビュー・ダウンロード用の React + Vite 静的サイト |
| `skills/` | **Manabi Skills** — エージェント向けの移植可能な Agent Skills |
| `curriculum/` | 正規化されたカリキュラム知識ベースとソースマニフェスト |
| `schemas/` | Pydantic モデルから生成される JSON Schema(2020-12) |
| `templates/` | LuaLaTeX 教材テンプレート |
| `materials/` | 教材ソース(メタデータ + TeX + レビュー/来歴レコード) |
| `docs/adr/` | Architecture Decision Records |

## セットアップ

```bash
# Web (Manabi Library)
pnpm install
pnpm lint:web && pnpm typecheck:web && pnpm test:web && pnpm build:web

# Python (Manabi Core)
cd python
uv sync --locked --all-groups
uv run manabi doctor        # 環境診断
uv run ruff check --config ruff.toml src tests
uv run ty check
uv run pytest
```

## ライセンス

- コード(CLI・スキーマ・スクリプト・TeX テンプレートコード): [Apache-2.0](LICENSE-CODE)
- 教材コンテンツ(問題文・解説・図版・カリキュラム注釈): [CC BY 4.0](LICENSE-CONTENT)

サードパーティ成果物は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照。

## 免責事項

この教材は Manabi Forge contributors が独自に制作した非公式教材です。文部科学省、大学入試センター、教科書会社、参考書出版社その他の団体による公式教材ではありません。
