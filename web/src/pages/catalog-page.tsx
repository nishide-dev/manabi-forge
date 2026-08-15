// 教材カタログ(spec §17.2)。フィルタ状態は URL の検索パラメータに
// エンコードし、検索結果を共有可能にする。
import { useSearchParams } from "react-router"

import { MaterialCard } from "@/components/material-card"
import {
  DIFFICULTY_LABELS,
  distinctValues,
  FORMAT_LABELS,
  filterMaterials,
} from "@/lib/catalog"
import { useCatalog } from "@/lib/catalog-context"

const FILTER_KEYS = ["course", "unit", "format", "difficulty", "q"] as const

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
  const filters = Object.fromEntries(
    FILTER_KEYS.map((key) => [key, searchParams.get(key) ?? ""])
  )
  const results = filterMaterials(materials, filters)

  const setFilter = (key: string, value: string) => {
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
        <h2 className="font-semibold text-lg">教材カタログ</h2>
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
            label: FORMAT_LABELS[v],
          }))}
          onChange={(v) => setFilter("format", v)}
        />
        <SelectFilter
          label="難易度"
          value={filters.difficulty}
          options={distinctValues(materials, (m) => [m.difficulty]).map(
            (v) => ({ value: v, label: DIFFICULTY_LABELS[v] })
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

      <p className="text-muted-foreground text-sm">{results.length} 件</p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {results.map((material) => (
          <MaterialCard key={material.id} material={material} />
        ))}
      </div>
    </div>
  )
}
