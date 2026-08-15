# Manabi Forge — Project Specification and Roadmap

- **Document status:** Draft v0.1.1
- **Last updated:** 2026-08-16
- **Project display name:** Manabi Forge
- **GitHub repository:** `manabi-forge`
- **Python package:** `manabi_forge`
- **CLI command:** `manabi`
- **Web application:** Manabi Library
- **Primary language of the project:** Japanese, with English identifiers and optional English documentation

> Manabi Forge is an open, curriculum-aware production system for creating, reviewing, typesetting, publishing, and browsing reliable Japanese learning materials.

---

## 1. Executive summary

Manabi Forge will provide a reproducible workflow for producing Japanese high-school learning materials with AI assistance while keeping curriculum alignment, mathematical correctness, editorial quality, provenance, licensing, and typesetting under explicit control.

The project is not intended to be a generic chatbot or a thin wrapper around a language model. Its core is a collection of deterministic data models, validation tools, TeX templates, review procedures, and Agent Skills. An AI agent may draft or revise content, but publication is controlled by machine-verifiable checks and human approval.

The initial vertical slice targets mathematics, beginning with one unit of Mathematics I. It should support two publication styles:

1. **Common Test–style practice material** — original, unofficial problems inspired by the assessment characteristics described in official policy and evaluation documents.
2. **Guided reference material** — an original “concept → worked example → strategy → solution → notes → practice” format, publicly described as a **段階解説型** or **guided example** layout rather than by the name of any commercial series.

The system consists of three deliberately separated layers:

- **Manabi Core:** Python tools and structured data for curriculum ingestion, material validation, review, TeX rendering, and publication.
- **Manabi Skills:** Portable Agent Skills that teach compatible agents how to use Manabi Core and follow the editorial workflow.
- **Manabi Library:** A lightweight React + Vite application for searching, previewing, and downloading approved materials.

The initial architecture intentionally avoids Next.js, vinext, LangChain, LangGraph, and a permanent backend service. The Web application is a static client. Python is managed with uv. Model orchestration remains outside the deterministic core and can be performed by Claude Code, other Agent Skills–compatible tools, or a future thin provider adapter.

---

## 2. Vision

### 2.1 Long-term vision

Create a public infrastructure where educators, learners, and contributors can:

- find materials by course, unit, curriculum code, skill, format, and difficulty;
- inspect what each material is intended to assess or teach;
- download problem PDFs, answer sheets, solutions, source TeX, and metadata;
- verify whether a material has passed curriculum, mathematical, editorial, visual, and rights review;
- use Agent Skills to draft new materials in a consistent and auditable manner;
- reproduce every published PDF from version-controlled source files;
- improve materials through transparent GitHub review rather than opaque one-shot generation.

### 2.2 Product promise

A published Manabi Forge material should answer all of the following questions:

- What learning objective does it address?
- Which official curriculum items support that scope?
- What assumptions and prerequisites does it make?
- How was the answer checked?
- Who or what reviewed it?
- Which parts were generated or edited with AI assistance?
- Which sources or data were used?
- Under what license may it be reused?
- Can the PDF be rebuilt from the repository?

### 2.3 Positioning

Manabi Forge is best described as an **open educational publishing toolchain**, not merely an “AI problem generator.” Its defensible value comes from the workflow around generation:

- official-source grounding;
- structured metadata;
- independent verification;
- reproducible TeX builds;
- transparent provenance;
- reusable Agent Skills;
- a public browsing and distribution layer.

---

## 3. Goals and non-goals

### 3.1 Goals

The project shall:

1. Represent Japanese high-school curriculum scope in a machine-readable form.
2. Allow materials to cite one or more official curriculum codes and supporting annotations.
3. Generate original educational material with AI assistance without making AI output authoritative.
4. Validate metadata and source structure deterministically.
5. Verify a useful subset of mathematics symbolically or numerically.
6. separate authoring, verification, review, rendering, and publication responsibilities.
7. Render Japanese educational documents reproducibly with LaTeX.
8. Support multiple document designs through independent templates.
9. Publish searchable material metadata and downloadable artifacts through a static site.
10. Maintain clear licensing, attribution, provenance, and third-party notices.
11. Remain usable without LangChain, LangGraph, a hosted database, or a proprietary orchestration layer.
12. Make it possible to run the core workflow locally and in GitHub Actions.

### 3.2 Initial non-goals

The first public version will not attempt to:

- cover every high-school subject;
- reproduce commercial textbook or reference-book layouts exactly;
- redistribute textbook scans, textbook OCR, Common Test PDFs, or third-party problem text;
- guarantee that all mathematical claims can be verified automatically;
- generate a full reference book in one operation;
- provide private teacher-only answer access;
- provide a production-grade online AI generation service;
- support user accounts, payments, classrooms, grades, or learning analytics;
- replace qualified human editorial or legal review;
- claim official affiliation with the Ministry of Education, the National Center for University Entrance Examinations, textbook publishers, or examination bodies.

---

## 4. Naming and public identity

### 4.1 Namespaces

| Surface | Name |
|---|---|
| Project | Manabi Forge |
| Repository | `manabi-forge` |
| Python import | `manabi_forge` |
| CLI | `manabi` |
| Web UI | Manabi Library |
| Material namespace | `manabi:` |
| Default GitHub organization/repository path | `<owner>/manabi-forge` |

### 4.2 Suggested tagline

**Curriculum-aware tools for creating reliable learning materials.**

Japanese description:

**学習内容に基づき、問題・教材・組版をつくり、検証し、公開するオープンな制作基盤。**

### 4.3 Public disclaimer

Every public-facing material page and generated PDF shall include a concise disclaimer similar to:

> この教材は Manabi Forge contributors が独自に制作した非公式教材です。文部科学省、大学入試センター、教科書会社、参考書出版社その他の団体による公式教材ではありません。

When a material is described as Common Test–style, it shall also state that it is an original unofficial practice material and not a past question or official sample question.

### 4.4 Commercial-series naming rule

Public categories, templates, Skills, filenames, and UI labels shall not use a commercial series name as a format name. The guided reference format will use neutral terms such as:

- 段階解説型;
- 例題・方針・演習形式;
- guided example;
- stepwise reference.

---

## 5. Users and principal workflows

### 5.1 Personas

#### Learner

- Finds a Mathematics I practice problem.
- Reviews prerequisites and estimated time.
- Opens the problem PDF.
- Downloads an answer sheet and later the solution.

#### Teacher or tutor

- Filters by course, unit, difficulty, and format.
- Checks curriculum alignment and review status.
- Downloads source TeX to adapt an original material under its license.
- Reports an ambiguity or mathematical error through GitHub.

#### Material author

- Creates a material specification.
- Invokes an Agent Skill to draft a problem or worked example.
- Runs deterministic validation and rendering.
- Submits a pull request with provenance and review records.

#### Reviewer

- Reviews scope, mathematics, pedagogy, wording, accessibility, visual output, or rights.
- Records findings in a structured review file.
- Approves or requests changes without modifying the author’s provenance history.

#### Maintainer

- Updates curriculum source snapshots.
- Maintains schemas, templates, CI, releases, and the Library.
- Assigns releases and manages deprecations.

### 5.2 Principal end-to-end workflow

```text
Official sources
    ↓
Normalized curriculum knowledge base
    ↓
Material brief / ItemSpec
    ↓
AI-assisted or human draft
    ↓
Structural validation
    ↓
Independent mathematical verification
    ↓
Curriculum and pedagogical review
    ↓
Rights and provenance review
    ↓
TeX rendering and PDF checks
    ↓
Human approval
    ↓
Release assets + Manabi Library catalog
```

---

## 6. Product principles

### 6.1 Deterministic core, probabilistic edge

Language models may propose content, but they must not own canonical validation, state transitions, release decisions, or artifact naming. The canonical core shall operate on files and explicit command inputs.

### 6.2 Source of truth is not the PDF

The PDF is a derived artifact. Canonical source consists of:

- structured metadata;
- structured item data where practical;
- TeX source or template parameters;
- assets;
- review and provenance records.

### 6.3 Official-source hierarchy

The project shall distinguish authoritative scope sources from contextual references. A textbook is useful for terminology and presentation, but official curriculum documents are the primary source for scope.

