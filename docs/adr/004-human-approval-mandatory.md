# ADR-004: Human approval is mandatory

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

自動チェックと AI 支援によるレビューは、カリキュラム解釈・教育学的判断・権利・複雑な数学に対して不完全である。

## Decision

自動チェックが全て通過しても、それだけを理由に教材を公開しない。教材が `approved` / `published` へ遷移するには人間レビュアー(公開は Maintainer)の承認を必須とする。

## Consequences

- レビューがボトルネックになり得るため、構造化ルーブリックと自動事前チェックで負荷を下げる(spec §27)。
- 自動レビューは `kind: automated` として記録し、人間レビューと偽装しない。
