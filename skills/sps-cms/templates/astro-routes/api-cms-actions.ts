import type { APIRoute } from 'astro';
import { queryDB } from '../../lib/db';

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const { action, collection, id, data } = body;

    if (action === 'save_collection') {
      if (id) {
        // Update
        await queryDB(
          `UPDATE sps_collections SET title = ?, slug = ?, price = ?, status = ?, show_on_homepage = ?, is_featured = ?, featured_image = ?, data_json = ? WHERE id = ?`,
          [data.title, data.slug, data.price || null, data.status, data.show_on_homepage ? 1 : 0, data.is_featured ? 1 : 0, data.featured_image, JSON.stringify(data.data), id]
        );
      } else {
        // Insert
        await queryDB(
          `INSERT INTO sps_collections (collection_name, slug, title, price, status, show_on_homepage, is_featured, featured_image, data_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
          [collection, data.slug, data.title, data.price || null, data.status, data.show_on_homepage ? 1 : 0, data.is_featured ? 1 : 0, data.featured_image, JSON.stringify(data.data)]
        );
      }
      return new Response(JSON.stringify({ success: true }), { status: 200 });
    }

    if (action === 'toggle_home') {
      await queryDB(`UPDATE sps_collections SET show_on_homepage = ? WHERE id = ?`, [data.show_on_homepage ? 1 : 0, id]);
      return new Response(JSON.stringify({ success: true }), { status: 200 });
    }

    if (action === 'delete') {
      await queryDB(`DELETE FROM sps_collections WHERE id = ?`, [id]);
      return new Response(JSON.stringify({ success: true }), { status: 200 });
    }

    return new Response(JSON.stringify({ error: 'Unknown action' }), { status: 400 });
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
};
