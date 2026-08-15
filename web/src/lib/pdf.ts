// PDF.js の薄いラッパー(spec §17.5)。
// pdfjs-dist はサイズが大きいため動的 import で遅延読込し、
// テストではこのモジュールをモックする。
import type { PDFDocumentProxy } from "pdfjs-dist"

export type PdfDocument = PDFDocumentProxy

export async function loadPdfDocument(url: string): Promise<PdfDocument> {
  const pdfjs = await import("pdfjs-dist")
  const worker = await import("pdfjs-dist/build/pdf.worker.min.mjs?url")
  pdfjs.GlobalWorkerOptions.workerSrc = worker.default
  return pdfjs.getDocument({ url }).promise
}

export async function renderPageToCanvas(
  doc: PdfDocument,
  pageNumber: number,
  canvas: HTMLCanvasElement,
  scale: number
): Promise<void> {
  const page = await doc.getPage(pageNumber)
  const viewport = page.getViewport({ scale })
  canvas.width = viewport.width
  canvas.height = viewport.height
  const context = canvas.getContext("2d")
  if (!context) {
    throw new Error("canvas 2D context を取得できませんでした")
  }
  await page.render({ canvas, canvasContext: context, viewport }).promise
}
