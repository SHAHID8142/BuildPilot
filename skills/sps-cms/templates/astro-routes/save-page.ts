import type { APIRoute } from 'astro';
import { queryDB } from '../../lib/db';

export const POST: APIRoute = async ({ request, cookies }) => {
  try {
    const session = cookies.get('sps_admin_session');
    if (!session || !session.value) {
      return new Response(JSON.stringify({ error: 'Unauthorized: Admin session required' }), { status: 401 });
    }

    const body = await request.json();
    const { slug, content, title, seoMeta } = body;

    if (!slug || !content) {
      return new Response(JSON.stringify({ error: 'Missing required fields: slug, content' }), { status: 400 });
    }

    const contentJson = typeof content === 'string' ? content : JSON.stringify(content);
    const seoJson = seoMeta ? (typeof seoMeta === 'string' ? seoMeta : JSON.stringify(seoMeta)) : null;
    const pageTitle = title || slug.replace(/^\//, '') || 'Home';

    // Upsert into sps_pages
    await queryDB(
      `INSERT INTO sps_pages (slug, title, content_json, seo_meta) 
       VALUES (?, ?, ?, ?) 
       ON DUPLICATE KEY UPDATE 
         content_json = VALUES(content_json), 
         seo_meta = COALESCE(VALUES(seo_meta), seo_meta),
         title = COALESCE(VALUES(title), title),
         updated_at = CURRENT_TIMESTAMP`,
      [slug, pageTitle, contentJson, seoJson]
    );

    return new Response(JSON.stringify({ success: true, message: 'Page content published successfully' }), { status: 200 });
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
};
