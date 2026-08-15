import { describe, expect, it } from "vitest"

import {
  type CatalogMaterial,
  difficultyLabel,
  distinctValues,
  filterMaterials,
  formatLabel,
  reviewProgress,
  statusLabel,
} from "@/lib/catalog"

function makeMaterial(overrides: Partial<CatalogMaterial>): CatalogMaterial {
  return {
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
    validation: { schema: "pending" },
    license: "CC-BY-4.0",
    ai_assisted: true,
    artifacts: {
      problem_pdf: null,
      answer_sheet_pdf: null,
      solution_pdf: null,
      source_bundle: null,
    },
    ...overrides,
  }
}

const materials = [
  makeMaterial({}),
  makeMaterial({
    id: "math1-qf-common-0001",
    title: "二次関数と最大・最小(共通テスト風)",
    format: "common-test-style",
    difficulty: "advanced",
  }),
  makeMaterial({
    id: "matha-prob-worksheet-0001",
    title: "場合の数",
    course: "mathematics-a",
    units: ["counting"],
    format: "worksheet",
    difficulty: "basic",
  }),
]

describe("filterMaterials", () => {
  it("returns everything without filters", () => {
    expect(filterMaterials(materials, {})).toHaveLength(3)
  })

  it("filters by course", () => {
    const results = filterMaterials(materials, { course: "mathematics-a" })
    expect(results.map((m) => m.id)).toEqual(["matha-prob-worksheet-0001"])
  })

  it("filters by unit membership", () => {
    expect(
      filterMaterials(materials, { unit: "quadratic-functions" })
    ).toHaveLength(2)
  })

  it("filters by format and difficulty together", () => {
    const results = filterMaterials(materials, {
      format: "common-test-style",
      difficulty: "advanced",
    })
    expect(results.map((m) => m.id)).toEqual(["math1-qf-common-0001"])
  })

  it("matches free text against title, id, units, and codes", () => {
    expect(filterMaterials(materials, { q: "場合の数" })).toHaveLength(1)
    expect(filterMaterials(materials, { q: "qf-common" })).toHaveLength(1)
    expect(filterMaterials(materials, { q: "84v10" })).toHaveLength(3)
    expect(filterMaterials(materials, { q: "存在しない語" })).toHaveLength(0)
  })

  it("ignores whitespace-only queries", () => {
    expect(filterMaterials(materials, { q: "  " })).toHaveLength(3)
  })
})

describe("labels", () => {
  it("translates known values and falls back to the raw slug", () => {
    expect(formatLabel("guided-example")).toBe("段階解説型")
    expect(formatLabel("drill-set")).toBe("drill-set")
    expect(difficultyLabel("standard")).toBe("標準")
    expect(difficultyLabel("expert")).toBe("expert")
    expect(statusLabel("passed")).toBe("合格")
    expect(statusLabel("unknown-status")).toBe("unknown-status")
  })
})

describe("reviewProgress", () => {
  it("uses the fixed expected check set as denominator", () => {
    const material = makeMaterial({
      validation: { schema: "passed", mathematics: "failed" },
    })
    expect(reviewProgress(material)).toEqual({
      passed: 1,
      failed: 1,
      total: 7,
    })
  })
})

describe("distinctValues", () => {
  it("collects sorted unique values", () => {
    expect(distinctValues(materials, (m) => [m.course])).toEqual([
      "mathematics-a",
      "mathematics-i",
    ])
    expect(distinctValues(materials, (m) => m.units)).toEqual([
      "counting",
      "quadratic-functions",
    ])
  })
})
