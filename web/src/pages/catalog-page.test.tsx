import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes, useLocation } from "react-router"
import { describe, expect, it, vi } from "vitest"

import { AppRoutes } from "@/App"
import type { Catalog } from "@/lib/catalog"
import { CatalogProvider } from "@/lib/catalog-context"
import { CatalogPage } from "@/pages/catalog-page"
import { MaterialDetailPage } from "@/pages/material-detail-page"

function LocationProbe() {
  const location = useLocation()
  return <div data-testid="location-search">{location.search}</div>
}

const catalog: Catalog = {
  schema_version: "1.0",
  includes_drafts: false,
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

  it("filters by keyword input", async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.type(screen.getByLabelText("キーワード"), "場合の数")
    expect(screen.getByText("1 件")).toBeInTheDocument()
    expect(screen.queryByText("二次関数の最大・最小")).not.toBeInTheDocument()
  })

  it("renders unknown format values as their raw slug", () => {
    const withUnknown: Catalog = {
      schema_version: "1.0",
      materials: [
        {
          ...catalog.materials[0],
          id: "math1-qf-drill-0001",
          format: "drill-set",
          difficulty: "expert",
        },
      ],
    }
    render(
      <MemoryRouter initialEntries={["/catalog"]}>
        <CatalogProvider preloaded={withUnknown}>
          <Routes>
            <Route path="/catalog" element={<CatalogPage />} />
          </Routes>
        </CatalogProvider>
      </MemoryRouter>
    )
    // 未知の値は空白ではなくスラッグをそのまま表示する
    // (フィルタの option とカードのバッジの両方に現れる)
    expect(screen.getAllByText("drill-set").length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText("難易度: expert")).toBeInTheDocument()
  })

  it("writes selected filters into the shareable URL", async () => {
    // spec §17.2: フィルタ状態は URL にエンコードされ共有できる
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={["/catalog"]}>
        <CatalogProvider preloaded={catalog}>
          <Routes>
            <Route
              path="/catalog"
              element={
                <>
                  <CatalogPage />
                  <LocationProbe />
                </>
              }
            />
          </Routes>
        </CatalogProvider>
      </MemoryRouter>
    )
    await user.selectOptions(screen.getByLabelText("形式"), "worksheet")
    expect(screen.getByTestId("location-search")).toHaveTextContent(
      "format=worksheet"
    )
    await user.selectOptions(screen.getByLabelText("形式"), "")
    expect(screen.getByTestId("location-search")).not.toHaveTextContent(
      "format="
    )
  })
})

describe("draft preview banner", () => {
  it("appears when the catalog includes drafts", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <CatalogProvider preloaded={{ ...catalog, includes_drafts: true }}>
          <AppRoutes />
        </CatalogProvider>
      </MemoryRouter>
    )
    expect(screen.getByRole("status")).toHaveTextContent("開発プレビュー")
  })

  it("is hidden for a public catalog", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <CatalogProvider preloaded={catalog}>
          <AppRoutes />
        </CatalogProvider>
      </MemoryRouter>
    )
    expect(screen.queryByRole("status")).not.toBeInTheDocument()
  })
})

describe("error state", () => {
  it("shows an alert when the catalog cannot be loaded", async () => {
    const originalFetch = globalThis.fetch
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(
        new Response("not found", { status: 404 })
      ) as typeof fetch
    try {
      render(
        <MemoryRouter initialEntries={["/catalog"]}>
          <CatalogProvider>
            <Routes>
              <Route path="/catalog" element={<CatalogPage />} />
            </Routes>
          </CatalogProvider>
        </MemoryRouter>
      )
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "カタログを読み込めませんでした"
      )
    } finally {
      globalThis.fetch = originalFetch
    }
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
