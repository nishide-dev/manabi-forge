# ADR-005: Generated PDFs are release assets

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

PDF は TeX ソースとメタデータから再現可能な派生物であり、Git 履歴に含めるとリポジトリが肥大化する。

## Decision

生成 PDF・ZIP バンドルは GitHub Releases のアセットとして配布し、リポジトリにはコミットしない(`build/` と `*.pdf` は ignore)。公開済みリリースアセットは不変とし、修正は新バージョンとして発行する。例外として、小さなゴールデンテスト用フィクスチャのみテスト配下へのコミットを許可する。

## Consequences

- すべての公開 PDF はクリーンなチェックアウトから CI で再ビルドできなければならない。
- リリースにはマニフェストとチェックサムを添付する(spec §18)。
