import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { describe, expect, it } from "vitest"

import type { Catalog } from "@/lib/catalog"
import { CatalogProvider } from "@/lib/catalog-context"
import { CatalogPage } from "@/pages/catalog-page"
import { MaterialDetailPage } from "@/pages/material-detail-page"

const catalog: Catalog = {
  schema_version: "1.0",
  materials: [
    {
      id: "math1-qf-guided-0001",
      version: "0.1.0",
      title: "二次関数の最大・最小",
      language: "ja",
      status: "draft",
      subject: "mathematics",
      course: "mathematics-i",
      units: ["quadratic-functions"],
      format: "guided-example",
      difficulty: "standard",
      estimated_minutes: 15,
      curriculum_snapshot: "mext-84V10-2026-08",
      curriculum_codes: ["84V10-math-i-quadratic-functions"],
      validation: { schema: "pending", mathematics: "pending" },
      license: "CC-BY-4.0",
      ai_assisted: true,
      artifacts: {
        problem_pdf: null,
        answer_sheet_pdf: null,
        solution_pdf: null,
        source_bundle: null,
      },
    },
    {
      id: "matha-prob-worksheet-0001",
      version: "0.1.0",
      title: "場合の数",
      language: "ja",
      status: "draft",
      subject: "mathematics",
      course: "mathematics-a",
      units: ["counting"],
      format: "worksheet",
      difficulty: "basic",
      estimated_minutes: 10,
      curriculum_snapshot: "mext-84V10-2026-08",
      curriculum_codes: ["84V10-math-a-counting"],
      validation: { schema: "pending" },
      license: "CC-BY-4.0",
      ai_assisted: false,
      artifacts: {
        problem_pdf: null,
        answer_sheet_pdf: null,
        solution_pdf: null,
        source_bundle: null,
      },
    },
  ],
}

function renderCatalog(initialEntry = "/catalog") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <CatalogProvider preloaded={catalog}>
        <Routes>
          <Route path="/catalog" element={<CatalogPage />} />
          <Route
            path="/materials/:materialId"
            element={<MaterialDetailPage />}
          />
        </Routes>
      </CatalogProvider>
    </MemoryRouter>
  )
}

describe("CatalogPage", () => {
  it("renders every material without filters", () => {
    renderCatalog()
    expect(screen.getByText("二次関数の最大・最小")).toBeInTheDocument()
    expect(screen.getByText("場合の数")).toBeInTheDocument()
    expect(screen.getByText("2 件")).toBeInTheDocument()
  })

  it("applies filters from the URL", () => {
    renderCatalog("/catalog?course=mathematics-a")
    expect(screen.queryByText("二次関数の最大・最小")).not.toBeInTheDocument()
    expect(screen.getByText("場合の数")).toBeInTheDocument()
    expect(screen.getByText("1 件")).toBeInTheDocument()
  })

  it("narrows results when a filter is selected", async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.selectOptions(screen.getByLabelText("形式"), "worksheet")
    expect(screen.getByText("1 件")).toBeInTheDocument()
    expect(screen.getByText("場合の数")).toBeInTheDocument()
  })
})

describe("MaterialDetailPage", () => {
  it("shows metadata for an existing material", () => {
    renderCatalog("/materials/math1-qf-guided-0001")
    expect(screen.getByText("二次関数の最大・最小")).toBeInTheDocument()
    expect(
      screen.getByText("84V10-math-i-quadratic-functions")
    ).toBeInTheDocument()
    expect(screen.getByText("目安時間: 15 分")).toBeInTheDocument()
  })

  it("reports unknown materials", () => {
    renderCatalog("/materials/does-not-exist-0001")
    expect(screen.getByRole("alert")).toHaveTextContent("見つかりませんでした")
  })
})
