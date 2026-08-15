// Manabi Library のルートレイアウト。
// GitHub Pages 等の静的ホストでサーバー側リライトを要求しないよう
// HashRouter を採用する(spec §6.7、ADR-001)。フィルタ共有用の
// 検索パラメータはハッシュ内で機能する。
import { HashRouter, Link, Route, Routes } from "react-router"

import { CatalogProvider } from "@/lib/catalog-context"
import { CatalogPage } from "@/pages/catalog-page"
import { HomePage } from "@/pages/home-page"
import { MaterialDetailPage } from "@/pages/material-detail-page"

export const DISCLAIMER =
  "この教材は Manabi Forge contributors が独自に制作した非公式教材です。文部科学省、大学入試センター、教科書会社、参考書出版社その他の団体による公式教材ではありません。"

export function AppRoutes() {
  return (
    <div className="flex min-h-svh flex-col">
      <header className="border-b">
        <nav className="flex items-center gap-6 px-6 py-3">
          <Link to="/" className="font-semibold">
            Manabi Library
          </Link>
          <Link to="/catalog" className="text-muted-foreground text-sm">
            カタログ
          </Link>
          <a
            href="https://github.com/nishide-dev/manabi-forge"
            className="ml-auto text-muted-foreground text-sm"
          >
            GitHub
          </a>
        </nav>
      </header>

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route
            path="/materials/:materialId"
            element={<MaterialDetailPage />}
          />
        </Routes>
      </main>

      <footer className="border-t px-6 py-4 text-muted-foreground text-xs leading-relaxed">
        <p>{DISCLAIMER}</p>
        <p className="mt-1">
          コンテンツ: CC BY 4.0 / コード: Apache-2.0 —{" "}
          <a
            className="underline"
            href="https://github.com/nishide-dev/manabi-forge"
          >
            nishide-dev/manabi-forge
          </a>
        </p>
      </footer>
    </div>
  )
}

export function App() {
  return (
    <HashRouter>
      <CatalogProvider>
        <AppRoutes />
      </CatalogProvider>
    </HashRouter>
  )
}
