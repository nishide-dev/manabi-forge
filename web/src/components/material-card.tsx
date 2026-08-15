import { Link } from "react-router"

import {
  type CatalogMaterial,
  difficultyLabel,
  formatLabel,
  reviewProgress,
} from "@/lib/catalog"

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-md border px-2 py-0.5 text-muted-foreground text-xs">
      {children}
    </span>
  )
}

export function MaterialCard({ material }: { material: CatalogMaterial }) {
  const { passed, failed, total } = reviewProgress(material)

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
        <Badge>{formatLabel(material.format)}</Badge>
        <Badge>難易度: {difficultyLabel(material.difficulty)}</Badge>
        <Badge>目安 {material.estimated_minutes} 分</Badge>
        <Badge>
          レビュー合格 {passed}/{total}
        </Badge>
        {failed > 0 && (
          <Badge>
            <span className="font-medium text-destructive">
              不合格 {failed} 件
            </span>
          </Badge>
        )}
        {material.status !== "published" && <Badge>{material.status}</Badge>}
      </div>
    </Link>
  )
}