### 6.4 Human publication gate

No AI-generated material is published solely because all automated checks pass. A human reviewer must approve the material before its state changes to `approved` or `published`.

### 6.5 Originality by construction

The authoring workflow should begin from learning objectives, constraints, and item structures—not from copying an existing problem and paraphrasing it.

### 6.6 Framework neutrality

Agent Skills should describe reproducible workflows and invoke repository tools. They should not require LangChain, LangGraph, or a particular hosted model provider.

### 6.7 Portable static publication

The Library shall build to static files and remain deployable to GitHub Pages, Cloudflare Pages, or another static host without changes to material data.

### 6.8 Progressive disclosure

Skills and curriculum references shall be split so agents load only the instructions and domain data needed for the current task.

---

## 7. Architecture overview

### 7.1 Logical components

```text
┌────────────────────────────────────────────────────────────┐
│                    Manabi Library                           │
│ React + Vite static application                            │
│ search / filters / PDF preview / downloads / provenance    │
└─────────────────────────────▲──────────────────────────────┘
                              │ catalog.json + release manifest
┌─────────────────────────────┴──────────────────────────────┐
│                    Publication layer                        │
│ catalog builder / release manifest / checksums / notices    │
└─────────────────────────────▲──────────────────────────────┘
                              │ approved material tree
┌─────────────────────────────┴──────────────────────────────┐
│                     Manabi Core                             │
│ curriculum / schemas / validation / review / TeX / CLI     │
│ Python managed with uv                                      │
└─────────────────────────────▲──────────────────────────────┘
                              │ files and commands
┌─────────────────────────────┴──────────────────────────────┐
│                     Manabi Skills                           │
│ Agent Skills: instructions + references + scripts/assets    │
└────────────────────────────────────────────────────────────┘
```

### 7.2 No always-on backend in the MVP

The MVP shall not require FastAPI or another persistent server. Python commands run locally or in CI. Manabi Library consumes generated static JSON and static assets.

A server may be introduced later only for a concrete requirement such as authenticated authoring, queued builds, private materials, or model invocation from the browser.

### 7.3 Model integration boundary

The first implementation does not require a Python model SDK. Compatible agents can use Skills to edit files and execute `manabi` commands.

If direct API integration is added later, it shall use a small internal protocol rather than spreading provider-specific objects through the core:

```python
from typing import Protocol

class ModelProvider(Protocol):
    def generate_text(self, *, system: str, prompt: str) -> str: ...
    def generate_structured(self, *, schema: dict, prompt: str) -> dict: ...
```

Provider adapters are optional packages and may never bypass validation or review gates.

---

## 8. Repository structure

### 8.1 Initial repository layout

```text
manabi-forge/
├── README.md
├── CONTRIBUTING.md
├── GOVERNANCE.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── AI_USAGE_POLICY.md
├── THIRD_PARTY_NOTICES.md
├── LICENSE-CODE
├── LICENSE-CONTENT
├── pyproject.toml                 # optional root tooling only
├── package.json                   # optional root task aliases only
├── pnpm-lock.yaml
├── .python-version
├── .node-version
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml        # repository-wide local quality hooks
├── .markdownlint.json
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
│
├── web/                           # Manabi Library
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   ├── public/
│   └── tests/
│
├── python/                        # one uv project at the beginning
│   ├── pyproject.toml              # dependencies, pytest, coverage, and ty config
│   ├── ruff.toml                   # Python lint and format policy
│   ├── uv.lock
│   ├── src/manabi_forge/
│   │   ├── cli/
│   │   ├── curriculum/
│   │   ├── models/
│   │   ├── validation/
│   │   ├── verification/
│   │   ├── review/
│   │   ├── tex/
│   │   ├── catalog/
│   │   └── provenance/
│   └── tests/
│
├── skills/                        # canonical portable Skill sources
│   ├── resolving-curriculum/
│   ├── authoring-math-items/
│   ├── verifying-mathematics/
│   ├── reviewing-materials/
│   └── publishing-tex/
│
├── curriculum/
│   ├── sources/                   # source manifests, URLs, hashes; no prohibited copies
│   ├── normalized/
│   ├── annotations/
│   └── snapshots/
│
├── schemas/
│   ├── material.schema.json
│   ├── item.schema.json
│   ├── review.schema.json
│   ├── provenance.schema.json
│   └── release.schema.json
│
├── templates/
│   ├── common-test/
│   ├── guided-example/
│   ├── worksheet/
│   ├── answer-sheet/
│   └── shared/
│
├── materials/
│   └── mathematics/
│       └── math-i/
│           └── quadratic-functions/
│               └── math1-qf-common-0001/
│
├── scripts/
├── docs/
│   ├── adr/
│   ├── editorial/
│   ├── curriculum/
│   └── contributor-guides/
│
└── build/                         # generated, ignored locally
```

### 8.2 Why a single Python project first

The first version shall use one uv project under `python/`. A uv workspace is introduced only when at least two Python components need independent packaging, dependency sets, release cycles, or test boundaries.

A future workspace could contain:

```text
python/
├── pyproject.toml
├── uv.lock
├── packages/
│   ├── manabi-core/
│   ├── manabi-curriculum/
│   ├── manabi-tex/
│   └── manabi-verification/
└── apps/
    ├── manabi-cli/
    └── manabi-api/
```

The migration trigger is organizational need, not line count alone.

### 8.3 Source and build separation

- `materials/**/source` and manifests are committed.
- `build/`, local PDFs, rendered page images, and temporary TeX files are ignored.
- Tagged release PDFs and ZIP bundles are uploaded as GitHub Release assets.
- A small curated set of golden images may be committed under test fixtures.
- Prohibited or private research material is never placed in the repository, even temporarily.

---

## 9. Technology decisions

### 9.1 Web application

| Concern | Decision |
|---|---|
| Framework | React + Vite |
| Language | TypeScript, strict mode |
| Styling | Tailwind CSS + shadcn/ui components |
| Formatting/lint | Biome |
| Unit/component tests | Vitest + Testing Library |
| Routing | React Router in library mode, or an equivalent small client router |
| PDF rendering | PDF.js |
| State | local component state and URL search parameters; no global state library initially |
| Data | generated static JSON files |
| Deployment | static `dist/`; GitHub Pages is the default MVP target |

Reasons:

- no requirement currently justifies Next.js, Server Components, Server Actions, or SSR;
- Vite produces a portable static build;
- the application’s primary operations are search, filter, preview, and download;
- a static site minimizes operations and security surface.

### 9.2 Python

| Concern | Decision |
|---|---|
| Environment and lockfile | uv |
| Minimum Python | pinned in `.python-version`; use a currently supported CPython release |
| Data models | Pydantic |
| Serialization | YAML for author-facing files; JSON for generated interchange |
| CLI | Typer or a thin argparse implementation; default recommendation: Typer |
| Test framework | pytest + pytest-cov |
| Lint/format | Ruff, configured in `python/ruff.toml` |
| Type checking | **ty**, configured in `python/pyproject.toml` and required in CI |
| Local hooks | pre-commit, including repository hygiene, Ruff, formatting, and Markdown checks |
| Mathematics | SymPy where applicable; explicit numeric and property tests elsewhere |
| Image/PDF utilities | system tools invoked through checked subprocess wrappers |

