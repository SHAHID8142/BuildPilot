-- SPS-CMS Embedded SQLite Schema (Zero-Config)

CREATE TABLE IF NOT EXISTS sps_pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  content_json TEXT NOT NULL,
  seo_meta TEXT,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sps_collections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  collection_name TEXT NOT NULL,
  slug TEXT NOT NULL,
  title TEXT NOT NULL,
  price REAL DEFAULT NULL,
  status TEXT DEFAULT 'published',
  show_on_homepage INTEGER DEFAULT 1,
  is_featured INTEGER DEFAULT 0,
  order_index INTEGER DEFAULT 0,
  featured_image TEXT DEFAULT NULL,
  data_json TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(collection_name, slug)
);

CREATE INDEX IF NOT EXISTS idx_collection_home ON sps_collections(collection_name, show_on_homepage, status);
CREATE INDEX IF NOT EXISTS idx_collection_order ON sps_collections(collection_name, order_index);

CREATE TABLE IF NOT EXISTS sps_media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  filepath TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  alt_text TEXT DEFAULT '',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sps_settings (
  setting_key TEXT PRIMARY KEY,
  setting_value TEXT NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
