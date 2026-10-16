import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

let db: Database.Database | null = null;

export function getSQLiteDB(): Database.Database {
  if (!db) {
    const dbDir = path.join(process.cwd(), 'data');
    if (!fs.existsSync(dbDir)) {
      fs.mkdirSync(dbDir, { recursive: true });
    }
    const dbPath = path.join(dbDir, 'sps_cms.db');
    db = new Database(dbPath);
    db.pragma('journal_mode = WAL');
  }
  return db;
}

export function getCollectionItems(collectionName: string, options: { onlyHomepage?: boolean; status?: string } = {}) {
  const database = getSQLiteDB();
  let sql = `SELECT * FROM sps_collections WHERE collection_name = ?`;
  const params: any[] = [collectionName];

  if (options.onlyHomepage) {
    sql += ` AND show_on_homepage = 1`;
  }
  if (options.status) {
    sql += ` AND status = ?`;
    params.push(options.status);
  }

  sql += ` ORDER BY order_index ASC, created_at DESC`;
  const rows = database.prepare(sql).all(...params) as any[];
  return rows.map((row) => ({
    ...row,
    data: typeof row.data_json === 'string' ? JSON.parse(row.data_json) : row.data_json
  }));
}

export function getCollectionItemBySlug(collectionName: string, slug: string) {
  const database = getSQLiteDB();
  const sql = `SELECT * FROM sps_collections WHERE collection_name = ? AND slug = ? LIMIT 1`;
  const row = database.prepare(sql).get(collectionName, slug) as any;
  if (!row) return null;
  return {
    ...row,
    data: typeof row.data_json === 'string' ? JSON.parse(row.data_json) : row.data_json
  };
}

export function getPageContent(slug: string) {
  const database = getSQLiteDB();
  const sql = `SELECT * FROM sps_pages WHERE slug = ? LIMIT 1`;
  const row = database.prepare(sql).get(slug) as any;
  if (!row) return null;
  return {
    ...row,
    content: typeof row.content_json === 'string' ? JSON.parse(row.content_json) : row.content_json
  };
}
