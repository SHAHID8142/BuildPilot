import mysql from 'mysql2/promise';

let pool: mysql.Pool | null = null;

export function getMySQLPool(): mysql.Pool {
  if (!pool) {
    pool = mysql.createPool({
      host: process.env.DB_HOST || 'localhost',
      port: Number(process.env.DB_PORT) || 3306,
      user: process.env.DB_USER || 'root',
      password: process.env.DB_PASSWORD || '',
      database: process.env.DB_NAME || 'sps_cms',
      waitForConnections: true,
      connectionLimit: 10,
      queueLimit: 0
    });
  }
  return pool;
}

export async function queryDB<T = any>(sql: string, params: any[] = []): Promise<T[]> {
  const pool = getMySQLPool();
  const [rows] = await pool.execute(sql, params);
  return rows as T[];
}

export async function getCollectionItems(collectionName: string, options: { onlyHomepage?: boolean; status?: string } = {}) {
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
  const rows = await queryDB(sql, params);
  return rows.map((row: any) => ({
    ...row,
    data: typeof row.data_json === 'string' ? JSON.parse(row.data_json) : row.data_json
  }));
}

export async function getCollectionItemBySlug(collectionName: string, slug: string) {
  const sql = `SELECT * FROM sps_collections WHERE collection_name = ? AND slug = ? LIMIT 1`;
  const rows = await queryDB(sql, [collectionName, slug]);
  if (!rows.length) return null;
  const row = rows[0];
  return {
    ...row,
    data: typeof row.data_json === 'string' ? JSON.parse(row.data_json) : row.data_json
  };
}

export async function getPageContent(slug: string) {
  const sql = `SELECT * FROM sps_pages WHERE slug = ? LIMIT 1`;
  const rows = await queryDB(sql, [slug]);
  if (!rows.length) return null;
  const row = rows[0];
  return {
    ...row,
    content: typeof row.content_json === 'string' ? JSON.parse(row.content_json) : row.content_json
  };
}
