# ADR-002: Single uv project before uv workspace

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

現時点で Python のアプリケーション/ライブラリ境界は 1 つ(Manabi Core)しか存在しない。

## Decision

`python/` 配下に単一の uv プロジェクトを置く。uv workspace への移行は、独立したパッケージング・依存セット・リリースサイクル・テスト境界を必要とするコンポーネントが 2 つ以上現れたときに行う。移行トリガーは行数ではなく組織的必要性とする。

あわせて、最小サポート CPython を **3.12** とし、`.python-version`・`requires-python`・Ruff `target-version`・ty `python-version` を常に一致させる(CI で整合性を検査する)。

## Consequences

- セットアップとロックファイル管理が単純になる。
- 将来の workspace 移行は `packages/` / `apps/` 構成として spec §8.2 に既定されている。
