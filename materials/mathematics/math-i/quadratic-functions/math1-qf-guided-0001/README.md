# math1-qf-guided-0001 — 二次関数の最大・最小

数学I「二次関数」単元の段階解説型(guided-example)教材。定義域つき二次関数の最大値・最小値を、平方完成 → 頂点の位置判定 → 端点比較の手順で解説する。

## ビルド

リポジトリルートから:

```bash
TEXINPUTS="templates/shared:templates/guided-example:" \
  latexmk -lualatex -halt-on-error -file-line-error \
  -output-directory=build/math1-qf-guided-0001 \
  materials/mathematics/math-i/quadratic-functions/math1-qf-guided-0001/source/main.tex
```

`manabi tex build` コマンド(issue #3)で置き換え予定。

## 状態

`material.yaml` を参照。レビューは `reviews/` に構造化レコードとして追加される。
