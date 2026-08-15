# Manabi Library (web)

教材の検索・フィルタ・PDF プレビュー・ダウンロードを提供する React + Vite の静的サイト。バックエンドを持たず、生成済みの静的 JSON(catalog.json)を読む(spec §17)。

> Based on [react-template](https://github.com/nishide-dev/react-template)

## Commands

ルートからは `pnpm <script>:web`、このディレクトリからは以下:

```bash
pnpm dev          # 開発サーバー起動
pnpm build        # tsc -b + vite build
pnpm test         # Vitest 実行
pnpm lint         # Biome check(lint + format 検査)
pnpm format       # Biome check --write(自動修正)
pnpm typecheck    # TypeScript 型チェック
```

## Structure

```text
src/
  components/
    ui/          # shadcn/ui コンポーネント
  lib/           # ユーティリティ (cn など)
  styles/        # globals.css
  test/          # Vitest セットアップ
```

## Adding shadcn/ui Components

```bash
pnpm dlx shadcn@latest add button
```

コンポーネントは `src/components/ui` に配置され、`@/components/ui/...` として import する。
