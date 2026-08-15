import { Link } from "react-router"

import {
  type CatalogMaterial,
  DIFFICULTY_LABELS,
  FORMAT_LABELS,
} from "@/lib/catalog"

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-md border px-2 py-0.5 text-muted-foreground text-xs">
      {children}
    </span>
  )
}

export function MaterialCard({ material }: { material: CatalogMaterial }) {
  const passed = Object.values(material.validation).filter(
    (status) => status === "passed"
  ).length
  const total = Object.keys(material.validation).length

  return (
    <Link
      to={`/materials/${material.id}`}
      className="block rounded-lg border p-4 transition-colors hover:bg-accent"
    >
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="font-medium">{material.title}</h3>
        <span className="font-mono text-muted-foreground text-xs">
          v{material.version}
        </span>
      </div>
      <p className="mt-1 text-muted-foreground text-sm">
        {material.course} / {material.units.join(", ")}
      </p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        <Badge>{FORMAT_LABELS[material.format]}</Badge>
        <Badge>難易度: {DIFFICULTY_LABELS[material.difficulty]}</Badge>
        <Badge>目安 {material.estimated_minutes} 分</Badge>
        <Badge>
          レビュー {passed}/{total}
        </Badge>
        {material.status !== "published" && <Badge>{material.status}</Badge>}
      </div>
    </Link>
  )
}
