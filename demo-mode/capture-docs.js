#!/usr/bin/env node
/**
 * Portfolio screenshot capture entry (Phase 3).
 * Delegates to the Python Playwright script for this Streamlit demo.
 *
 * Usage (from repo root or demo_mode/):
 *   DOCS_URL=http://127.0.0.1:8501 node demo_mode/capture-docs.js
 *   node demo_mode/capture-docs.js --no-start
 */
const { spawnSync } = require("child_process");
const path = require("path");

const root = path.resolve(__dirname, "..");
const script = path.join(root, "scripts", "capture_docs_screenshots.py");
const outDir = path.join(root, "Documentation", "images");

const extra = process.argv.slice(2);
const envUrl = process.env.DOCS_URL;
const args = [script, "--out", outDir, ...extra];
if (envUrl && !extra.some((a) => a === "--url" || a.startsWith("--url="))) {
  args.push("--url", envUrl, "--no-start");
}

const result = spawnSync("python3", args, {
  cwd: root,
  stdio: "inherit",
  env: {
    ...process.env,
    DOCS_EMAIL: process.env.DOCS_EMAIL || "admin@admin.com",
    DOCS_PASSWORD: process.env.DOCS_PASSWORD || "admin123",
  },
});

process.exit(result.status == null ? 1 : result.status);
