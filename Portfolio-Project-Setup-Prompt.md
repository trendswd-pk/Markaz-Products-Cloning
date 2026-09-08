# Portfolio Project Setup — Master Prompt (Demo → Screenshots → Docs → Rules → README)

> **Kaise use karein:** Is file ka **CONFIG** section pehle bharo, phir **MASTER PROMPT** wala hissa Cursor me naye project par paste karo.  
> Cursor **Phase 1 → 2 → 3 → 4 → 5 → 6** order follow karega — pehle `demo-mode`, phir docs skeleton, screenshots, full docs, Cursor rules, phir root **`README.md`** (professional + screenshots from `Documentation/images/`).

**Short Urdu flow:**
```text
1) demo-mode/ — professional offline clone + demo.json (LIVE_DEMO_URL)
   + Trends WD favicon: https://www.trendswd.com/favicon.png
   + demo-mode/.gitignore (root jaisi ignores — Phase 1 me hi)
2) Documentation/ skeleton (version + CHANGELOG + nav)
3) Playwright screenshots → Documentation/images/ ONLY
4) English client-facing docs — har screenshot ./images/ se link
5) .cursor/rules/ — har change pe CHANGELOG + daily version bump (bar bar na batana pade)
6) Root README.md — professional rewrite; zaroori images Documentation/images/ se embed

⚠️ HARD: `demo-mode/` ko **production / root deploy build se hamesha exclude** rakho — warna main product deploy toot / ruk jati hai.
```

---

## CONFIG — pehle yeh values bharo (paste se pehle)

```text
PRODUCT_NAME     = My App Name
APP_SLUG         = my-app-slug
CATEGORY_TYPE    = web-app
VERSION          = 1.0.0
RELEASE_DATE     = 2026-09-07

# Live / hosted demo URL (Vercel etc.) — abhi empty chhod sakte ho;
# baad me deploy ke baad yahi value demo-mode/demo.json me set ho jayegi.
LIVE_DEMO_URL    = https://your-demo.vercel.app

# Local demo while capturing screenshots (auto-detect OK if empty)
LOCAL_DEMO_URL   = http://localhost:3000

DEMO_FOLDER      = demo-mode
DOCS_FOLDER      = Documentation
SCREENSHOT_DIR   = Documentation/images

# Demo login (capture + docs) — show on Demo login UI only, NEVER in demo.json
DEMO_ADMIN_EMAIL = admin@admin.com
DEMO_ADMIN_PASS  = admin123

# Trends WD brand assets (live — download from here, do not invent new logos)
BRAND_LOGO_URL     = https://www.trendswd.com/logo.png
BRAND_FAVICON_URL  = https://www.trendswd.com/favicon.png
BRAND_ICON_URL     = https://www.trendswd.com/icon.png
```

`CATEGORY_TYPE` examples (navbar / `/our-projects/[category]`):
- `web-app` → route `/our-projects/web-apps` (label: Web Applications)
- `shopify-theme` → `/our-projects/shopify-themes`
- `mobile-app` → `/our-projects/mobile-apps`
- `hide` → product portfolio se hide (client ko dikhega nahi)

### Trends WD live brand assets (source of truth)

| Asset | Live URL |
|-------|----------|
| Logo (navbar / footer) | `https://www.trendswd.com/logo.png` |
| Favicon (browser tab) | `https://www.trendswd.com/favicon.png` |
| App icon (Next `app/icon.png` / apple) | `https://www.trendswd.com/icon.png` |

Canonical site: `https://trendswd.com/` (redirects to `www`). Always download from these live URLs — do not design a new logo for Demo Mode.

---

## MASTER PROMPT (yahan se copy karo → Cursor)

You are setting up this repository for the **Trends WD portfolio pipeline**.

Work in **strict order**. Do not skip ahead. Do not rewrite the production app at repo root unless a tiny shared fix is required. Finish each phase’s acceptance checklist before starting the next.

**Client-facing quality is non-negotiable.** Demo Mode, screenshots, and Documentation are shown to real clients on the Trends WD portfolio. Everything must look **professional, polished, and trustworthy** — never unfinished, slangy, joke-filled, or internally messy.

Use these values from the human’s CONFIG (or detect sensible defaults from `package.json` / README if a field was left as placeholder):

| Key | Value |
|-----|--------|
| Product | `{{PRODUCT_NAME}}` |
| Slug | `{{APP_SLUG}}` |
| Category | `{{CATEGORY_TYPE}}` |
| Version | `{{VERSION}}` |
| Release date | `{{RELEASE_DATE}}` |
| Live demo URL | `{{LIVE_DEMO_URL}}` |
| Local demo URL | `{{LOCAL_DEMO_URL}}` |
| Demo folder | `{{DEMO_FOLDER}}` (= `demo-mode`) |
| Docs folder | `{{DOCS_FOLDER}}` (= `Documentation`) |
| Screenshots | `{{SCREENSHOT_DIR}}` (= `Documentation/images`) |
| Brand favicon | `https://www.trendswd.com/favicon.png` |
| Brand logo | `https://www.trendswd.com/logo.png` |
| Brand icon | `https://www.trendswd.com/icon.png` |

---

