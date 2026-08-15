import { Link } from "react-router"

import { Button } from "@/components/ui/button"

export function HomePage() {
  return (
    <div className="flex max-w-2xl flex-col gap-4 p-6">
      <h1 className="font-semibold text-2xl">Manabi Library</h1>
      <p className="text-sm leading-relaxed">
        学習指導要領に基づいて制作・検証された学習教材を、検索・プレビュー・
        ダウンロードできるオープンなライブラリです。すべての教材はソースから
        再現可能で、カリキュラム整合・数学的検証・編集・権利の各レビューの
        状態を公開しています。
      </p>
      <div>
        <Button nativeButton={false} render={<Link to="/catalog" />}>
          教材カタログを見る
        </Button>
      </div>
    </div>
  )
}
