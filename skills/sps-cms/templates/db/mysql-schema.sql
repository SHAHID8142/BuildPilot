-- SPS-CMS Native MySQL Schema (Hostinger / cPanel / VPS Compatible)

CREATE TABLE IF NOT EXISTS sps_pages (
  id INT AUTO_INCREMENT PRIMARY KEY,
  slug VARCHAR(255) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  content_json LONGTEXT NOT NULL,
  seo_meta JSON,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sps_collections (
  id INT AUTO_INCREMENT PRIMARY KEY,
  collection_name VARCHAR(64) NOT NULL,
  slug VARCHAR(255) NOT NULL,
  title VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) DEFAULT NULL,
  status ENUM('published', 'draft', 'archived') DEFAULT 'published',
  show_on_homepage TINYINT(1) DEFAULT 1,
  is_featured TINYINT(1) DEFAULT 0,
  order_index INT DEFAULT 0,
  featured_image VARCHAR(512) DEFAULT NULL,
  data_json LONGTEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_collection_slug (collection_name, slug),
  INDEX idx_collection_home (collection_name, show_on_homepage, status),
  INDEX idx_collection_order (collection_name, order_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sps_media (
  id INT AUTO_INCREMENT PRIMARY KEY,
  filename VARCHAR(255) NOT NULL,
  filepath VARCHAR(512) NOT NULL,
  mime_type VARCHAR(64) NOT NULL,
  file_size INT NOT NULL,
  alt_text VARCHAR(255) DEFAULT '',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sps_settings (
  setting_key VARCHAR(64) PRIMARY KEY,
  setting_value LONGTEXT NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