# GLOBAL — Professional client standards (ALL phases)

Apply these in Demo Mode, screenshots, docs, changelog, and Cursor rules.

### Tone & language
- Documentation language: **clear professional English** (UI labels match the app exactly).
- Write for a **business client / end user**, not for developers debugging the repo.
- No Hinglish, memes, jokes, emoji spam, or “lorem ipsum” left in visible UI or docs.
- No internal jargon that confuses clients: avoid “GitHub type”, “repo”, “hack”, “WIP dump”, “temp seed”, “TODO fill later” in client-visible copy.
- No maintainer rant / process dump at the top of `CHANGELOG.md` or guide pages.

### What MUST NOT appear in docs or demo UI
| Forbidden | Why |
|-----------|-----|
| Real customer PII, real emails of clients, real phone numbers | Privacy / trust |
| Production secrets, API keys, tokens, `.env` values | Security |
| Joke names (`test123`, `asdf`, `foo bar`, `xxx`, cartoon insults) | Unprofessional |
| Broken empty states on every page (“No data”, blank tables) when a seeded demo should look alive | Looks unfinished |
| Fake screenshot filenames that do not exist under `Documentation/images/` | Broken docs |
| Passwords inside `demo.json` or public markdown tables that look like a leak dump | Wrong place / scary |
| Screenshots saved only under `demo-mode/screenshots/` without copies in `Documentation/images/` | Portfolio docs cannot link them |

### What SHOULD appear
- Realistic but **fictional** business data (neutral company names, plausible dates, clean currency/IDs).
- Consistent product naming (`{{PRODUCT_NAME}}`) everywhere.
- Clear Demo Mode banner so nobody confuses demo with live production.
- Every guide screenshot linked as `![Description](./images/NN-name.png)` from `Documentation/`.
- Version + date kept in sync across `version.json`, `APP-VERSION.md`, `CHANGELOG.md`, `_meta/navigation.json`, and `index.md`.

### Screenshot + docs link rule (permanent)
1. Canonical PNG location: **`Documentation/images/` only**.
2. Guides under `Documentation/*.md` MUST use relative links: `./images/...`.
3. Optional mirror under `demo-mode/screenshots/` is OK for capture convenience — but docs never link there.
4. After UI changes that affect screens, re-capture and update the matching guide + `SCREENSHOT-INDEX.md`.

### HARD — `demo-mode/` must NEVER break production deploy

**Problem:** Agar `demo-mode/` root production build me include ho jaye (Next.js / TypeScript / ESLint / Vercel), main product deploy fail / stop ho jati hai — phir human ko manually exclude karwana padta hai. Yeh **forbidden**.

**Rule (all phases, especially Phase 1):** Treat `demo-mode/` as a **separate app**. Root `npm run build` / Vercel production build for the **main product** must ignore it completely.

While working from this prompt, Cursor **must** wire excludes before considering Phase 1 done — do not leave this for the human.

| Layer | What to do (typical Next.js / Node monorepo-style product) |
|-------|--------------------------------------------------------------|
| Own app | `demo-mode/` has its **own** `package.json`; install/run only via `cd demo-mode` |
| TypeScript | Root `tsconfig.json` → `"exclude": ["demo-mode", "Documentation", ...]` (keep existing excludes) |
| Next.js | Do **not** put demo routes under root `app/` or `pages/`. Do **not** import from `demo-mode/` in production code |
| ESLint | Root eslint ignore: `demo-mode/**` (e.g. `.eslintignore` or `ignores` in flat config) |
| Vercel (main product) | Root `vercel.json` or project settings: ensure build command stays root-only; add `.vercelignore` entries for `demo-mode` if the platform still scans it |
| Output / tooling | Root `next.config` must not `transpilePackages` / webpack-include `demo-mode` |
| CI | Root build scripts must not `turbo`/`npm run build` inside `demo-mode` unless a **separate** demo deploy job |

**Demo deploy (separate):** Live demo is deployed as its **own** Vercel/project from `demo-mode/` (Root Directory = `demo-mode`), then URL goes into `demo-mode/demo.json` → `live_demo_url`. Never merge demo into main product build to “save a project”.

**Verify before finishing Phase 1:**
```bash
# From repo root — must succeed WITHOUT compiling demo-mode
npm run build
```
If build tries to typecheck or bundle files under `demo-mode/`, fix excludes immediately.

---

# PHASE 1 — Demo Mode (`demo-mode/`)

### Goal
Build a **standalone, professional offline demo** of this app so clients can try the full UI without production backend, secrets, DB, or paid APIs.

### Target
Create everything under:

```text
demo-mode/
```

Production root stays untouched.

### Required outputs in `demo-mode/`

```text
demo-mode/
├── demo.json                 # REQUIRED for portfolio Live Demo button
├── README.md                 # run steps + accounts (maintainer-facing OK)
├── .gitignore                # REQUIRED — mirror root ignores (node_modules, .next, .env*, …)
├── capture-docs.js           # created/updated in Phase 3 (placeholder OK in Phase 1)
├── public/favicon.png        # REQUIRED — Trends WD favicon
├── (app source / package.json / …)
└── screenshots/              # optional working copy; FINAL PNGs = Documentation/images
```

