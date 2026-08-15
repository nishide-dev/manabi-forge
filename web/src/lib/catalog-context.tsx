// カタログ読込状態を配下のページへ提供する Context。
// テストでは preloaded でネットワークなしに注入できる。
import * as React from "react"

import { type Catalog, loadCatalog } from "@/lib/catalog"

export type CatalogState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; catalog: Catalog }

const CatalogContext = React.createContext<CatalogState>({ status: "loading" })

export function CatalogProvider({
  children,
  preloaded,
}: {
  children: React.ReactNode
  preloaded?: Catalog
}) {
  const [state, setState] = React.useState<CatalogState>(
    preloaded ? { status: "ready", catalog: preloaded } : { status: "loading" }
  )

  React.useEffect(() => {
    if (preloaded) {
      return
    }
    let cancelled = false
    loadCatalog()
      .then((catalog) => {
        if (!cancelled) {
          setState({ status: "ready", catalog })
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            status: "error",
            message: error instanceof Error ? error.message : String(error),
          })
        }
      })
    return () => {
      cancelled = true
    }
  }, [preloaded])

  return (
    <CatalogContext.Provider value={state}>{children}</CatalogContext.Provider>
  )
}

export function useCatalog(): CatalogState {
  return React.useContext(CatalogContext)
}
