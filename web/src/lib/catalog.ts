// Manabi Library のカタログデータ型とフィルタロジック(spec §17)。
// catalog.json は Manabi Core の `manabi catalog build`(issue #5)が生成する
// 静的 JSON。Web 側はそれを読むだけで、バックエンドを持たない。

export type CheckStatus = "pending" | "passed" | "failed"

export type MaterialFormat =
  | "common-test-style"
  | "guided-example"
  | "worksheet"

export type Difficulty = "basic" | "standard" | "advanced"

export interface CatalogArtifacts {
  problem_pdf: string | null
  answer_sheet_pdf: string | null
  solution_pdf: string | null
  source_bundle: string | null
}

export interface CatalogMaterial {
  id: string
  version: string
  title: string
  language: string
  status: string
  subject: string
  course: string
  units: string[]
  format: MaterialFormat
  difficulty: Difficulty
  estimated_minutes: number
  curriculum_snapshot: string
  curriculum_codes: string[]
  validation: Record<string, CheckStatus>
  license: string
  ai_assisted: boolean
  artifacts: CatalogArtifacts
}

export interface Catalog {
  schema_version: string
  materials: CatalogMaterial[]
}

export interface CatalogFilters {
  course?: string
  unit?: string
  format?: string
  difficulty?: string
  q?: string
}

export const FORMAT_LABELS: Record<MaterialFormat, string> = {
  "common-test-style": "共通テスト風",
  "guided-example": "段階解説型",
  worksheet: "ワークシート",
}

export const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  basic: "基礎",
  standard: "標準",
  advanced: "発展",
}

export function filterMaterials(
  materials: CatalogMaterial[],
  filters: CatalogFilters
): CatalogMaterial[] {
  const query = filters.q?.trim().toLowerCase()
  return materials.filter((material) => {
    if (filters.course && material.course !== filters.course) {
      return false
    }
    if (filters.unit && !material.units.includes(filters.unit)) {
      return false
    }
    if (filters.format && material.format !== filters.format) {
      return false
    }
    if (filters.difficulty && material.difficulty !== filters.difficulty) {
      return false
    }
    if (query) {
      const haystack = [
        material.title,
        material.id,
        ...material.units,
        ...material.curriculum_codes,
      ]
        .join(" ")
        .toLowerCase()
      if (!haystack.includes(query)) {
        return false
      }
    }
    return true
  })
}

export function distinctValues<T>(
  materials: CatalogMaterial[],
  pick: (material: CatalogMaterial) => T[]
): T[] {
  return [...new Set(materials.flatMap(pick))].sort()
}

export async function loadCatalog(): Promise<Catalog> {
  const response = await fetch(`${import.meta.env.BASE_URL}catalog.json`)
  if (!response.ok) {
    throw new Error(`catalog.json の取得に失敗しました (${response.status})`)
  }
  return (await response.json()) as Catalog
}
