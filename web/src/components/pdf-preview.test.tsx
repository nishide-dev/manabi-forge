import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { PdfPreview } from "@/components/pdf-preview"

const { loadPdfDocument, renderPageToCanvas } = vi.hoisted(() => ({
  loadPdfDocument: vi.fn(),
  renderPageToCanvas: vi.fn(),
}))

vi.mock("@/lib/pdf", () => ({
  loadPdfDocument,
  renderPageToCanvas,
}))

describe("PdfPreview", () => {
  it("renders pages with navigation and a persistent download link", async () => {
    loadPdfDocument.mockResolvedValue({ numPages: 2 })
    renderPageToCanvas.mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<PdfPreview url="https://example.com/p.pdf" title="問題" />)

    expect(
      screen.getByRole("link", { name: "問題 をダウンロード" })
    ).toHaveAttribute("href", "https://example.com/p.pdf")
    expect(await screen.findByText("1 / 2 ページ")).toBeInTheDocument()

    const prev = screen.getByRole("button", { name: "前のページ" })
    const next = screen.getByRole("button", { name: "次のページ" })
    expect(prev).toBeDisabled()
    await user.click(next)
    expect(screen.getByText("2 / 2 ページ")).toBeInTheDocument()
    expect(next).toBeDisabled()

    // ページ描画がラッパー経由で呼ばれている
    expect(renderPageToCanvas).toHaveBeenCalled()
  })

  it("changes zoom via the accessible select", async () => {
    loadPdfDocument.mockResolvedValue({ numPages: 1 })
    renderPageToCanvas.mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<PdfPreview url="https://example.com/p.pdf" title="問題" />)
    await screen.findByText("1 / 1 ページ")

    renderPageToCanvas.mockClear()
    await user.selectOptions(screen.getByLabelText("拡大率"), "1.5")
    expect(renderPageToCanvas).toHaveBeenCalledWith(
      expect.anything(),
      1,
      expect.anything(),
      1.5
    )
  })

  it("falls back to the download link when the viewer fails", async () => {
    loadPdfDocument.mockRejectedValue(new Error("network down"))

    render(<PdfPreview url="https://example.com/p.pdf" title="問題" />)

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "プレビューを表示できませんでした"
    )
    // 失敗してもダウンロードリンクは残る(spec §17.5)
    expect(
      screen.getByRole("link", { name: "問題 をダウンロード" })
    ).toBeInTheDocument()
  })

  it("downloads from the canonical URL while previewing the mirror", async () => {
    loadPdfDocument.mockResolvedValue({ numPages: 1 })
    renderPageToCanvas.mockResolvedValue(undefined)

    render(
      <PdfPreview
        url="/artifacts/p.pdf"
        downloadHref="https://github.com/nishide-dev/manabi-forge/releases/download/t/p.pdf"
        title="問題"
      />
    )
    await screen.findByText("1 / 1 ページ")

    // プレビューは same-origin ミラー、ダウンロードはリリース URL(正本)
    expect(loadPdfDocument).toHaveBeenCalledWith("/artifacts/p.pdf")
    expect(
      screen.getByRole("link", { name: "問題 をダウンロード" })
    ).toHaveAttribute(
      "href",
      "https://github.com/nishide-dev/manabi-forge/releases/download/t/p.pdf"
    )
  })
})
