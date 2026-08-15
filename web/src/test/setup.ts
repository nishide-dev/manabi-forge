import "@testing-library/jest-dom/vitest"
import { cleanup } from "@testing-library/react"
import { afterEach } from "vitest"

// vitest の globals を有効にしていないため、Testing Library の自動クリーン
// アップは働かない。テスト間で DOM が蓄積しないよう明示的に掃除する。
afterEach(() => {
  cleanup()
})
