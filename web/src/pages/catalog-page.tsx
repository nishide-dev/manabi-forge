// 教材カタログ(spec §17.2)。フィルタ状態は URL の検索パラメータに
// エンコードし、検索結果を共有可能にする。
import { useSearchParams } from "react-router"

import { MaterialCard } from "@/components/material-card"
import {
  difficultyLabel,
  distinctValues,
  filterMaterials,
  formatLabel,
} from "@/lib/catalog"
import { useCatalog } from "@/lib/catalog-context"

const FILTER_KEYS = ["course", "unit", "format", "difficulty", "q"] as const

type FilterKey = (typeof FILTER_KEYS)[number]

function SelectFilter({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-muted-foreground text-xs">{label}</span>
      <select
        className="h-9 rounded-md border bg-background px-2"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">すべて</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  )
}

export function CatalogPage() {
  const state = useCatalog()
  const [searchParams, setSearchParams] = useSearchParams()

  if (state.status === "loading") {
    return <p className="p-6 text-muted-foreground">読み込み中…</p>
  }
  if (state.status === "error") {
    return (
      <p className="p-6 text-destructive" role="alert">
        カタログを読み込めませんでした: {state.message}
      </p>
    )
  }

  const materials = state.catalog.materials
  // FILTER_KEYS と 1:1 の明示的な型付け(キーの typo をコンパイルエラーにする)
  const filters: Record<FilterKey, string> = {
    course: searchParams.get("course") ?? "",
    unit: searchParams.get("unit") ?? "",
    format: searchParams.get("format") ?? "",
    difficulty: searchParams.get("difficulty") ?? "",
    q: searchParams.get("q") ?? "",
  }
  const results = filterMaterials(materials, filters)

  const setFilter = (key: FilterKey, value: string) => {
    setSearchParams(
      (previous) => {
        const next = new URLSearchParams(previous)
        if (value) {
          next.set(key, value)
        } else {
          next.delete(key)
        }
        return next
      },
      { replace: true }
    )
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="font-semibold text-lg">教材カタログ</h1>
        <p className="text-muted-foreground text-sm">
          フィルタ状態は URL に保存され、そのまま共有できます。
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <SelectFilter
          label="コース"
          value={filters.course}
          options={distinctValues(materials, (m) => [m.course]).map((v) => ({
            value: v,
            label: v,
          }))}
          onChange={(v) => setFilter("course", v)}
        />
        <SelectFilter
          label="単元"
          value={filters.unit}
          options={distinctValues(materials, (m) => m.units).map((v) => ({
            value: v,
            label: v,
          }))}
          onChange={(v) => setFilter("unit", v)}
        />
        <SelectFilter
          label="形式"
          value={filters.format}
          options={distinctValues(materials, (m) => [m.format]).map((v) => ({
            value: v,
            label: formatLabel(v),
          }))}
          onChange={(v) => setFilter("format", v)}
        />
        <SelectFilter
          label="難易度"
          value={filters.difficulty}
          options={distinctValues(materials, (m) => [m.difficulty]).map(
            (v) => ({ value: v, label: difficultyLabel(v) })
          )}
          onChange={(v) => setFilter("difficulty", v)}
        />
        <label className="flex min-w-48 flex-1 flex-col gap-1 text-sm">
          <span className="text-muted-foreground text-xs">キーワード</span>
          <input
            type="search"
            className="h-9 rounded-md border bg-background px-2"
            placeholder="タイトル・ID・単元・カリキュラムコード"
            value={filters.q}
            onChange={(event) => setFilter("q", event.target.value)}
          />
        </label>
      </div>

      <p aria-live="polite" className="text-muted-foreground text-sm">
        {results.length} 件
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {results.map((material) => (
          <MaterialCard key={material.id} material={material} />
        ))}
      </div>
    </div>
  )
}
