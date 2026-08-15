# ADR-003: No LangChain or LangGraph dependency

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

Manabi Forge のワークフローはファイルと明示的コマンドを中心とする決定論的なものであり、モデルオーケストレーション抽象に核となる正しさを依存させるべきではない。

## Decision

LangChain・LangGraph を依存に加えない。モデル連携が必要になった場合は、小さな内部プロトコル(`ModelProvider` Protocol、spec §7.3)を通すオプションのアダプタとして実装し、バリデーションやレビューのゲートを迂回させない。

## Consequences

- コアは Agent Skills 互換のあらゆるエージェント(Claude Code 等)から利用できる。
- フレームワークの破壊的変更からコアが隔離される。
