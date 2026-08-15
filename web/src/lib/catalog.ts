// Manabi Library のカタログデータ型とフィルタロジック(spec §17)。
// catalog.json は Manabi Core の `manabi catalog build`(issue #5)が生成する
// 静的 JSON。Web 側はそれを読むだけで、バックエンドを持たない。
//
// catalog.json は信頼境界の外にある(生成器の更新で未知の値が来得る)ため、
// format / difficulty は string として扱い、表示ラベルは既知値のみ翻訳して
// 未知値はスラッグをそのまま表示する(空白 UI へのサイレント縮退を防ぐ)。

export type CheckStatus = "pending" | "passed" | "failed"

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
  format: string
  difficulty: string
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
  includes_drafts?: boolean
  materials: CatalogMaterial[]
}

export interface CatalogFilters {
  course?: string
  unit?: string
  format?: string
  difficulty?: string
  q?: string
}

const FORMAT_LABELS: Record<string, string> = {
  "common-test-style": "共通テスト風",
  "guided-example": "段階解説型",
  worksheet: "ワークシート",
}

const DIFFICULTY_LABELS: Record<string, string> = {
  basic: "基礎",
  standard: "標準",
  advanced: "発展",
}

export const STATUS_LABELS: Record<CheckStatus, string> = {
  pending: "未検証",
  passed: "合格",
  failed: "不合格",
}

// 全教材に期待される検証・レビュー次元(spec §11.3)。カード上の
// レビュー進捗の分母を教材ごとの key 数に依存させない。
export const EXPECTED_CHECKS = [
  "schema",
  "tex",
  "mathematics",
  "curriculum",
  "editorial",
  "visual",
  "rights",
] as const

export function formatLabel(format: string): string {
  return FORMAT_LABELS[format] ?? format
}

export function difficultyLabel(difficulty: string): string {
  return DIFFICULTY_LABELS[difficulty] ?? difficulty
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status as CheckStatus] ?? status
}

export function reviewProgress(material: CatalogMaterial): {
  passed: number
  failed: number
  total: number
} {
  let passed = 0
  let failed = 0
  for (const check of EXPECTED_CHECKS) {
    const status = material.validation[check]
    if (status === "passed") {
      passed += 1
    } else if (status === "failed") {
      failed += 1
    }
  }
  return { passed, failed, total: EXPECTED_CHECKS.length }
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
