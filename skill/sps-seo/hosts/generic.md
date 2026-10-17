# sps-seo — Host-Agnostic Notes

The SEO audit operates on **rendered build output**, so it is host-agnostic by
construction. Host-specific concerns:

- **Static hosts (cPanel/shared):** ensure `robots.txt` and `sitemap.xml` land
  in the web root actually served. Audit that directory, not the repo root.
- **Edge/serverless (Vercel/Netlify/Cloudflare):** audit the build output dir
  (`dist/`, `.output/`, `build/`). Headers-based `X-Robots-Tag` is not visible
  to the file audit — verify headers separately.
- **SSR (Next/Nuxt/SvelteKit):** run a production build, then audit the
  pre-rendered HTML. Client-rendered-only pages fail metadata checks by design.
