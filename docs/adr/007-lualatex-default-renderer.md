# ADR-007: LuaLaTeX is the default renderer

- **Status:** Proposed(vertical slice で検証後に確定)
- **Date:** 2026-08-16

## Context

日本語教材の組版には Unicode と日本語組版(luatexja)の堅実なサポート、およびプログラマブルな文書設計が必要。

## Decision

既定のレンダラを LuaLaTeX + `latexmk`(`-lualatex -halt-on-error -file-line-error`)とする。shell escape は無効。CI はピン留めされた TeX Live 環境で実行する。

## Consequences

- フォントは TeX Live またはオープンライセンスのものに限定し、プロプライエタリフォントはコミット・配布しない。
- Phase 1 の vertical slice でビルド再現性を検証してから Accepted に更新する。
