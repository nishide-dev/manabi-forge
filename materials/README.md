# Materials

教材ソースツリー。PDF は派生物であり、正本は構造化メタデータ + TeX ソース + レビュー/来歴レコード(spec §6.2, §11)。

パス構成と教材 ID:

```text
materials/<subject>/<course>/<unit>/<material-id>/
# 例: materials/mathematics/math-i/quadratic-functions/math1-qf-common-0001/
```

ID 形式は `<course>-<unit>-<format>-<serial>`(小文字 ASCII、改版しても不変)。各教材ディレクトリは `material.yaml`、`source/`、`reviews/`、`provenance.yaml`、`ATTRIBUTION.md` を持つ(spec Appendix A)。

状態遷移: `draft → generated → structurally-valid → under-review → (changes-requested | approved) → published → (revised | deprecated)`。`published` への遷移は Maintainer のみ。
