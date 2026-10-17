# Logo Sources

Use `theSVG` as the default logo source for brand, framework, and cloud-service
icons.

## Primary source

- Site: [https://thesvg.org/](https://thesvg.org/)
- Registry: `https://thesvg.org/api/registry.json`
- Primary automation CDN:
  `https://cdn.jsdelivr.net/gh/glincker/thesvg@main/public/icons/{slug}/{variant}.svg`

## Preferred workflow

1. Resolve the slug from the registry.
2. Choose the correct variant for the background:
   - `default`
   - `mono`
   - `light`
   - `dark`
   - `wordmark`
3. Deliver the logo in the form the project needs:
   - CDN URL
   - local SVG file
   - package/component usage
   - raw SVG markup

## When to use local files

Prefer local downloaded SVGs when:
- the project should not depend on remote asset URLs
- the build pipeline wants checked-in assets
- the team wants stricter review of trademarked assets

## Fallback ladder

1. `theSVG`
2. official vendor / press kit / asset page
3. user-supplied asset

Do not scrape random logos from search results.

## Legal note

Brand marks are still trademarks of their owners. For production or commercial
use, follow the brand's official usage guidelines when needed.
