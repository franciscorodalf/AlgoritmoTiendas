import { defineConfig } from "astro/config";

const base = process.env.SITE_BASE || "/";

export default defineConfig({
  site: process.env.SITE_URL || "https://franciscorodalf.github.io",
  base,
  output: "static"
});
