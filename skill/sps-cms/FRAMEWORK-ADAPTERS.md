# Multi-Stack Framework Adapters (Universal & Language-Agnostic)

SPS-CMS is designed with a **Universal Decoupled Architecture**. It works seamlessly across **JavaScript/TypeScript, PHP, Python, Go, Ruby, and Vanilla HTML**.

---

## 1. JavaScript & TypeScript Stacks

### A. Astro 4/5+
- **Rendering:** Island Architecture with `<AdminOverlay client:only="react" />` (0kb JS for public visitors).
- **Backend:** Server Endpoints (`src/pages/api/cms/*.ts`) or `Astro Actions`.
- **Database:** `mysql2/promise`, `better-sqlite3`, or `@libsql/client`.

### B. Next.js (App Router)
- **Rendering:** React Server Components (RSC) + Client Island for Admin.
- **Backend:** Next.js Server Actions with `revalidatePath()`.
- **Database:** Direct DB queries inside `lib/db.ts`.

### C. Nuxt.js 3 / Vue
- **Rendering:** Universal SSR with `useAsyncData()` and `<AdminOverlay />` component.
- **Backend:** Nitro Server Routes (`server/api/cms/*.ts`).

### D. Svelte / SvelteKit
- **Rendering:** SvelteKit Page Loaders (`+page.server.ts`).
- **Backend:** Form Actions (`+page.server.ts`) or API Endpoints (`+server.ts`).

---

## 2. PHP Ecosystem (Laravel & Native PHP)

### A. Modern Laravel 10/11
- **Routes:** `routes/web.php` (`/admin`, `/api/cms/*`).
- **Controllers:** `SpsCmsController.php` handling CRUD operations via Eloquent / DB Query Builder.
- **Blade View Integration:**
  ```html
  <!-- resources/views/layouts/app.blade.php -->
  @auth('admin')
    <script src="/sps-cms/overlay.js" defer></script>
  @endauth
  
  <h1 data-sps-key="hero.title">{!! $pageContent['hero.title'] ?? 'Default Title' !!}</h1>
  ```

### B. Native PHP / cPanel Shared Hosting (Zero Framework)
- **Single Drop-in API:** `api-cms.php` using standard `PDO` (MySQL/SQLite).
- **Admin UI:** Lightweight standalone HTML/Tailwind SPA in `/admin/index.html`.

---

## 3. Python Ecosystem (Django & FastAPI / Flask)

### A. Django 4/5
- **Views:** Django Class-based or Functional Views querying models (`SpsCollection`, `SpsPage`).
- **Templates:** Jinja2 / Django Templates with `data-sps-key` tags:
  ```html
  <h1 data-sps-key="home.headline">{{ page_content.headline|default:"Welcome" }}</h1>
  ```

### B. FastAPI / Flask
- **Endpoints:** Async routes (`/api/cms/save-page`, `/api/cms/collections`) querying SQLAlchemy or Peewee.

---

## 4. Go Ecosystem (Fiber / Gin / Echo)

- **Handlers:** REST handlers executing SQL queries via `database/sql` + `sqlx` or `gorm`.
- **HTML Templates:** Go `html/template` with standard `data-sps-key` attributes.

---

## 5. Vanilla Static HTML & Jamstack (Pure HTML + CSS + JS)

For ultra-lightweight static websites hosted on any web server (Apache, Nginx, GitHub Pages, Netlify):
1. Public HTML pages include the zero-dependency script:
   ```html
   <script src="/sps-cms/overlay.js"></script>
   ```
2. Elements marked with `data-sps-key="about.heading"` are made live-editable when logged in.
3. Content loads from a lightweight SQLite database or JSON file.
