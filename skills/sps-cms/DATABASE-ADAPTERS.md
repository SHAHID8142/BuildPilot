# Multi-Driver Database Adapters (Universal & Host-Agnostic)

SPS-CMS supports all standard web database engines without lock-in. The choice of database is determined during the initial Discovery Grill based on the client's hosting plan.

---

## 1. Supported Database Adapters

| Database Engine | Typical Hosting Environment | Driver / Library | Config Key |
| :--- | :--- | :--- | :--- |
| **MySQL / MariaDB** | cPanel, Hostinger, Namecheap, Dedicated VPS | `mysql2/promise` | `database: "mysql"` |
| **SQLite (Embedded)** | VPS (PM2/Docker), Node.js server, Local Dev | `better-sqlite3` | `database: "sqlite"` |
| **PostgreSQL** | Dedicated VPS, Railway, Render, Supabase (Self-hosted/Neon) | `pg` / `postgres` | `database: "postgres"` |
| **Cloudflare D1** | Cloudflare Pages (Serverless Edge) | `@cloudflare/workers-types` | `database: "d1"` |
| **LibSQL / Turso** | Edge & Serverless deployments | `@libsql/client` | `database: "libsql"` |

---

## 2. Environment Configuration by Host

### A. Standard Shared / cPanel / VPS (MySQL)
```env
DATABASE_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mysite_db
DB_USER=mysite_user
DB_PASSWORD=SecurePassword123!
```

### B. VPS / Node.js (Embedded SQLite)
```env
DATABASE_TYPE=sqlite
DATABASE_URL=file:./data/sps_cms.db
```

### C. Cloud / Dedicated Server (PostgreSQL)
```env
DATABASE_TYPE=postgres
DATABASE_URL=postgresql://user:password@localhost:5432/mysite_db
```

### D. Cloudflare Pages (D1 Database)
```toml
# wrangler.toml
[[d1_databases]]
binding = "DB"
database_name = "sps_cms_prod"
database_id = "xxxx-xxxx-xxxx"
```

---

## 3. Universal Multi-Collection Schema Architecture

### 1. `sps_pages` Table (For Visual Page Content)
Stores inline text strings and image URLs for singleton pages (Home, About, Contact).
- Columns: `id`, `slug` (UNIQUE), `title`, `content_json` (LONGTEXT), `seo_meta` (JSON), `updated_at`.

### 2. `sps_collections` Table (The Universal Polymorphic Entity Store)
Stores **any bulk entity** (Packages, Products, Doctors, Properties, Dishes, Courses, Portfolio items) in a hybrid structured-JSON format:
- Columns:
  - `id` (PK)
  - `collection_name` (VARCHAR: e.g. 'properties', 'doctors', 'packages', 'dishes')
  - `slug` (VARCHAR: e.g. 'luxury-beach-villa')
  - `title` (VARCHAR: primary display title)
  - `price` (DECIMAL: optional numeric index for pricing/sorting)
  - `status` (ENUM: 'published', 'draft', 'archived')
  - `show_on_homepage` (BOOLEAN: toggle for featured grid queries)
  - `is_featured` (BOOLEAN: toggle for VIP/Trending flags)
  - `order_index` (INT: drag-and-drop sort order)
  - `featured_image` (VARCHAR: main thumbnail URL)
  - `data_json` (LONGTEXT: stores all custom fields, itineraries, variants, specs)
  - `created_at`, `updated_at`
- Indexes: `(collection_name, slug) UNIQUE`, `(collection_name, show_on_homepage, status)`, `(collection_name, order_index)`.

### 3. `sps_media` Table (Media Library)
- Columns: `id`, `filename`, `filepath`, `mime_type`, `file_size`, `alt_text`, `created_at`.

### 4. `sps_settings` Table (Site Configuration)
- Columns: `setting_key` (PK), `setting_value` (LONGTEXT), `updated_at`.

---

## 4. Media Storage Adapters

1. **Local Server Disk (`/public/uploads`):**
   - Ideal for cPanel, VPS, and standard Node.js hosting. Zero recurring cost.
2. **Cloudflare R2 / S3-Compatible Storage:**
   - Ideal for serverless/edge environments (Cloudflare Pages, Vercel) where server disk is ephemeral. Direct signed URL or proxy upload.
