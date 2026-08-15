// 教材 PDF の組込プレビュー(spec §17.5)。
// 要件: 遅延読込・常時表示のダウンロードフォールバック・キーボード操作
// 可能なページ/ズーム操作・初期化失敗時もダウンロードは可能なまま。
import * as React from "react"

import { Button } from "@/components/ui/button"
import {
  loadPdfDocument,
  type PdfDocument,
  renderPageToCanvas,
} from "@/lib/pdf"

const SCALES = [0.75, 1, 1.25, 1.5] as const

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; doc: PdfDocument; pageCount: number }

export function PdfPreview({
  url,
  downloadHref,
  title,
}: {
  /** プレビューの取得元(same-origin のミラー。spec §17.5) */
  url: string
  /** ダウンロードリンク先(正本のリリース URL)。省略時は url */
  downloadHref?: string
  title: string
}) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null)
  const [state, setState] = React.useState<State>({ status: "loading" })
  const [pageNumber, setPageNumber] = React.useState(1)
  const [scale, setScale] = React.useState<number>(1)

  React.useEffect(() => {
    let cancelled = false
    setState({ status: "loading" })
    setPageNumber(1)
    loadPdfDocument(url)
      .then((doc) => {
        if (!cancelled) {
          setState({ status: "ready", doc, pageCount: doc.numPages })
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
  }, [url])

  React.useEffect(() => {
    const canvas = canvasRef.current
    if (state.status !== "ready" || !canvas) {
      return
    }
    let cancelled = false
    renderPageToCanvas(state.doc, pageNumber, canvas, scale).catch(
      (error: unknown) => {
        if (!cancelled) {
          setState({
            status: "error",
            message: error instanceof Error ? error.message : String(error),
          })
        }
      }
    )
    return () => {
      cancelled = true
    }
  }, [state, pageNumber, scale])

  return (
    <div className="flex flex-col gap-2">
      {/* ビューア初期化に失敗してもダウンロードは常に可能(spec §17.5) */}
      <p className="text-sm">
        <a className="underline" href={downloadHref ?? url} download>
          {title} をダウンロード
        </a>
      </p>

      {state.status === "loading" && (
        <p className="text-muted-foreground text-sm">プレビューを読み込み中…</p>
      )}
      {state.status === "error" && (
        <p className="text-muted-foreground text-sm" role="alert">
          プレビューを表示できませんでした({state.message})。
          上のリンクからダウンロードしてください。
        </p>
      )}
      {state.status === "ready" && (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={pageNumber <= 1}
              onClick={() => setPageNumber((n) => Math.max(1, n - 1))}
            >
              前のページ
            </Button>
            <span aria-live="polite" className="text-sm">
              {pageNumber} / {state.pageCount} ページ
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={pageNumber >= state.pageCount}
              onClick={() =>
                setPageNumber((n) => Math.min(state.pageCount, n + 1))
              }
            >
              次のページ
            </Button>
            <label className="ml-2 flex items-center gap-1 text-sm">
              <span className="text-muted-foreground text-xs">拡大率</span>
              <select
                className="h-8 rounded-md border bg-background px-1"
                value={scale}
                onChange={(event) => setScale(Number(event.target.value))}
              >
                {SCALES.map((value) => (
                  <option key={value} value={value}>
                    {Math.round(value * 100)}%
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="overflow-auto rounded-lg border">
            <canvas
              ref={canvasRef}
              role="img"
              aria-label={`${title} のプレビュー(${pageNumber} ページ目)`}
            />
          </div>
        </>
      )}
    </div>
  )
}
