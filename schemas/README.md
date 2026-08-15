# JSON Schemas

Pydantic モデル(`python/src/manabi_forge/models/`、実装予定)から生成される JSON Schema Draft 2020-12 ファイル。**手書きで編集しない** — 再生成で差分が出ると CI が失敗する(spec §9.3)。

予定ファイル:

- `material.schema.json` — 教材マニフェスト(`material.yaml`)
- `item.schema.json` — ItemSpec(`item.yaml`)
- `review.schema.json` — レビューレコード
- `provenance.schema.json` — 来歴レコード
- `release.schema.json` — リリースマニフェスト