### Branding assets (REQUIRED — use Trends WD live files only)

Download brand files from the live site (do **not** invent / redraw logos):

| Asset | Live URL | Save as (typical) |
|-------|----------|-------------------|
| **Favicon** | `https://www.trendswd.com/favicon.png` | `demo-mode/public/favicon.png` (and/or `app/icon.png`) |
| Logo | `https://www.trendswd.com/logo.png` | only if needed (see rule below) |
| Icon | `https://www.trendswd.com/icon.png` | optional alias / Next metadata icon |

**Branding rule:**
- **Default = favicon only.** If the demo has a single brand slot, set **only the favicon**.
- Use **`logo.png`** only when the UI already has a dedicated navbar/footer wordmark `<img>`.
- Prefer local copies so offline demo still shows the icon.

Example (Next.js App Router metadata):

```ts
export const metadata = {
  icons: {
    icon: "/favicon.png",
    apple: "/favicon.png",
  },
};
```

```bash
mkdir -p demo-mode/public
curl -fsSL -o demo-mode/public/favicon.png https://www.trendswd.com/favicon.png
# ONLY if navbar/footer needs the wide logo:
# curl -fsSL -o demo-mode/public/logo.png https://www.trendswd.com/logo.png
```

### `demo.json` contract (REQUIRED — exact shape)

```json
{
  "live_demo_url": "{{LIVE_DEMO_URL}}",
  "type": "{{CATEGORY_TYPE}}"
}
```

Rules:
- **Do NOT put username/password in `demo.json`.** Credentials belong on the Demo Mode login page (account cards) and in `demo-mode/README.md` for maintainers.
- If `{{LIVE_DEMO_URL}}` is empty / placeholder, set `"live_demo_url": ""` and add a clear TODO in `demo-mode/README.md` only (not in client docs as scary unfinished text).
- `type` must be the portfolio category slug (`web-app`, `shopify-theme`, `mobile-app`, …) or `hide`.
- When the human deploys the demo, **only** update `live_demo_url` — never invent a fake public URL.

Also add a GitHub topic later (human): same as `type` so `/our-projects/...` picks this repo up.

### Demo Mode hard rules

| Do | Do NOT |
|----|--------|
| Same screens, routes, labels, layout as production | Call production Supabase / Firebase / Mongo / SQL |
| Client-only or local file storage | Require API keys, webhooks, SMTP |
| Mock external APIs | Keep real secret-dependent `/api` routes |
| Per-user sandboxes keyed by user id/email | One shared mutable store for all demo users |
| Clear “Demo Mode” banner / title suffix | Silent clone that looks like live production |
| Own `package.json` in `demo-mode/` when practical | Depend on root `.env` |
| Professional seed data (filled tables/charts) | Empty, broken, or joke-filled screens |
| Root build **excludes** `demo-mode/` (tsconfig / eslint / vercel) | Let Next/TS compile `demo-mode` during main product deploy |

### Production build exclusion (REQUIRED — do this in Phase 1)

Before Phase 1 acceptance, configure the **root product** so `demo-mode/` is invisible to production build:

1. Ensure `demo-mode/package.json` exists (standalone install).
2. Update root `tsconfig.json` `exclude` to include `"demo-mode"` (and `"demo-mode/**"` if the toolchain needs it).
3. Add `demo-mode/**` to root ESLint ignore.
4. Add `demo-mode` to `.vercelignore` at repo root when using Vercel for the **main** product (unless demo is a separate Vercel project with Root Directory `demo-mode` only).
5. Confirm no production imports: `from "@/../demo-mode"` / relative imports into `demo-mode/` from root `app` / `src`.
6. Run **root** `npm run build` and confirm it does not error on demo-mode sources.
7. Document in `demo-mode/README.md`: “Demo is excluded from the main product build; deploy demo separately.”

If the stack is not Next.js, apply the same idea: exclude the demo folder from the main compile/publish step (Python package data, Docker COPY, etc.).

### `demo-mode/.gitignore` (REQUIRED — do in Phase 1, do not leave for the human)

Root `.gitignore` does **not** always cover nested demo app junk the way you expect when demo is opened/deployed on its own. Create **`demo-mode/.gitignore`** in the same session as Demo Mode setup — **do not** wait for the human to add it after the prompt finishes.

1. Read the **root** `.gitignore` (and any stack defaults for this app).
2. Create `demo-mode/.gitignore` with at least the same dependency / build / env / OS / debug ignores, adapted for paths **inside** `demo-mode/` (no need for a leading `/demo-mode` prefix — this file lives inside the folder).
3. Typical Next.js / Node demo entries (adjust to this stack; keep anything extra already in root):

```gitignore
# dependencies
node_modules/
.pnp
.pnp.*
.yarn/*
!.yarn/patches
!.yarn/plugins
!.yarn/releases
!.yarn/versions

# testing
coverage/

# next.js / build
.next/
out/
build/
dist/

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# env (never commit secrets)
.env
.env.*
!.env.example

# vercel / typescript
.vercel
*.tsbuildinfo
next-env.d.ts

# local capture / playwright junk (if present)
test-results/
playwright-report/
blob-report/
playwright/.cache/
```

