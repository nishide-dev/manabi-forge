# ADR-001: React + Vite instead of Next.js or vinext

- **Status:** Accepted (MVP)
- **Date:** 2026-08-16

## Context

Manabi Library は検索・フィルタ・PDF プレビュー・ダウンロードが主目的の公開カタログであり、SSR・RSC・Server Actions を必要とする要件が存在しない。

## Decision

React + Vite による静的ビルドを採用する。Next.js および vinext は導入しない。

## Consequences

- 静的ホスティング(GitHub Pages / Cloudflare Pages)にそのままデプロイできる。
- 運用・セキュリティ面の攻撃面が最小になる。
- SSR が必要になった場合は新しい ADR で再検討する。
