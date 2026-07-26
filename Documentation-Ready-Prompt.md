# Documentation Ready Prompt (Portfolio-style)

> Copy everything below the line into Cursor AI on **any project**.  
> Replace the placeholders in `{{...}}` first.

---

## PROMPT (copy from here)

You are documenting this entire application for a portfolio docs site (Trends WD style).

### Target folder (REQUIRED)
Create / update **all** documentation only inside:

```text
{{TARGET_FOLDER}}
```

Example: `Documentation/` or `My-App-Docs/`

Do **not** scatter docs across the repo. Everything lives in that folder.

---

### Goal
Scan the **whole codebase** (routes, pages, layouts, modals, settings, roles, APIs if needed) and produce **complete English documentation**:

1. **One markdown file per page / major screen**
2. **Step-by-step** user flows
3. **Full per-page details** (layout, fields, buttons, tables, modals, permissions, errors)
4. Wire **screenshots** from `images/` into the matching page guides
5. Keep **Version** + **Changelog** always up to date for future changes

---

### Required folder structure

```text
{{TARGET_FOLDER}}/
├── index.md                 # Docs home / index
├── README.md                # Short helper for humans copying this pack
├── APP-VERSION.md           # Current version + release notes summary
├── CHANGELOG.md             # Date-wise history (newest first)
├── version.json             # Optional mirror: { name, version, released }
├── _meta/
│   └── navigation.json      # Sidebar tree for the portfolio docs viewer
├── images/                  # Screenshots ONLY (png/jpg/webp)
│   ├── 01-login.png
│   ├── 02-dashboard.png
│   └── ...
├── 00-getting-started.md    # Optional: install / env / first login
├── 01-<page>.md             # Flat numbered guides (preferred)
├── 02-<page>.md
└── ...
```

**Preferred style (like Dev Log Verse / Complaint CMS):**
- Flat root guides: `01-login.md`, `02-dashboard.md`, …
- Screenshots: `./images/NN-name.png`
- No giant single “pages guide” file

If the app is huge, you may use `pages/` subfolder — but keep numbering consistent and update `navigation.json` paths accordingly.

---

### `_meta/navigation.json` contract

Must include:

```json
{
  "site": "{{PRODUCT_NAME}} Documentation",
  "base_url": "https://trendswd.com/web-applications/{{SLUG}}/doc",
  "version": "{{VERSION}}",
  "version_date": "{{YYYY-MM-DD}}",
  "navigation": [
    {
      "title": "Home",
      "path": "/docs",
      "file": "index.md"
    },
    {
      "title": "Getting started",
      "children": [
        { "title": "Version", "path": "/docs/APP-VERSION", "file": "APP-VERSION.md" },
        { "title": "Changelog", "path": "/docs/CHANGELOG", "file": "CHANGELOG.md" }
      ]
    },
    {
      "title": "Pages",
      "children": []
    }
  ]
}
```

Rules for nav paths:
- Use `/docs/...` paths (portfolio remaps `/docs` → app doc base)
- Every real guide file must appear in `navigation`
- Titles must be human-readable (not locale keys)

---

### `index.md` requirements
- Product name + short description
- Version table (`Version`, `Released`)
- Live demo URL + default/demo login if any
- “What’s new” bullets for current version (if applicable)
- Full documentation index (links to every guide)
- Simple app map (ASCII routes tree)

---

### Every page guide (`01-…md`, etc.) MUST include

1. **Title** (`# Page Name`)
2. **Version** line matching current app version
3. **Route** (e.g. `/complaints`)
4. **Who can access** (roles / guests)
5. **Screenshot(s)** using relative paths:
   ```markdown
   ![Login screen](./images/01-login.png)
   ```
6. **What this page does** (1–3 sentences)
7. **Layout at a glance** (table or bullets: sidebar, header, main, modals)
8. **Steps** — numbered, exact UI labels (buttons, fields, menus)
9. **Sub-details** where relevant:
   - Form fields (label, type, required, validation)
   - Tables (columns, filters, row actions)
   - Modals / drawers (open/close, fields, save/cancel)
   - Permissions (View / Edit / Delete)
10. **Errors & edge cases**
11. **Related links** to other guides in the same folder

Write for a **new user**, not a developer dump. Be concrete and sequential.

---

### Images folder rules
- Put screenshots only in `{{TARGET_FOLDER}}/images/`
- Naming: `NN-short-kebab-name.png` (e.g. `01-login.png`, `05-complaints-filter.png`)
- If images **already exist**, map them into the correct page guides (do not invent fake image files)
- If images are **missing**, still write the markdown with the correct `![...](./images/...)` placeholders and list missing filenames at the end of `README.md` under “Screenshots still needed”
- Prefer Demo Mode / fictional data in screenshots (no personal live data)

---

### `APP-VERSION.md` requirements
- Product name
- Current version + release date
- Short release notes for this version
- Link to `CHANGELOG.md`
- Keep it short (no long “how to bump” essays unless useful)

---

### `CHANGELOG.md` requirements
- Newest date section first: `## YYYY-MM-DD`
- Under each date, feature subsections with plain-English bullets
- Link to related guides when useful
- **Do not** put long maintainer instructions at the top (no “when you ship a release, bump package.json…” walls of text)
- Title only: `# Changelog` then sections

When documenting an existing project for the first time, reconstruct changelog from:
- git history / CHANGELOG if present
- feature set visible in code
- current version from `package.json` / app config

---

### Version sync (keep forever)
Whenever docs are generated or updated, keep these **equal**:

| Place | Field |
|--------|--------|
| `_meta/navigation.json` | `version`, `version_date` |
| `APP-VERSION.md` | Current version / Released |
| `index.md` | Version table |
| `version.json` | `version`, `released` |
| Page guides | `**Version:** x.y.z` near the top (optional but preferred) |
| App code if present | `APP_VERSION` / `package.json` (mention in docs; don’t break the app) |

---

### Language & quality
- Documentation language: **English**
- Exact UI strings as shown in the app
- No filler / no “as an AI” commentary
- Cross-link related pages
- After writing, self-check:
  - [ ] Every route/page has a guide
  - [ ] Every nav item file exists
  - [ ] Every screenshot path resolves or is listed as missing
  - [ ] Version matches across meta / APP-VERSION / index / changelog
  - [ ] Changelog has at least one dated section for the current release

---

### Output
1. Create/update files only under `{{TARGET_FOLDER}}`
2. Print a short summary:
   - version
   - list of guide files created
   - images wired vs missing
   - navigation groups

### Placeholders to fill before running
- `{{TARGET_FOLDER}}` → e.g. `Documentation`
- `{{PRODUCT_NAME}}` → e.g. `Dev Log Verse`
- `{{SLUG}}` → e.g. `dev-log-verse`
- `{{VERSION}}` → e.g. `1.0.0`
- `{{YYYY-MM-DD}}` → release date

END OF PROMPT

---

## Follow-up prompt (when you change the app later)

Use this in the same project after features change:

```text
Update documentation in {{TARGET_FOLDER}} for the latest code changes.

1. Diff the app vs existing guides — update only affected pages.
2. Add/adjust screenshots under {{TARGET_FOLDER}}/images/ and wire them into the guides.
3. Bump version if this is a release:
   - _meta/navigation.json (version + version_date)
   - APP-VERSION.md
   - index.md version table
   - version.json
4. Add a NEW section at the TOP of CHANGELOG.md for today’s date with what changed.
5. Keep English, step-by-step style, and working relative image links.
```
