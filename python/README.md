# manabi-forge (Python / Manabi Core)

Manabi Forge の決定論的コア。カリキュラム取込・教材バリデーション・数学検証・レビュー・TeX レンダリング・カタログ生成を担う uv 管理の Python プロジェクト。CLI 名は `manabi`。

## セットアップ

```bash
cd python
uv sync --locked --all-groups
```

## コマンド

```bash
uv run manabi doctor                 # 環境診断(--json 対応)
uv run ruff check --config ruff.toml src tests
uv run ruff format --check --config ruff.toml src tests
uv run ty check                      # 型チェック
uv run pytest                        # テスト
```

詳細は `../docs/spec.md` §9.2 および §16 を参照。
