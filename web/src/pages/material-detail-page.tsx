// 教材詳細ページ(spec §17.4)。カリキュラム整合・レビュー状態・来歴・
// ライセンス・非公式ディスクレーマーを表示する。PDF プレビュー(PDF.js)は
// リリースアセット配布後に追加する。
import { Link, useParams } from "react-router"

import { difficultyLabel, formatLabel, statusLabel } from "@/lib/catalog"
import { useCatalog } from "@/lib/catalog-context"

const VALIDATION_LABELS: Record<string, string> = {
  schema: "スキーマ",
  tex: "TeX ビルド",
  mathematics: "数学",
  curriculum: "カリキュラム",
  editorial: "編集",
  visual: "視覚",
  rights: "権利",
}

const ARTIFACT_LABELS: Record<string, string> = {
  problem_pdf: "問題 PDF",
  answer_sheet_pdf: "解答用紙 PDF",
  solution_pdf: "解答解説 PDF",
  source_bundle: "ソース一式 (ZIP)",
}

function StatusBadge({ status }: { status: string }) {
  const style =
    status === "passed"
      ? "border-foreground/40 font-medium"
      : status === "failed"
        ? "border-destructive text-destructive"
        : "text-muted-foreground"
  return (
    <span
      className={`inline-flex rounded-md border px-2 py-0.5 text-xs ${style}`}
    >
      {statusLabel(status)}
    </span>
  )
}

export function MaterialDetailPage() {
  const { materialId } = useParams()
  const state = useCatalog()

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

  const material = state.catalog.materials.find((m) => m.id === materialId)
  if (!material) {
    return (
      <div className="flex flex-col gap-3 p-6">
        <p role="alert">教材 {materialId} は見つかりませんでした。</p>
        <Link className="text-sm underline" to="/catalog">
          カタログへ戻る
        </Link>
      </div>
    )
  }

  return (
    <article className="flex max-w-3xl flex-col gap-6 p-6">
      <div>
        <Link className="text-muted-foreground text-sm underline" to="/catalog">
          ← カタログへ戻る
        </Link>
        <h1 className="mt-2 font-semibold text-xl">{material.title}</h1>
        <p className="mt-1 font-mono text-muted-foreground text-sm">
          {material.id} v{material.version}
        </p>
      </div>

      <section className="grid gap-2 text-sm sm:grid-cols-2">
        <p>コース: {material.course}</p>
        <p>単元: {material.units.join(", ")}</p>
        <p>形式: {formatLabel(material.format)}</p>
        <p>難易度: {difficultyLabel(material.difficulty)}</p>
        <p>目安時間: {material.estimated_minutes} 分</p>
        <p>状態: {material.status}</p>
      </section>

      <section>
        <h2 className="font-medium">カリキュラム整合</h2>
        <p className="mt-1 text-muted-foreground text-sm">
          スナップショット: {material.curriculum_snapshot}
        </p>
        <ul className="mt-1 list-inside list-disc font-mono text-sm">
          {material.curriculum_codes.map((code) => (
            <li key={code}>{code}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="font-medium">レビュー状態</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          {Object.entries(material.validation).map(([key, status]) => (
            <span key={key} className="flex items-center gap-1 text-sm">
              {VALIDATION_LABELS[key] ?? key}
              <StatusBadge status={status} />
            </span>
          ))}
        </div>
      </section>

      <section>
        <h2 className="font-medium">ダウンロード</h2>
        <ul className="mt-2 flex flex-col gap-1 text-sm">
          {Object.entries(material.artifacts).map(([key, url]) => (
            <li key={key}>
              {url ? (
                <a className="underline" href={url}>
                  {ARTIFACT_LABELS[key] ?? key}
                </a>
              ) : (
                <span className="text-muted-foreground">
                  {ARTIFACT_LABELS[key] ?? key}(未公開)
                </span>
              )}
            </li>
          ))}
        </ul>
      </section>

      <section className="text-muted-foreground text-sm">
        <h2 className="font-medium text-foreground">来歴・ライセンス</h2>
        <p className="mt-1">
          AI 支援:{" "}
          {material.ai_assisted ? "あり(詳細は provenance を参照)" : "なし"}
        </p>
        <p>コンテンツライセンス: {material.license}</p>
        <p className="mt-2">
          問題の誤りや曖昧さは{" "}
          <a
            className="underline"
            href={`https://github.com/nishide-dev/manabi-forge/issues/new?title=${encodeURIComponent(`[${material.id}] `)}`}
          >
            GitHub Issue
          </a>{" "}
          から報告できます。
        </p>
      </section>
    </article>
  )
}
