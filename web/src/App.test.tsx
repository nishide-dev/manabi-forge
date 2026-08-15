import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { App, DISCLAIMER } from "./App"

describe("App", () => {
  it("renders the library shell with navigation and disclaimer", async () => {
    render(<App />)
    expect(
      screen.getByRole("link", { name: "Manabi Library" })
    ).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "カタログ" })).toBeInTheDocument()
    expect(screen.getByText(DISCLAIMER)).toBeInTheDocument()
    // ホームページ(初期ルート)の見出し
    expect(
      await screen.findByRole("heading", { name: "Manabi Library" })
    ).toBeInTheDocument()
  })
})