The Python quality baseline should follow the same general approach as
[`nishide-dev/ml-research-template`](https://github.com/nishide-dev/ml-research-template):
a uv-managed environment, an explicit Ruff policy, `ty check` as the type gate,
pytest, and equivalent local/CI commands. Manabi Forge shall adapt the rule set to
its own application rather than copying ML-specific exceptions without review.

#### 9.2.1 Required development dependencies

The initial `dev` dependency group shall include at least:

```toml
[dependency-groups]
dev = [
  "pre-commit",
  "pytest",
  "pytest-cov",
  "ruff",
  "ty",
]
```

Versions are resolved and committed through `python/uv.lock`. Automated updates
must arrive through reviewed dependency pull requests; CI must use `uv sync
--locked` and must never resolve an uncommitted environment implicitly.

#### 9.2.2 Ruff policy

Ruff is both the Python linter and formatter. The repository shall maintain a
committed `python/ruff.toml` rather than relying on tool defaults.

Required policy:

- set `target-version` to the exact minimum CPython version supported by the project;
- use one canonical line length, initially 88;
- enable a broad rule set and maintain an explicit, reviewed ignore list;
- define narrower per-file ignores for tests and generated files;
- exclude `.venv`, build output, generated catalog artifacts, TeX build output,
  Web dependencies, and other non-source directories;
- run both `ruff check` and `ruff format --check` in CI;
- allow automatic fixes locally, but never let CI modify the checkout;
- require specific rule codes for `# noqa` suppressions;
- reject new global ignores added solely to make a single pull request pass.

The initial configuration may start from the structure used by
`ml-research-template`, including `select = ["ALL"]`, formatter-conflict ignores,
and test-specific exceptions. Each ignored rule must have an inline rationale.
The maintainers may reduce the selected set only through an ADR or a focused
configuration pull request.

Canonical commands:

```bash
cd python
uv run ruff check --config ruff.toml src tests ../scripts
uv run ruff format --check --config ruff.toml src tests ../scripts
```

Local autofix commands:

```bash
cd python
uv run ruff check --fix --config ruff.toml src tests ../scripts
uv run ruff format --config ruff.toml src tests ../scripts
```

#### 9.2.3 ty policy

`ty` is the canonical Python type checker for the initial implementation. Do not
configure Pyright or mypy in parallel unless an ADR demonstrates a concrete need;
multiple type checkers with divergent semantics would create unnecessary policy
and suppression overhead.

The project shall configure ty under `[tool.ty]` in `python/pyproject.toml` and
shall at minimum:

- set the Python version to match `.python-version` and `requires-python`;
- run against production source, tests, and maintained Python scripts;
- use full diagnostic output in CI;
- fail CI on all unsuppressed type errors;
- require error-code-specific suppressions and an adjacent explanation;
- avoid `Any` at public boundaries where a Pydantic model, protocol, typed mapping,
  or generic parameter can express the contract;
- type subprocess results, filesystem interfaces, schema conversion, and provider
  adapters rather than treating infrastructure code as untyped glue.

Baseline configuration:

```toml
[tool.ty]

[tool.ty.environment]
python-version = "3.12" # update with the project's selected minimum version

[tool.ty.terminal]
output-format = "full"
```

Canonical command:

```bash
cd python
uv run ty check
```

The exact Python version in this example is illustrative until ADR-002 selects the
minimum supported interpreter. Once selected, `.python-version`,
`project.requires-python`, Ruff `target-version`, and ty `python-version` must be
updated in one pull request and checked for consistency in CI.

#### 9.2.4 Local hooks

A root `.pre-commit-config.yaml` shall provide fast feedback before pull requests.
It should include:

- trailing whitespace and end-of-file repair;
- TOML, YAML, and merge-conflict checks;
- a maximum newly added file-size check;
- Ruff lint with safe fixes;
- Ruff formatting;
- Markdown linting for specifications, Skills, and contributor documentation.

`ty check` may remain a pre-push or CI check if its runtime makes commit hooks
noticeably slow. Regardless of hook placement, CI remains authoritative; local
hooks are convenience controls and may not replace CI gates.

### 9.3 Data schemas

Pydantic models are the Python source of truth for validation. JSON Schema Draft 2020-12 files are generated from those models and committed so TypeScript, editors, contributors, and non-Python tools can validate the same files.

The committed schema must be reproducible. CI fails if regeneration changes tracked schema files.

### 9.4 TeX stack

The default engine is **LuaLaTeX** through `latexmk`.

Recommended packages include:

- `luatexja` for Japanese typesetting;
- `fontspec` and `unicode-math`;
- `tcolorbox` for structured educational boxes;
- `tikz` and `pgfplots` for original diagrams and plots;
- `tabularray` or standard table packages;
- `enumitem`, `geometry`, `fancyhdr`, `hyperref`, and `bookmark`;
- project-owned `.cls` and `.sty` files under `templates/shared`.

Default fonts should come from TeX Live or openly licensed system packages. Proprietary font files shall not be committed or distributed.

### 9.5 TeX reproducibility

- CI uses a pinned TeX Live environment or container digest.
- Builds use `latexmk -lualatex -halt-on-error -file-line-error`.
- Warnings are categorized; selected warnings fail CI.
- PDF metadata and timestamps are normalized where practical.
- A build manifest records tool versions, template version, material version, and source commit.

### 9.6 Hosting and artifacts

MVP:

- Manabi Library: GitHub Pages.
- Source code and reviews: GitHub repository.
- Published PDF and ZIP assets: GitHub Releases.
- Optional mirror: Cloudflare Pages or object storage, without changing the catalog schema.

Large binaries are not committed to Git history unless they are tiny test fixtures.

---

## 10. Curriculum knowledge base

### 10.1 Source hierarchy

The curriculum resolver shall assign each piece of information a source class.

| Priority | Source class | Purpose |
|---|---|---|
| 1 | Statutory/official curriculum text | authoritative scope and objectives |
| 2 | Official curriculum explanations | depth, treatment, limitations, connections |
| 3 | MEXT curriculum-code tables | stable machine-readable identifiers |
| 4 | Official exam policy and evaluation | assessment characteristics and observed issues |
| 5 | Textbook catalogs and editorial intent documents | terminology, ordering, comparison of treatment |
| 6 | Licensed public datasets and statistics | source material for original questions |
| 7 | Maintainer annotations | explicit interpretations and crosswalks |
| 8 | Private research notes | never published unless rights permit |

### 10.2 Initial official sources

Initial ingestion shall focus on:

- High School Courses of Study, 2018 notification;
- subject-specific explanatory documents;
- MEXT high-school curriculum code table `84V10`;
- Common Test question-creation policy;
- Common Test evaluation and analysis reports;
- public past-question index for metadata and manual analysis;
- textbook catalogs and editorial intent documents where useful.

### 10.3 Normalized curriculum record

Example:

```yaml
code: "84V10-..."
source_version: "84V10"
school_level: high-school
subject: mathematics
course: mathematics-i
path:
  - quadratic-functions
  - variation-of-quadratic-functions
statement_ja: "..."
objective_dimensions:
  - knowledge-and-skills
  - thinking-judgment-expression
prerequisites:
  - junior-high-quadratic-relations
scope_notes:
  - "Maximum and minimum under stated domains"
restrictions: []
source_refs:
  - id: mext-course-of-study
    locator: "..."
review:
  status: reviewed
  reviewed_by: "..."
  reviewed_at: "YYYY-MM-DD"
```

### 10.4 Ingestion policy

- Download scripts record URL, retrieval date, checksum, and media type.
- A source file is stored only if its publication and repository storage are permitted.
- Otherwise, store metadata and a local-fetch instruction, not the bytes.
- PDFs requiring interpretation are processed into maintainer-authored summaries with page references.
- OCR output is never treated as authoritative without human comparison to the source.
- Changes between snapshots generate a machine-readable diff for review.

### 10.5 Curriculum update process

1. Run `manabi curriculum check-updates`.
2. Download or identify new official versions.
3. Verify hashes and source metadata.
4. Generate normalized diffs.
5. Human reviewer approves scope changes.
6. Affected materials are marked `needs-curriculum-review`.
7. Published material remains available but displays the curriculum snapshot against which it was approved.

### 10.6 Curriculum resolver behavior

The resolver should answer:

- whether a topic belongs to a given course;
- which codes are directly or indirectly relevant;
- prerequisite units;
- explicit treatment limitations;
- whether a proposed solution uses knowledge outside the target scope;
- uncertainty notes where official text requires interpretation.

It must return evidence and uncertainty, not just a Boolean.

---

## 11. Material and item data model

### 11.1 Material lifecycle

```text
draft
  → generated
  → structurally-valid
  → under-review
  → changes-requested | approved
  → published
  → revised | deprecated
```

Only maintainers may transition a material to `published`.

### 11.2 Stable identifiers

Recommended identifier format:

```text
<course>-<unit>-<format>-<serial>
```

Example:

```text
math1-qf-common-0001
math1-qf-guided-0001
```

Rules:

- lowercase ASCII;
- stable across revisions;
- no year embedded unless the year is semantically part of the material;
- version stored separately using semantic versioning or an integer revision.

### 11.3 Material manifest

Every material directory must contain `material.yaml`.

```yaml
schema_version: "1.0"
id: math1-qf-common-0001
version: "0.1.0"
title: 二次関数と最大・最小
language: ja
status: draft

classification:
  school_level: high-school
  subject: mathematics
  course: mathematics-i
  units:
    - quadratic-functions
  format: common-test-style
  difficulty: standard
  estimated_minutes: 15
  audience:
    - learner

curriculum:
  snapshot: mext-84V10-2026-08
  codes:
    - "84V10-..."
  alignment_status: pending

artifacts:
  problem_pdf: null
  answer_sheet_pdf: null
  solution_pdf: null
  source_bundle: null

validation:
  schema: pending
  tex: pending
  mathematics: pending
  curriculum: pending
  editorial: pending
  visual: pending
  rights: pending

license:
  content: CC-BY-4.0
  code: Apache-2.0

provenance:
  ai_assisted: true
  origin: original
  source_text_included: false
```

### 11.4 ItemSpec

`item.yaml` is recommended for individual problems and required for generated Common Test–style items. It captures semantic structure independently of the final TeX design.

Minimum fields:

- prompt/stem;
- parts;
- answer type;
- correct answer;
- distractor rationale where applicable;
- required knowledge;
- intended reasoning process;
- source data and licenses;
- solution outline;
- verification strategy;
- accessibility description for figures.

Complex TeX is allowed in explicitly marked fields, but the structured model should remain sufficient for search and review.

### 11.5 Review record

Each review is an immutable YAML or JSON file under `reviews/`.

```yaml
schema_version: "1.0"
material_id: math1-qf-common-0001
review_id: math-review-2026-0001
review_type: mathematics
reviewer:
  kind: human
  name: contributor-id
reviewed_commit: "<git-sha>"
result: changes-requested
findings:
  - severity: high
    location: item.parts[2]
    code: non-unique-answer
    message: 条件のもとで選択肢BとDがともに成立する。
    suggested_action: 条件を追加するか選択肢Dを修正する。
created_at: "2026-08-16T00:00:00Z"
```

Automated reviews use `kind: automated` and identify the tool and version. They never masquerade as human reviews.

### 11.6 Provenance record

Provenance shall include:

- human authors and editors;
- AI-assisted steps;
- model/provider identifiers when disclosure is permitted;
- prompts or prompt hashes according to repository policy;
- source datasets and licenses;
- source commit and generated artifact hashes;
- transformations and manual changes;
- similarity-review status;
- rights-review status.

Sensitive prompts or credentials must never be stored. A redacted summary or hash may be used.

---

## 12. Agent Skills architecture

### 12.1 Standards compliance

Each Skill is a directory containing at minimum a `SKILL.md` file with YAML frontmatter. Names use lowercase letters, digits, and hyphens. Descriptions state both what the Skill does and when it should be used.

Canonical Skills live under `skills/`. Packaging commands can copy or bundle them for:

- project-local Claude Code installation;
- Agent Skills–compatible tools;
- zipped upload surfaces;
- API-managed Skill versions.

### 12.2 Skill design rules

- Keep `SKILL.md` procedural and concise.
- Move detailed curriculum tables into `references/`.
- Put deterministic operations into repository scripts, not prose instructions.
- Include failure handling and required checks.
- Do not embed volatile version numbers when a generated reference file can hold them.
- Include at least three evaluation cases for every publishable Skill.
- Keep references shallow and directly named.
- Do not grant a Skill more file or network access than needed.

### 12.3 Initial Skills

#### `resolving-curriculum`

Purpose:

- map a requested topic to curriculum codes;
- identify prerequisites and scope limitations;
- produce a cited curriculum brief.

Inputs:

- course;
- unit or learning objective;
- target difficulty;
- optional format.

Outputs:

- curriculum brief YAML;
- evidence list;
- uncertainty and escalation notes.

#### `authoring-math-items`

Purpose:

- create original mathematics ItemSpecs from an approved brief;
- avoid copying source problem wording;
- produce complete answer and solution reasoning.

It must not mark its own output as verified.

#### `verifying-mathematics`

Purpose:

- solve the problem independently;
- check the stated answer;
- test domains, edge cases, units, and uniqueness;
- invoke SymPy or numeric/property checks where appropriate;
- record unsupported claims for human review.

The verifier should not read the author’s hidden chain of reasoning. It may read the final proposed solution only after completing an independent solution attempt.

#### `reviewing-materials`

Purpose:

- perform curriculum, pedagogical, wording, accessibility, and format review using explicit rubrics;
- classify findings by severity;
- never silently rewrite the material during a formal review.

#### `publishing-tex`

Purpose:

- select an approved template;
- render TeX;
- build PDFs;
- inspect logs and generated pages;
- create release manifests and source bundles.

It shall refuse publication when required reviews are absent or stale.

### 12.4 Later specialized Skills

- `designing-distractors`;
- `authoring-common-test-materials`;
- `authoring-guided-examples`;
- `reviewing-rights-and-provenance`;
- `reviewing-visual-layout`;
- `updating-curriculum-data`;
- `assembling-workbooks`;
- subject-specific authoring and verification Skills.

### 12.5 Skill evaluation

Each Skill shall have a test set containing:

- an ordinary success case;
- an ambiguous request requiring documented assumptions;
- a request that must be refused or escalated;
- malformed input;
- an adversarial case attempting to bypass review or rights rules.

Evaluation checks include output structure, correct commands, refusal behavior, evidence use, and absence of prohibited source reuse.

---

## 13. Authoring and review pipeline

### 13.1 Stage A — Brief

The brief defines:

- audience;
- course and unit;
- curriculum codes;
- target reasoning skills;
- difficulty;
- expected time;
- item format;
- allowed and prohibited techniques;
- source data requirements;
- accessibility requirements.

No problem drafting begins until the brief validates.

### 13.2 Stage B — Draft

An author or agent creates:

- ItemSpec;
- answer;
- complete solution;
- distractor rationales;
- figure descriptions and source assets;
- provenance entry.

The draft must be original and should be constructed from the brief rather than a copied reference problem.

### 13.3 Stage C — Structural validation

Automated checks:

- schema validity;
- stable ID and path consistency;
- required files;
- curriculum code existence;
- asset existence;
- license fields;
- prohibited phrases and placeholder markers;
- dangling references;
- malformed TeX fragments where detectable.

### 13.4 Stage D — Mathematical verification

Verification layers:

1. Independent human- or agent-produced solution.
2. Symbolic checks using SymPy where suitable.
3. Numeric sampling and boundary tests.
4. Answer-choice uniqueness checks.
5. Dimensional/unit checks.
6. Graph/table consistency checks.
7. Manual proof review for unsupported symbolic domains.

A “SymPy passed” result is evidence, not a proof that the educational solution is correct or appropriate.

### 13.5 Stage E — Curriculum review

The reviewer checks:

- target content is within the cited course;
- prerequisites are reasonable;
- no solution step requires uncited later-course knowledge;
- terminology matches current curriculum conventions;
- difficulty comes from reasoning rather than hidden out-of-scope knowledge;
- learning objective and item behavior agree.

### 13.6 Stage F — Pedagogical and editorial review

Checks include:

- unambiguous instructions;
- fair and useful distractors;
- meaningful use of context and data;
- appropriate cognitive demand;
- readable Japanese;
- answer explanation proportional to the target learner;
- no misleading shortcuts;
- notation consistency;
- accessibility text and figure legibility.

### 13.7 Stage G — Rights and provenance review

Checks include:

- all text and figures are original, licensed, public domain, or properly quoted;
- no prohibited past-question or textbook content is present;
- datasets have acceptable terms and attribution;
- similarity to reference material has been considered;
- AI assistance is recorded;
- release license is compatible with included components.

### 13.8 Stage H — TeX and visual review

Automated checks:

- successful compilation;
- no missing glyphs;
- no unresolved references;
- no overfull boxes above configured thresholds;
- expected page count range;
- fonts embedded or otherwise compliant;
- selectable text where expected;
- PDF metadata present;
- generated thumbnails valid.

Visual reviewer checks:

- hierarchy and spacing;
- page breaks;
- answer boxes and marks;
- diagrams at print size;
- grayscale legibility;
- solution/problem separation;
- branding and disclaimer.

### 13.9 Stage I — Approval and publication

Publication requires:

- all required review types passed against the current source commit;
- no unresolved high- or critical-severity findings;
- release artifacts built in CI;
- human maintainer approval;
- release manifest and checksums;
- Library catalog update.

---

## 14. Review severities and quality gates

### 14.1 Severity levels

| Severity | Meaning | Publication effect |
|---|---|---|
| Critical | rights violation, fundamentally false answer, unsafe or corrupt artifact | immediate block and possible takedown |
| High | non-unique answer, out-of-scope dependency, major ambiguity | block |
| Medium | pedagogical weakness, significant layout issue, incomplete explanation | block unless explicitly waived by maintainer |
| Low | style, minor wording, optional improvement | may publish with recorded decision |
| Note | observation without required action | no block |

### 14.2 Definition of Done for a material

A material is done when:

- metadata validates;
- curriculum codes resolve;
- mathematical review passes;
- curriculum review passes;
- editorial review passes;
- rights review passes;
- TeX builds reproducibly;
- visual review passes;
- PDFs and source bundle have checksums;
- license and attribution are visible;
- provenance is complete;
- material has a permanent page in Manabi Library;
- a human maintainer approves the release.

---

## 15. TeX template system

### 15.1 Template boundaries

A template owns visual structure, not subject truth. It may define:

- page size and margins;
- typography;
- headers and footers;
- boxes and labels;
- question numbering;
- answer grids;
- solution styles;
- callouts;
- document metadata.

The material source owns mathematical and educational content.

### 15.2 Initial templates

#### `common-test`

Features:

- multi-part questions;
- conversations, data tables, and original diagrams;
- answer-choice and mark-number components;
- separate answer sheet;
- compact but readable page design;
- explicit unofficial-material disclaimer.

The visual design must be original and must not reproduce an official test sheet pixel-for-pixel.

#### `guided-example`

Features:

- concept summary;
- worked example;
- strategy/approach box;
- full solution;
- alternative method or caution;
- practice item;
- related curriculum tags.

The visual identity must be owned by Manabi Forge and not imitate a commercial reference book’s distinctive arrangement, colors, icons, or wording.

#### `worksheet`

Features:

- classroom-print-friendly layout;
- optional workspace;
- answer key variant;
- grayscale-safe design.

### 15.3 Template versioning

Templates use semantic versions. Every artifact records the template ID and version. A template update does not silently alter existing release files; re-rendering requires a new material revision or rebuild release.

### 15.4 Escape hatches

A material may include controlled custom TeX for a complex diagram or layout, but:

- custom commands must be namespaced;
- shell escape is disabled by default;
- arbitrary file access is prohibited in CI;
- custom code is included in rights and security review.

---

## 16. Manabi CLI

### 16.1 Command design

Proposed commands:

```text
manabi init
manabi doctor

manabi curriculum sync
manabi curriculum validate
manabi curriculum query
manabi curriculum diff

manabi material new
manabi material validate
manabi material status

manabi verify math
manabi review run
manabi review list

manabi tex build
manabi tex inspect

manabi catalog build
manabi release prepare
manabi release verify

manabi skills validate
manabi skills package
manabi skills install
```

### 16.2 Exit-code contract

- `0`: success;
- `1`: validation or review failure;
- `2`: usage/configuration error;
- `3`: missing external dependency;
- `4`: rights or provenance block;
- `5`: internal unexpected error.

Commands shall support human-readable output and `--json` machine-readable output.

### 16.3 `manabi doctor`

Checks:

- Python and uv;
- Node and pnpm;
- TeX engine and `latexmk`;
- Poppler tools;
- Git;
- required fonts;
- schema consistency;
- writable build directories.

It reports corrective commands without automatically making privileged system changes.

---

## 17. Manabi Library specification

### 17.1 MVP pages

1. Home.
2. Material catalog.
3. Material detail.
4. Curriculum map.
5. About, licensing, and editorial policy.
6. Build/review status page for contributors.

### 17.2 Catalog filters

- school level;
- subject;
- course;
- unit;
- curriculum code;
- format;
- difficulty;
- estimated time;
- review status;
- artifact type;
- updated date;
- language.

Filter state is encoded in the URL so a search can be shared.

### 17.3 Material card

Display:

- title;
- course and unit;
- format;
- difficulty;
- estimated time;
- approval/review badges;
- problem and solution availability;
- version and update date.

### 17.4 Material detail page

Display:

- title and summary;
- intended learning objectives;
- curriculum alignment;
- prerequisites;
- PDF preview;
- downloads;
- review status;
- provenance summary;
- license and attribution;
- version history;
- report-an-issue link;
- unofficial-material disclaimer.

### 17.5 PDF preview

PDF.js is used for an integrated viewer. Requirements:

- lazy loading;
- visible download fallback;
- keyboard navigation;
- zoom and page controls;
- same-origin or properly configured CORS for remote release assets;
- no assumption that preview is available offline;
- a text or summary alternative where practical.

### 17.6 Search architecture

MVP catalog data is generated as static JSON. For small catalogs, filtering can scan the in-memory array. When size requires it, CI generates a compact client-side full-text index.

No hosted search service is required initially.

### 17.7 Accessibility

Target WCAG 2.2 AA for the Web UI where feasible.

- semantic headings and landmarks;
- keyboard-operable filters and viewer controls;
- visible focus states;
- sufficient contrast;
- non-color-only status indicators;
- Japanese language attributes;
- alt text for thumbnails;
- textual descriptions for educational diagrams;
- printer-friendly PDF design.

### 17.8 Responsive behavior

- mobile: catalog and metadata fully usable; PDF may open in a dedicated view;
- tablet: split metadata/preview where space permits;
- desktop: filter sidebar plus catalog/detail content.

---

## 18. Catalog and release format

### 18.1 Generated catalog

`catalog.json` contains only approved public data and links. It must not contain private prompts, reviewer email addresses, unpublished materials, or local paths.

### 18.2 Release asset set

Recommended assets per material version:

```text
math1-qf-common-0001-v1.0.0-problem.pdf
math1-qf-common-0001-v1.0.0-answer-sheet.pdf
math1-qf-common-0001-v1.0.0-solution.pdf
math1-qf-common-0001-v1.0.0-source.zip
math1-qf-common-0001-v1.0.0-manifest.json
math1-qf-common-0001-v1.0.0-SHA256SUMS
```

### 18.3 Source bundle

The source ZIP includes:

- material and item manifests;
- TeX source;
- original owned/licensed assets;
- license texts;
- attribution file;
- build instructions;
- template identifier and version.

It excludes:

- private research files;
- model credentials;
- disallowed third-party source files;
- build caches;
- local environment files.

### 18.4 Immutability

Published release assets are immutable. Corrections create a new version. A withdrawn artifact remains in release history when legally possible but is prominently marked as withdrawn; rights violations may require removal.

---

## 19. CI/CD

### 19.1 Pull request workflows

#### Web checks

- pnpm frozen install;
- Biome check;
- TypeScript typecheck;
- unit/component tests;
- production build;
- optional Playwright smoke test.

#### Python checks

- `cd python && uv sync --locked --all-groups`;
- `ruff check` with the committed `python/ruff.toml`;
- `ruff format --check` with no CI-side modifications;
- `ty check` using the committed `[tool.ty]` configuration;
- pytest and coverage reporting;
- schema regeneration diff;
- CLI smoke tests;
- a configuration consistency check across `.python-version`, `requires-python`,
  Ruff `target-version`, and ty `python-version`.

Ruff and ty are required status checks. A material or Web-only pull request may use
path filtering to skip Python execution only when no Python source, Python config,
schema generator, Skill script, or workflow affecting Python has changed.

#### Material checks

- schema validation;
- curriculum-code resolution;
- provenance and license validation;
- mathematical automated tests;
- TeX compile;
- PDF inspection;
- thumbnail generation;
- catalog dry run.

#### Skill checks

- frontmatter and naming validation;
- broken reference detection;
- script lint/tests;
- evaluation fixtures;
- packaging test.

### 19.2 Security controls

- pin GitHub Actions by full commit SHA;
- least-privilege workflow permissions;
- no secrets in pull-request workflows from forks;
- shell escape disabled for TeX;
- external commands executed with argument arrays, not interpolated shell strings;
- dependency and secret scanning;
- generated archives inspected before upload;
- Skill scripts reviewed as executable code.

### 19.3 Main-branch workflow

On merge:

1. run full validation;
2. build public catalog;
3. build Manabi Library;
4. deploy preview or production site;
5. do not publish new release assets unless a release manifest is approved.

### 19.4 Release workflow

Triggered manually or by an approved release PR:

1. verify material states;
2. rebuild from clean checkout;
3. compare expected hashes where applicable;
4. package assets;
5. create signed/tagged release;
6. upload artifacts and checksums;
7. update catalog links;
8. deploy Library;
9. produce release summary.

---

## 20. Licensing, copyright, and provenance policy

### 20.1 Recommended licensing split

- **Software, CLI, schemas, scripts, TeX classes and reusable template code:** Apache License 2.0.
- **Original problem text, explanations, authored diagrams, curriculum annotations, and educational content:** Creative Commons Attribution 4.0 International.
- **Third-party components:** their original licenses, listed in `THIRD_PARTY_NOTICES.md` and per-material attribution files.

The final choice may be changed by an explicit ADR before the first public release. Multiple license files must make the boundary clear.

### 20.2 No-license warning

The project must not be made public without explicit licenses. Public visibility and GitHub forking do not by themselves grant broad reuse rights.

### 20.3 Common Test material

The repository shall not include:

- official question PDFs;
- OCR of official questions;
- copied questions, figures, conversations, or choices;
- derivative problem sets requiring an unapproved secondary-use license.

Allowed repository content includes:

- links and metadata;
- maintainer-authored structural analysis;
- learning-objective and item-feature tags;
- original problems created from independent briefs;
- short, lawful quotations when genuinely necessary and properly attributed.

If official question content is to be reused, the contributor must follow the National Center’s current application process and separately clear third-party rights.

### 20.4 Textbooks and commercial reference books

- textbook scans and OCR are not committed;
- private analysis data must be stored outside the repository;
- editorial intent documents may be linked and summarized within their terms;
- the project does not clone distinctive commercial page designs;
- problem text and explanation text are independently authored;
- trademarks and series names are not used as project categories or branding.

### 20.5 AI-assisted material

AI assistance does not eliminate infringement risk or guarantee copyright protection. Every AI-assisted material must be reviewed for:

- similarity;
- source leakage;
- unsupported attribution;
- factual and mathematical correctness;
- identifiable third-party expression;
- adequate human contribution and editorial accountability.

### 20.6 Takedown and correction process

`RIGHTS.md` or `SECURITY.md` shall provide a contact process. Reports are triaged quickly and may result in temporary unlisting, release withdrawal, attribution correction, or removal.

---

## 21. Privacy and data security

The MVP should collect no personal learner data.

- no accounts;
- no analytics requiring identifiers by default;
- no storage of prompts in the public catalog;
- no student work uploads;
- no API keys in the repository;
- no reviewer personal email in public metadata;
- contributor identities follow their chosen GitHub identities.

If analytics are added, use privacy-preserving, minimally invasive metrics and document them.

---

## 22. Testing strategy

### 22.1 Unit tests

- schema models;
- ID/path rules;
- curriculum resolver;
- TeX escaping and renderer helpers;
- provenance and license rules;
- catalog generation;
- mathematical verification utilities.

### 22.2 Integration tests

- material directory → approved PDF build;
- curriculum source snapshot → normalized records;
- review set → state transition decision;
- release manifest → ZIP and checksums;
- catalog JSON → Web page rendering.

### 22.3 Golden tests

Maintain a small set of intentionally diverse sample materials:

- Japanese text and ruby/annotations;
- equations and cases;
- table and graph;
- Common Test–style answer components;
- guided example page;
- multi-page solution.

Compare rendered page images with tolerance. Golden changes require explicit review.

### 22.4 Mutation and adversarial tests

Test failures such as:

- incorrect stated answer;
- two correct choices;
- missing domain restriction;
- nonexistent curriculum code;
- out-of-scope method;
- prohibited source text;
- missing attribution;
- TeX injection attempt;
- stale review against an older commit;
- asset path traversal.

### 22.5 Skill evaluations

Skills are evaluated separately from the Python core. Success means the agent follows the workflow, produces valid files, runs checks, and stops at required human gates.

---

## 23. Observability and auditability

Because the MVP is mostly a build system, observability is artifact-oriented.

Each build records:

- commit SHA;
- material version;
- template version;
- curriculum snapshot;
- Python and package lock hash;
- TeX environment identifier;
- command invocation;
- warnings and failures;
- output hashes.

CI summaries should link directly to failing material paths and review records.

---

## 24. Roadmap

The roadmap is milestone-based rather than date-based. A phase begins when its dependencies are complete and ends only when its exit criteria are satisfied.

### Phase 0 — Repository foundation

**Objective:** establish the legal, technical, and contribution baseline.

Deliverables:

- initialize from `nishide-dev/react-template` under `web/`;
- create the Python uv project under `python/`;
- establish directory structure;
- add code/content licenses and notices;
- add contribution, security, governance, AI usage, and editorial policies;
- configure pnpm, uv, Biome, tests, and GitHub Actions;
- add `python/ruff.toml` with the reviewed initial lint/format rule set;
- configure `ty` in `python/pyproject.toml` and make `ty check` a required CI gate;
- add root pre-commit hooks for repository hygiene, Ruff, formatting, and Markdown;
- create initial ADRs;
- implement `manabi doctor` and a minimal CLI shell.

Exit criteria:

- clean clone can run Web and Python checks;
- `ruff check`, `ruff format --check`, `ty check`, and pytest pass with zero
  unsuppressed diagnostics;
- CI passes on a trivial sample;
- licenses are unambiguous;
- no LangChain, LangGraph, Next.js, or backend dependency exists.

### Phase 1 — One complete vertical slice

**Objective:** prove that one original Mathematics I material can travel from source to Library.

Scope:

- Mathematics I;
- quadratic functions;
- one Common Test–style problem;
- one guided-example material.

Deliverables:

- initial manifest and item schemas;
- minimal curriculum records for the chosen unit;
- `common-test` and `guided-example` templates;
- TeX build command;
- material validator;
- one independent mathematical verification path;
- manual review records;
- generated catalog JSON;
- Library catalog and detail pages;
- PDF preview and downloads.

Exit criteria:

- both sample materials meet Definition of Done;
- PDFs rebuild in CI from a clean checkout;
- public pages show curriculum, review, provenance, and license information;
- release assets can be produced without manual file editing.

### Phase 2 — Curriculum foundation

**Objective:** make official scope data a maintained subsystem rather than ad hoc notes.

Deliverables:

- source manifest system;
- ingestion of high-school code table `84V10`;
- normalized Mathematics I and Mathematics A hierarchy;
- subject explanation annotations for selected units;
- curriculum query and diff commands;
- source/version/checksum tracking;
- curriculum review guide.

Exit criteria:

- every published mathematics material resolves to existing curriculum records;
- updating a snapshot identifies affected materials;
- official text, maintainer interpretation, and uncertainty are distinguishable.

### Phase 3 — Core Agent Skills

**Objective:** make the authoring process repeatable across compatible agents.

Deliverables:

- `resolving-curriculum`;
- `authoring-math-items`;
- `verifying-mathematics`;
- `reviewing-materials`;
- `publishing-tex`;
- Skill validator and package command;
- at least three evaluation cases per Skill;
- installation guide for project-local agent environments.

Exit criteria:

- an agent can create a valid draft from a brief;
- the authoring Skill cannot self-approve;
- verifier findings are recorded structurally;
- publication Skill blocks stale or missing reviews.

### Phase 4 — Review and verification depth

**Objective:** improve correctness beyond basic schema and compile checks.

Deliverables:

- SymPy verification adapters for supported item classes;
- numeric and property-test helpers;
- choice-uniqueness checker;
- review severity/state engine;
- independent-solution workflow;
- figure/data consistency checks;
- visual regression fixtures;
- editorial and accessibility rubrics.

Exit criteria:

- seeded mathematical defects are caught by tests;
- unsupported verification cases are explicitly escalated;
- review state cannot be forged by editing a single status field.

### Phase 5 — Manabi Library MVP release

**Objective:** provide a polished public catalog.

Deliverables:

- home, catalog, detail, curriculum, policy, and status pages;
- URL-shareable filters;
- PDF.js viewer;
- accessible responsive layout;
- release download links;
- version history;
- issue-report links;
- static deployment workflow;
- custom domain decision.

Exit criteria:

- all public content comes from generated approved catalog data;
- site works without a backend;
- problem PDF remains downloadable if viewer initialization fails;
- Lighthouse/accessibility checks meet agreed thresholds.

### Phase 6 — Content scaling

**Objective:** expand from a demonstration into a useful library.

Deliverables:

- broader Mathematics I/A coverage;
- workbook assembly;
- difficulty calibration notes;
- template component library;
- contributor onboarding examples;
- release collections by course/unit;
- content coverage dashboard.

Exit criteria:

- at least one coherent unit collection can be used as a small workbook;
- review workload and defect rates are measurable;
- multiple contributors can author without direct maintainer intervention in every file operation.

### Phase 7 — Additional subjects and formats

**Objective:** generalize carefully after mathematics proves the architecture.

Potential work:

- Information I;
- sciences;
- English or Japanese reading formats;
- source-data citation components;
- rubrics and constructed-response formats;
- Typst or HTML output experiments.

Each new subject requires subject-specific scope, authoring, and review Skills. Shared infrastructure alone is not sufficient.

### Phase 8 — Optional online authoring service

**Objective:** add dynamic services only when the static workflow is mature.

Potential capabilities:

- authenticated draft workspace;
- job queue for generation and TeX builds;
- private materials;
- online review UI;
- provider adapters;
- audit log and role-based permissions.

This phase may introduce an API service. It must preserve the file-based canonical format and never make the Web database the sole source of truth.

---

## 25. Initial GitHub milestone backlog

### Milestone: Foundation

1. Initialize repository structure.
2. Import React template into `web/` without preserving template Git history.
3. Initialize `python/` with uv.
4. Define code/content licensing boundary.
5. Add base policies and contribution documents.
6. Add root task aliases or a Justfile.
7. Configure CI with least-privilege permissions.
8. Add `manabi doctor`.
9. Add first ADRs.

### Milestone: Data model

10. Define `MaterialManifest` Pydantic model.
11. Define `ItemSpec` Pydantic model.
12. Define `ReviewRecord` and `ProvenanceRecord`.
13. Generate JSON Schema 2020-12 files.
14. Implement material path/ID validation.
15. Add example valid and invalid fixtures.

### Milestone: TeX vertical slice

16. Create shared LuaLaTeX class/package.
17. Implement guided-example template.
18. Implement Common Test–style template.
19. Build PDF and capture logs.
20. Generate thumbnails and metadata.
21. Create source bundle and checksums.

### Milestone: Curriculum

22. Create source manifest schema.
23. Add `84V10` ingestion prototype.
24. Normalize selected Mathematics I records.
25. Implement curriculum query.
26. Link first material to official codes.

### Milestone: Library

27. Build catalog JSON generator.
28. Implement material catalog.
29. Implement material detail page.
30. Integrate PDF.js.
31. Add curriculum map.
32. Deploy static preview.

### Milestone: Skills

33. Add Skill validation command.
34. Implement curriculum Skill.
35. Implement authoring Skill.
36. Implement mathematics verification Skill.
37. Implement review Skill.
38. Implement TeX publication Skill.
39. Add Skill evaluations.

---

## 26. Initial architecture decision records

### ADR-001 — React + Vite instead of Next.js or vinext

Status: accepted for MVP.

Reason: no current requirement for SSR, RSC, Server Actions, or framework-specific server features. Static deployment is sufficient and simpler.

### ADR-002 — Single uv project before uv workspace

Status: accepted.

Reason: only one Python application/library boundary currently exists. Workspace migration remains straightforward when independent packages emerge.

### ADR-003 — No LangChain or LangGraph dependency

Status: accepted.

Reason: the workflow is file- and command-oriented. Core correctness should not depend on a model orchestration abstraction.

### ADR-004 — Human approval is mandatory

Status: accepted.

Reason: automated and AI-assisted checks are incomplete for curriculum interpretation, pedagogy, rights, and complex mathematics.

### ADR-005 — Generated PDFs are release assets

Status: accepted.

Reason: avoid repository bloat and maintain immutable distributable versions.

### ADR-006 — Official past questions are references, not repository content

Status: accepted.

Reason: secondary use is subject to current rights and application requirements, including third-party rights.

### ADR-007 — LuaLaTeX is the default renderer

Status: proposed, to be validated in the vertical slice.

Reason: modern Unicode/Japanese support and flexible programmatic document design.

---

## 27. Risks and mitigations

### Curriculum interpretation errors

Mitigation:

- retain evidence and uncertainty;
- require human curriculum review;
- version snapshots;
- never infer scope solely from model memory.

### Mathematically incorrect AI output

Mitigation:

- independent solution;
- symbolic/numeric checks;
- adversarial fixtures;
- human approval.

### Accidental copying or excessive similarity

Mitigation:

- originality-first briefs;
- no source scans in repository;
- provenance review;
- similarity checks and contributor attestations;
- clear takedown process.

### TeX security and build instability

Mitigation:

- no shell escape;
- isolated CI;
- pinned environment;
- restricted custom TeX;
- reproducible builds.

### Agent Skill prompt bloat

Mitigation:

- concise SKILL.md files;
- progressive references;
- subject-specific Skills;
- evaluation and profiling.

### Review bottleneck

Mitigation:

- structured rubrics;
- separate review specialties;
- automated pre-checks;
- small coherent batches;
- transparent reviewer workload.

### Framework churn

Mitigation:

- keep material data and Python tools independent from the Web framework;
- use static interchange files;
- document ADRs;
- avoid unnecessary libraries.

### Public misuse of answer files

Mitigation:

- clearly separate learner and instructor artifacts;
- accept that public repositories cannot provide genuine teacher-only secrecy;
- add authenticated distribution only in a later service if required.

---

## 28. Success metrics

### Reliability

- 100% of published materials build from a clean CI checkout.
- 100% of published materials have current required reviews.
- zero known critical or high-severity defects remain open in published current versions.
- artifact checksums and source commit are available for every release.

### Curriculum coverage

- percentage of normalized curriculum records with human-reviewed annotations;
- number of published materials per unit and objective;
- number of stale materials after curriculum snapshot changes.

### Quality

- defect rate found after publication;
- proportion of seeded defects caught by automated checks;
- review turnaround by review type;
- learner/teacher issue reports by category.

### Usability

- catalog search success;
- PDF preview success and download fallback rate;
- accessibility test pass rate;
- build and contribution setup success from a clean clone.

### Community

- number of external contributors;
- number of reviewed material PRs;
- contributor retention;
- reuse or adaptations that preserve attribution.

Metrics must not incentivize raw problem count over correctness.

---

## 29. Open questions

These questions should be resolved through ADRs before or during the vertical slice:

1. Apache-2.0 versus MIT for code and TeX packages.
2. Exact LuaLaTeX font set and container image.
3. React Router versus a file-based lightweight router.
4. GitHub Pages versus Cloudflare Pages as the first custom-domain host.
5. Whether solution PDFs are linked directly from the same learner-facing page.
6. Whether structured ItemSpec is mandatory for guided examples or only Common Test–style items.
7. Similarity-check implementation and acceptable evidence.
8. Public disclosure detail for model names and prompts.
9. Minimum human reviewer qualifications for subject-specific approval.
10. Whether curriculum annotations themselves use CC BY 4.0 or CC BY-SA 4.0.

---

## 30. Immediate next actions

The recommended implementation sequence is:

1. Create the `manabi-forge` repository.
2. Place the React template under `web/`.
3. Initialize a single uv project under `python/`.
4. Add `ruff`, `ty`, pytest, coverage, and pre-commit to the uv-managed development
   dependencies; commit `python/ruff.toml` and `[tool.ty]` configuration.
5. Add licenses and policy files before publishing the repository.
6. Add ADR-001 through ADR-006.
7. Implement Pydantic models for material, item, review, and provenance.
8. Build one manually authored guided-example PDF using LuaLaTeX.
9. Build one original Common Test–style quadratic-functions problem.
10. Add the first curriculum snapshot and code links.
11. Implement the minimal catalog generator and Manabi Library detail page.
12. Only then package the first five Agent Skills around the proven commands.

The first milestone should prove the complete path, not maximize feature count.

---

## 31. Reference links

### Agent Skills

- [Agent Skills overview — Claude Platform Docs](https://platform.claude.com/docs/ja/agents-and-tools/agent-skills/overview)
- [Skill authoring best practices — Claude Platform Docs](https://platform.claude.com/docs/ja/agents-and-tools/agent-skills/best-practices)
- [Agent Skills specification](https://agentskills.io/specification)
- [Anthropic public Skills repository](https://github.com/anthropics/skills)
- [Using Agent Skills with the API](https://platform.claude.com/docs/ja/build-with-claude/skills-guide)

### Python and schemas

- [uv projects](https://docs.astral.sh/uv/concepts/projects/)
- [uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/)
- [Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
- [SymPy solving guide](https://docs.sympy.org/latest/guides/solving/index.html)
- [Ruff configuration](https://docs.astral.sh/ruff/configuration/)
- [ty configuration](https://docs.astral.sh/ty/configuration/)
- [ML Research Template — Ruff, ty, uv, and CI reference](https://github.com/nishide-dev/ml-research-template)

### Web and PDF

- [Vite static deployment guide](https://vite.dev/guide/static-deploy.html)
- [PDF.js Getting Started](https://mozilla.github.io/pdf.js/getting_started/)
- [PDF.js API](https://mozilla.github.io/pdf.js/api/)
- [React template used as the starting point](https://github.com/nishide-dev/react-template)

### Japanese curriculum and assessment

- [MEXT: 2017/2018/2019 revised Courses of Study and explanations](https://www.mext.go.jp/a_menu/shotou/new-cs/1384661.htm)
- [MEXT: High School Courses of Study explanatory documents](https://www.mext.go.jp/a_menu/shotou/new-cs/1407074.htm)
- [MEXT education data standards and curriculum codes](https://www.mext.go.jp/a_menu/other/data_00001.htm)
- [MEXT textbook catalog](https://www.mext.go.jp/a_menu/shotou/kyoukasho/mext_00008.html)
- [MEXT textbook editorial intent documents](https://www.mext.go.jp/a_menu/shotou/kyoukasho/tenji/index.htm)
- [National Center: past three years of Common Test questions](https://www.dnc.ac.jp/kyotsu/kakomondai/)
- [National Center: Common Test information](https://www.dnc.ac.jp/kyotsu/index.html/)
- [National Center: current-year test information and question-creation policy](https://www.dnc.ac.jp/kyotsu/kako_shiken_jouhou/r8/)
- [National Center: question evaluation and analysis reports](https://www.dnc.ac.jp/kyotsu/hyouka/index.html)

### Rights and licensing

- [National Center website and test-question secondary-use policy](https://www.dnc.ac.jp/about_site.html)
- [Agency for Cultural Affairs: AI and Copyright](https://www.bunka.go.jp/seisaku/chosakuken/aiandcopyright.html)
- [GitHub: Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
- [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/deed.ja)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

---

## Appendix A — Example material directory

```text
materials/mathematics/math-i/quadratic-functions/math1-qf-common-0001/
├── material.yaml
├── item.yaml
├── source/
│   ├── problem.tex
│   ├── solution.tex
│   └── answer-sheet.tex
├── assets/
│   ├── graph.tikz
│   └── graph-description.txt
├── reviews/
│   ├── mathematics.yaml
│   ├── curriculum.yaml
│   ├── editorial.yaml
│   ├── visual.yaml
│   └── rights.yaml
├── provenance.yaml
├── ATTRIBUTION.md
└── README.md
```

## Appendix B — Example release manifest

```json
{
  "$schema": "https://example.invalid/manabi/release.schema.json",
  "materialId": "math1-qf-common-0001",
  "materialVersion": "1.0.0",
  "sourceCommit": "0123456789abcdef",
  "curriculumSnapshot": "mext-84V10-2026-08",
  "template": {
    "id": "common-test",
    "version": "1.0.0"
  },
  "reviews": {
    "mathematics": "passed",
    "curriculum": "passed",
    "editorial": "passed",
    "visual": "passed",
    "rights": "passed"
  },
  "artifacts": [
    {
      "kind": "problem-pdf",
      "filename": "math1-qf-common-0001-v1.0.0-problem.pdf",
      "sha256": "..."
    }
  ]
}
```

## Appendix C — Example Skill skeleton

```markdown
---
name: verifying-mathematics
description: Independently verifies mathematics materials, checks answers, domains, edge cases, and choice uniqueness, and records structured findings. Use after a draft ItemSpec exists and before curriculum or publication approval.
---

# Verifying mathematics

## Required inputs

- Material directory
- Valid ItemSpec
- Target curriculum brief

## Workflow

1. Validate the material structure with `manabi material validate`.
2. Solve the problem independently before reading the proposed solution in detail.
3. Compare the independent result with the stated answer.
4. Run supported symbolic and numeric checks.
5. Inspect domain restrictions, boundaries, units, and all answer choices.
6. Record a review file; do not edit the authoring files during formal review.
7. Return `passed`, `changes-requested`, or `escalated` with evidence.

## Publication rule

Never mark the material approved or published. Human approval is required.
```

## Appendix D — Initial Python quality configuration

This appendix is normative for Phase 0, except for the selected Python version and
individual Ruff ignores, which must be finalized in the bootstrap pull request.
It is based on the configuration style demonstrated by
[`nishide-dev/ml-research-template`](https://github.com/nishide-dev/ml-research-template)
and simplified for Manabi Forge's non-ML workload.

### D.1 `python/pyproject.toml` excerpt

```toml
[project]
name = "manabi-forge"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2",
  "pyyaml",
  "typer",
]

[dependency-groups]
dev = [
  "pre-commit",
  "pytest>=8",
  "pytest-cov",
  "ruff",
  "ty",
]

[tool.ty]

[tool.ty.environment]
python-version = "3.12"

[tool.ty.terminal]
output-format = "full"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
  "--strict-config",
  "--strict-markers",
  "--showlocals",
]

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
show_missing = true
skip_covered = false
```

### D.2 `python/ruff.toml` excerpt

```toml
exclude = [
  ".git",
  ".pytest_cache",
  ".ruff_cache",
  ".venv",
  "build",
  "dist",
  "node_modules",
]
line-length = 88
indent-width = 4
target-version = "py312"

[lint]
select = ["ALL"]
ignore = [
  "COM812", # conflicts with the formatter
  "D203",   # conflicts with D211
  "D213",   # conflicts with D212
  "E501",   # formatter owns physical line wrapping
  "ISC001", # conflicts with the formatter
]
fixable = ["ALL"]
unfixable = []
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[lint.per-file-ignores]
"tests/**/*.py" = [
  "ANN001",
  "ANN201",
  "D",
  "S101",
]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

The bootstrap pull request must run this draft against the actual codebase and add
only those further exceptions that have a documented project-level rationale.

### D.3 Root task aliases

The root may expose convenience commands without introducing Turborepo:

```json
{
  "scripts": {
    "lint:web": "pnpm --dir web lint",
    "test:web": "pnpm --dir web test",
    "build:web": "pnpm --dir web build",
    "lint:py": "cd python && uv run ruff check --config ruff.toml src tests ../scripts",
    "format:py:check": "cd python && uv run ruff format --check --config ruff.toml src tests ../scripts",
    "typecheck:py": "cd python && uv run ty check",
    "test:py": "cd python && uv run pytest"
  }
}
```

The canonical source of dependency truth remains `python/pyproject.toml` and
`python/uv.lock`; root aliases are ergonomic wrappers only.