4. **Do commit** `demo.json`, source, `public/` assets, and `.gitignore` itself. **Do not commit** `node_modules/`, `.next/`, `.env*`, `.vercel/`.
5. If root `.gitignore` is missing entries that demo needs, you may also add `demo-mode/node_modules/`, `demo-mode/.next/`, `demo-mode/.env*` at **repo root** as a safety net — but **`demo-mode/.gitignore` is still mandatory**.
6. Mention in Phase 1 summary: “demo-mode/.gitignore created (mirrored from root + demo defaults).”

### Professional Demo Mode UX (REQUIRED)
- Polished login with **clickable demo account cards**.
- Visible but tasteful “Demo Mode” indicator (banner or subtitle) — not a huge ugly warning.
- Every major page looks **demo-ready**: seeded rows, charts, settings, reference dropdowns.
- Seed names/companies/statuses must read like a real business demo (e.g. “Northwind Retail”, “Ayesha Khan”, “Invoice #INV-1042”) — never “asd”, “test user 99”, “xxx”.
- Optional “Reset demo data” control for the signed-in sandbox.
- Mobile-usable layout for key screens (portfolio clients often check phone).

### Architecture (pick this repo’s stack)

**Next.js / React / SPA**
1. Clone UI into `demo-mode/` (or twin app).
2. Remove/neutralize real DB clients, secret APIs, env-gated blocks.
3. Add:
   - `lib/demoAuth.ts` — session in localStorage / sessionStorage
   - `lib/demoStore.ts` — CRUD, namespaced by user
   - `lib/demoSeed.ts` — first-login seed (professional fictional data)
   - `lib/demoUsers.ts` — fixed accounts + roles
4. Storage keys:
   ```text
   demo:{{APP_SLUG}}:user:{userId}:{resource}
   demo:{{APP_SLUG}}:session
   ```
5. `npm install && npm run dev` must work with **no `.env`**.

**Streamlit / Python**
- Own entry under `demo-mode/`; per-user JSON under `demo-mode/data/users/{username}/`; mock externals; Demo Mode banner; professional seed JSON.

### Demo users on login (REQUIRED)

Show **demo account cards** on login (click → fill / sign in). Minimum:

| Role | Login | Password |
|------|-------|----------|
| Admin | `admin@admin.com` or `admin` | `admin123` |
| Editor / Staff | `editor@demo.com` or `demo` | `demo123` |
| Viewer (if app has RO) | `viewer@demo.com` or `viewer` | `view123` |

- Isolated sandbox per user
- Seed on **first** login only (optional “Reset demo data”)
- Document accounts in `demo-mode/README.md` (maintainer). In client `Documentation/`, mention that demo logins are shown on the demo login screen — do not dump a scary credential wall unless a dedicated “Demo access” guide needs a clean table.

### Phase 1 acceptance
- [ ] `demo-mode/` runs offline without secrets
- [ ] Login cards work; per-user isolation; seed on first login
- [ ] Seed/UI looks professional (no joke/empty junk screens)
- [ ] No live Supabase/secret API usage in demo paths
- [ ] Favicon from `https://www.trendswd.com/favicon.png` wired
- [ ] Logo only if a real navbar/footer logo slot exists
- [ ] `demo-mode/demo.json` has `type` + `live_demo_url` (URL or `""`) — **no passwords**
- [ ] `demo-mode/README.md` has run steps + accounts + URL TODO if needed
- [ ] **`demo-mode/.gitignore` exists** (mirrored from root + node_modules / .next / .env* / build / OS / debug) — human must not have to add this later
- [ ] **Root production build excludes `demo-mode/`** (tsconfig / eslint / vercelignore as needed)
- [ ] **Root `npm run build` succeeds** without compiling or failing on `demo-mode/`
- [ ] Print summary: path, run command, accounts, mocks, storage, branding, **exclude config touched**, **gitignore path**

**STOP.** Print Phase 1 summary. Ask before Phase 2 only if Demo Mode cannot run. Otherwise continue.

---

# PHASE 2 — Documentation folder skeleton (`Documentation/`)

### Goal
Create the **portfolio docs folder structure** (stubs OK). Full prose is Phase 4 after screenshots exist.

### Target structure (REQUIRED)

```text
Documentation/
├── index.md
├── README.md
├── APP-VERSION.md
├── CHANGELOG.md
├── version.json
├── _meta/
│   └── navigation.json
├── images/                      # ONLY canonical screenshot folder
│   └── .gitkeep
├── 00-getting-started.md        # stub OK
└── (optional stub 01-*.md — or create fully in Phase 4)
```

### `version.json`
```json
{
  "name": "{{PRODUCT_NAME}}",
  "version": "{{VERSION}}",
  "released": "{{RELEASE_DATE}}"
}
```

### `_meta/navigation.json` (minimum)

```json
{
  "site": "{{PRODUCT_NAME}} Documentation",
  "base_url": "https://trendswd.com/projects/{{REPO_NAME}}/doc",
  "version": "{{VERSION}}",
  "version_date": "{{RELEASE_DATE}}",
  "navigation": [
    { "title": "Home", "path": "/docs", "file": "index.md" },
    {
      "title": "Getting started",
      "children": [
        { "title": "Version", "path": "/docs/APP-VERSION", "file": "APP-VERSION.md" },
        { "title": "Changelog", "path": "/docs/CHANGELOG", "file": "CHANGELOG.md" }
      ]
    },
    { "title": "Pages", "children": [] }
  ]
}
```

### `CHANGELOG.md` format (REQUIRED from day one)

Use Keep-a-Changelog style. Newest section on top. One section per **calendar day** of work (and/or per version bump):

```markdown
# Changelog

All notable changes to {{PRODUCT_NAME}} are documented here.

## [{{VERSION}}] — {{RELEASE_DATE}}

### Added
- Initial Demo Mode and documentation pipeline for portfolio publishing.

### Changed
- (none yet)

### Fixed
- (none yet)
```

Rules:
- Client-readable bullets (“Improved invoice filters”) — not git dump (“fix stuff”, “wip”).
- No secrets, no internal dispute notes, no “ask Ahmed” TODOs.
- Every meaningful product / docs / demo change later **must** append here (enforced in Phase 5 rules).

### `APP-VERSION.md`
Short professional version page: current version, release date, link to Changelog, what this release includes in 3–6 bullets.

### Stubs
- `index.md` — product name, version table, live demo placeholder from `demo-mode/demo.json`, “Screenshots pending”.
- `README.md` — pipeline note for maintainers: Demo → Screenshots → Docs → Rules.

### Phase 2 acceptance
- [ ] Folder tree exists under `Documentation/`
- [ ] `images/` ready for PNGs
- [ ] `version.json` / APP-VERSION / CHANGELOG / navigation version fields match
- [ ] Print: list of files created

**Continue to Phase 3.**

---

# PHASE 3 — Playwright screenshots → `Documentation/images/`

### Goal
Automate **full visual coverage** of Demo Mode. Save PNGs for documentation **only** under `Documentation/images/`.

### Prefer
Run against **Demo Mode** only (fictional professional data). Never production secrets / real customer data.

### Paths

| What | Path |
|------|------|
| Output PNGs (canonical) | `Documentation/images/` |
| Capture script | `demo-mode/capture-docs.js` |
| Index | `Documentation/images/SCREENSHOT-INDEX.md` |
| Optional mirror | `demo-mode/screenshots/` (must still copy/write finals to Documentation/images) |

### Prerequisites
1. Confirm `demo-mode/` exists and runs.
2. `cd demo-mode && npm install` (or stack equivalent).
3. Install Playwright: `npm install -D playwright` && `npx playwright install chromium`.
4. Start demo: `npm run dev` — detect real port (`3000` / `3001` / `8501`).
5. Wait until HTTP responds, then run capture.
6. Env overrides:
   ```bash
   DOCS_URL={{LOCAL_DEMO_URL}}
   DOCS_EMAIL={{DEMO_ADMIN_EMAIL}}
   DOCS_PASSWORD={{DEMO_ADMIN_PASS}}
   node capture-docs.js
   ```

### Login
1. Screenshot login **before** submit.
2. Sign in as admin; wait for real post-login landmark.
3. Optional second role pass only for permission-diff screens (`viewer-…` in filename).

### Coverage (must)
- Every main route / nav destination
- Primary CTAs, filters, tabs, row menus, create/edit **modals/drawers** (Cancel after shot)
- Tables with seed rows; charts after paint
- Mobile subset: home, open nav, 1 content page, settings/profile if exist  
Desktop `1280×800`, mobile `375×812`.

### Naming
```text
01-login.png
02-dashboard.png
03-…-modal.png
18-mobile-dashboard.png
```
Global counter; clear old numbered `*.png` in `Documentation/images/` on full recapture (keep `.gitkeep` / index handling clean).

### Script requirements
- Real selectors for **this** app
- Discover routes from sidebar / router
- Guard optional UI with `count()` checks
- Log each saved file; non-zero exit on hard failure
- npm script: `"screenshots": "node capture-docs.js"`
- Write files to **`Documentation/images/`** (resolve path from `demo-mode/` → `../Documentation/images`)

### After capture
Write `Documentation/images/SCREENSHOT-INDEX.md`:
- datetime, base URL, user
- table: `# | file | route | what | notes`
- PNG count

### Phase 3 acceptance
- [ ] Demo used as `DOCS_URL`
- [ ] PNGs exist under `Documentation/images/`
- [ ] Login + main nav + important modals captured
- [ ] Mobile subset done
- [ ] `SCREENSHOT-INDEX.md` complete
- [ ] Print: path, count, re-run commands, skips

**Continue to Phase 4.**

---

# PHASE 4 — Full documentation using screenshots

### Goal
Write **complete, professional English** portfolio documentation under `Documentation/`, wiring real screenshots from `Documentation/images/`.

### Style
- One markdown guide per page / major screen: `01-login.md`, `02-dashboard.md`, …
- Flat numbered guides preferred
- Screenshots: `![Login](./images/01-login.png)` — **always** this relative form
- Exact UI labels; step-by-step for a new user / client trainee

### Every page guide MUST include
1. `# Title`
2. Version line (`{{VERSION}}`)
3. Route
4. Who can access
5. Screenshot(s) with `./images/...` paths
6. What this page does
7. Layout at a glance
8. Numbered steps (exact button/field labels)
9. Fields / tables / modals / permissions as relevant
10. Errors & edge cases (user-facing, calm tone)
11. Related links

### Update
- `index.md` — product blurb, version table, **live demo URL** from `demo-mode/demo.json`, how to open demo, full index, simple ASCII app map
- `_meta/navigation.json` — every guide listed
- `APP-VERSION.md`, `CHANGELOG.md`, `version.json` — version fields equal
- Map each PNG from `SCREENSHOT-INDEX.md` into the correct guide
- If a shot is missing: keep correct `![...](./images/...)` placeholder and list under README “Screenshots still needed” (maintainer), not as broken client panic text on Home

### Do not
- Invent fake image filenames
- Scatter docs outside `Documentation/`
- Put maintainer-only walls of text at top of CHANGELOG or index
- Link to `demo-mode/screenshots/` from docs
- Include unprofessional seed examples in prose

### Phase 4 acceptance
- [ ] Every major route has a guide
- [ ] Every nav item file exists
- [ ] Screenshots wired via `./images/...` or listed missing for maintainers
- [ ] Version synced across meta / APP-VERSION / index / changelog / version.json
- [ ] Tone is client-professional
- [ ] `demo-mode/demo.json` still valid; index shows same live URL or clean “available on project page” wording

**Continue to Phase 5.**

---

# PHASE 5 — Cursor rules (auto CHANGELOG + version — permanent)

### Goal
Install project Cursor rules so **future changes** (any Cursor session in this repo) automatically:
1. Record what changed in `Documentation/CHANGELOG.md`
2. Keep version files in sync
3. Bump version when the day’s work warrants it
4. Keep docs/demo professional and screenshot links correct

Human should **not** need to re-explain this every time.

### Create these files

#### 1) `.cursor/rules/portfolio-product.mdc` (`alwaysApply: true`)

```markdown
---
description: Trends WD portfolio product — demo, docs, changelog, version discipline
alwaysApply: true
---

# Trends WD portfolio product rules

This repo ships on the Trends WD portfolio via `demo-mode/` + `Documentation/`.

## On every meaningful change (UI, features, demo, docs, fixes)

1. Update `Documentation/CHANGELOG.md` under **today’s date** (newest section on top).
   - If a section for today / current version already exists, append bullets there.
   - If not, add a new `## [x.y.z] — YYYY-MM-DD` section.
   - Use client-readable bullets (Added / Changed / Fixed / Removed).
   - Never log secrets, jokes, or internal blame notes.

2. Keep these version fields identical when you bump:
   - `Documentation/version.json` → `version`, `released`
   - `Documentation/APP-VERSION.md`
   - `Documentation/_meta/navigation.json` → `version`, `version_date`
   - `Documentation/index.md` version table
   - Top changelog section heading

3. **Version bump policy (do this without being asked):**
   - Same calendar day, small ongoing edits → keep same version; append CHANGELOG bullets under today’s section.
   - End of a work session with shippable changes, or a new calendar day with new changes → bump **patch** (`1.0.0` → `1.0.1`) and set `released` / `version_date` to **today**.
   - New user-facing feature set → bump **minor** (`1.0.x` → `1.1.0`).
   - Breaking workflow / major redesign → bump **major** (`1.x` → `2.0.0`).
   - Always sync all version files listed above in the same edit.

4. If UI screens changed: refresh Playwright screenshots into `Documentation/images/`, update `SCREENSHOT-INDEX.md`, and fix guide image links (`./images/...` only). Also refresh hero / gallery images in root `README.md` if those screens changed.

5. If Demo Mode behavior/seed changed: update `demo-mode/` and any docs that describe those screens. Keep seed data professional.

6. Never put passwords in `demo-mode/demo.json`. Never invent a fake `live_demo_url`.

7. **Never let `demo-mode/` enter the main product production build.** Keep root `tsconfig` / ESLint / Vercel ignores excluding `demo-mode`. Do not import demo code from root `app`/`src`. Root `npm run build` must stay green. Deploy demo as a **separate** project (Root Directory `demo-mode`). If a change risks pulling demo into the main build, fix excludes in the same session — do not leave it for the human.

8. Keep **`demo-mode/.gitignore`** present and up to date (node_modules, .next/out/build, .env*, .vercel, OS/debug logs, Playwright junk). Mirror root ignores into demo-mode — do not leave gitignore setup for the human after the pipeline.

9. Client-facing docs and root `README.md` stay professional English — no Hinglish, no meme copy, no empty “lorem” UI in screenshots.

10. When finishing a change set, briefly confirm in the reply: changelog updated + version (or “same version, bullets appended”). If README visuals/copy changed, say so. If build-exclude or gitignore files changed, mention that too.

11. After a full pipeline run (or when asked), keep root `README.md` aligned with product + `Documentation/` (see Phase 6). Prefer embedding screenshots from `Documentation/images/` via `Documentation/images/filename.png` — do not invent image paths.
```

#### 2) `.cursor/rules/documentation-screenshots.mdc`

```markdown
---
description: Documentation screenshot paths and linking
globs: Documentation/**/*.md
alwaysApply: false
---

# Documentation screenshots

- Canonical images live in `Documentation/images/`.
- In markdown guides link only as `![Alt](./images/file.png)`.
- Do not link `demo-mode/screenshots/`.
- Do not invent filenames; check `Documentation/images/SCREENSHOT-INDEX.md`.
- After adding/renaming images, update the matching guide and navigation if needed.
```

#### 3) Optional `AGENTS.md` (repo root, short pointer)

```markdown
# Agent notes

Follow `.cursor/rules/portfolio-product.mdc`.
Portfolio pipeline: `demo-mode/` + `Documentation/` (screenshots in `Documentation/images/`).
On changes: update CHANGELOG and version files per the rule — do not wait to be asked.
`demo-mode/` must stay excluded from the main product production build (separate deploy only).
After full setup (or UI screenshot changes): keep root `README.md` professional and embed key images from `Documentation/images/`.
```

### Phase 5 acceptance
- [ ] `.cursor/rules/portfolio-product.mdc` exists with `alwaysApply: true`
- [ ] Screenshot rule file exists
- [ ] Optional `AGENTS.md` pointer exists
- [ ] Rules mention CHANGELOG + daily/session version bump + professional tone + `./images/` links + README alignment + **demo-mode excluded from main production build** + **demo-mode/.gitignore**
- [ ] Print: paths created

**Continue to Phase 6.**

---

# PHASE 6 — Root `README.md` (professional + docs screenshots)

### Goal
After Demo, Docs, Screenshots, and Rules are done, rewrite / update the **repository root `README.md`** so GitHub visitors see a **professional product overview** — not a messy WIP dump. Pull **key screenshots from `Documentation/images/`** (already captured in Phase 3) into the README. Do **not** invent new image files; reuse docs screenshots.

### When to run
- **Always** at the end of a full pipeline (Phases 1–5 complete).
- Also when the human pastes the “Refresh README” follow-up after later UI/docs changes.

### Image rules for README
| Do | Do NOT |
|----|--------|
| Use existing PNGs under `Documentation/images/` | Invent filenames that do not exist |
| Link as `Documentation/images/02-dashboard.png` (from repo root) | Link `demo-mode/screenshots/` |
| Pick 3–6 **best** screens (login optional, dashboard + 2–4 core flows) | Dump every PNG into README |
| Check `Documentation/images/SCREENSHOT-INDEX.md` for real names | Hotlink random external placeholders |
| Keep alt text clear and professional | Use meme captions |

Suggested selection (adapt to this app; skip missing):
1. Dashboard / home after login  
2. One primary list or workflow screen  
3. One create/edit modal or detail view  
4. One settings / reports / secondary highlight  
5. Optional: mobile shot if it looks strong  

### README structure (REQUIRED — professional English)

Rewrite root `README.md` to roughly this shape (adapt section titles to the product; keep it tight):

```markdown
# {{PRODUCT_NAME}}

One clear sentence: what the product does for the client.

![Dashboard](Documentation/images/02-dashboard.png)

## Overview
2–4 short paragraphs or bullets: who it is for, main outcomes.

## Features
- Bullet list of real capabilities (from the app, not vaporware)

## Screenshots
![…](Documentation/images/…)
![…](Documentation/images/…)
(short caption under each image optional)

## Demo
- How to run Demo Mode locally (`demo-mode/` — point to `demo-mode/README.md`)
- Live demo URL from `demo-mode/demo.json` → `live_demo_url` (or “Deploy pending” if empty — calm wording, no panic)
- Demo logins: “Shown as account cards on the Demo Mode login screen” (do not dump a huge credential table unless helpful; if included, keep it clean)

## Documentation
- Link to `Documentation/index.md` (and portfolio docs URL if known)
- Note that full guides and screenshots live under `Documentation/`

## Tech stack
Short accurate table/list from this repo.

## Getting started (production app, if applicable)
Install / env / run — only what is real for this repo. Never paste real secrets.

## Version
Current version from `Documentation/version.json` + link to `Documentation/CHANGELOG.md` / `APP-VERSION.md`.

## License / contact (optional)
Only if the repo already has a clear policy; otherwise omit or keep minimal (Trends WD).
```

### Professional tone (same as docs)
- Client-readable; no Hinglish, jokes, “WIP”, “asdf”, or internal GitHub process essays.
- No secrets, tokens, or production customer data.
- Prefer product language over “this repo was set up for the portfolio pipeline” (one short maintainer note at the bottom is OK if useful).

### Also update
- If an old README exists: **replace** messy sections; preserve only still-true install/env facts.
- Sync version string with `Documentation/version.json`.
- Append a CHANGELOG bullet under today: e.g. “Updated root README with product overview and documentation screenshots.” (bump version only if Phase 5 policy says so).

### Phase 6 acceptance
- [ ] Root `README.md` rewritten / updated in professional English
- [ ] Screenshots embedded from `Documentation/images/` only (verified files exist)
- [ ] Demo + Documentation sections point to real paths / URL from `demo.json`
- [ ] No fake images, no passwords in `demo.json`, no unprofessional copy
- [ ] CHANGELOG mentions README update if this pass changed it
- [ ] Print: README path + list of image files used

---

# FINAL OUTPUT (all phases)

Print one summary:

1. **Demo:** path, run command, accounts, `demo.json` (type + live_demo_url status), professionalism notes, **root build exclude confirmation**
2. **Screenshots:** `Documentation/images/` count, how to re-run
3. **Docs:** guide files, nav groups, missing images
4. **Rules:** changelog/version auto-discipline installed (paths)
5. **README:** root `README.md` updated; which `Documentation/images/` PNGs were embedded
6. **Human next steps:**
   - Deploy `demo-mode/` as its **own** host project (Root Directory `demo-mode`) → paste public URL into `demo-mode/demo.json` → `live_demo_url`
   - Do **not** fold demo into the main product Vercel project
   - Re-run Phase 6 / “Refresh README” after deploy so Live Demo link in README matches
   - Add GitHub topic = `{{CATEGORY_TYPE}}`
   - Ensure repo root has `demo-mode/` and `Documentation/` for portfolio sync

---

# Implementation order (never reverse)

1. Scan production: routes, auth, data, roles, externals  
2. **Phase 1** — `demo-mode/` + `demo.json` (professional seed) + **exclude demo-mode from root production build**  
3. **Phase 2** — `Documentation/` skeleton + CHANGELOG/version  
4. **Phase 3** — Playwright → `Documentation/images/`  
5. **Phase 4** — Full docs wired to `./images/` screenshots  
6. **Phase 5** — `.cursor/rules/` so future edits auto-update CHANGELOG + version  
7. **Phase 6** — Root `README.md` professional rewrite + embed screenshots from `Documentation/images/`  
8. Final summary + human deploy URL reminder (demo = separate deploy)  

END OF MASTER PROMPT

---

## After deploy — URL set (short paste)

Jab demo live ho jaye, Cursor me yeh paste karo:

```text
Update demo-mode/demo.json:
- set "live_demo_url" to: {{PASTE_PUBLIC_DEMO_URL_HERE}}
- keep "type" unchanged unless I say otherwise
- do NOT add demo_credentials (logins stay on the Demo Mode login page)
Also update Documentation/index.md live demo link to the same URL.
Update root README.md Demo section to the same live URL.
Append Documentation/CHANGELOG.md (today) and bump patch version + sync version files per .cursor/rules.
Show me the final demo.json, version, and README Demo section.
```

---

## Follow-ups (optional)

### Fix / finish Demo Mode
```text
Continue Demo Mode in demo-mode/ only.
Replace any remaining real API/DB/env usage with localStorage (or local JSON) + mocks.
Login cards, first-login seed, per-user isolation.
Seed data must stay professional (no joke names / empty junk screens).
Keep demo-mode excluded from root production build (tsconfig / eslint / vercelignore); root npm run build must stay green.
Ensure demo-mode/.gitignore exists (node_modules, .next, .env*, etc. — mirror root).
Update demo-mode/README.md + demo.json.
Update CHANGELOG + version per project rules.
```

### Re-capture screenshots
```text
Re-run Playwright against demo-mode.
Write PNGs to Documentation/images/ (clear old numbered PNGs), update SCREENSHOT-INDEX.md.
Wire guides with ./images/ links only.
Use DOCS_URL / demo admin from demo-mode/README.md.
Update CHANGELOG if visuals/docs changed.
Then refresh root README.md screenshot gallery from Documentation/images/.
```

### Docs / app changes (ongoing — rules should already cover this)
```text
Apply .cursor/rules/portfolio-product.mdc:
- Update Documentation to match the app
- Refresh screenshots in Documentation/images/ if UI changed
- Append CHANGELOG under today; bump version when policy says so; sync version.json / APP-VERSION / navigation / index
- Keep root README.md aligned (copy + Documentation/images/ embeds)
Keep professional English and working ./images/ links.
```

### Refresh README only (after pipeline / after new screenshots)
```text
Run Phase 6 only: rewrite/update root README.md professionally.
Embed 3–6 key screenshots from Documentation/images/ (verify via SCREENSHOT-INDEX.md).
Sync Demo URL from demo-mode/demo.json and version from Documentation/version.json.
Update CHANGELOG for the README pass. Show which images were used.
```

---

## One-liner (Urdu/Hinglish)

```text
Is project me portfolio pipeline chalao (order lock):
1) demo-mode/ — professional offline demo + demo.json (type + live_demo_url)
   + favicon from https://www.trendswd.com/favicon.png
   + HARD: demo-mode ko root production build se exclude (tsconfig/eslint/vercel) — main deploy mat todo
   + demo-mode/.gitignore bhi Phase 1 me banao (node_modules/.next/.env*) — baad me human se mat karwao
2) Documentation/ skeleton (CHANGELOG + version.json)
3) Playwright → Documentation/images/ + SCREENSHOT-INDEX.md
4) Client-facing English docs — screenshots sirf ./images/ se link
5) .cursor/rules/ — har change pe CHANGELOG + daily/session version bump (bar bar na bolna pade)
6) Root README.md — professional update; zaroori screenshots Documentation/images/ se embed
CONFIG pehle bharo. Full rules: Personal Notedbook/Portfolio-Project-Setup-Prompt.md
```
