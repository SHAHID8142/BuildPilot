import type { APIRoute } from 'astro';
import { updateInquiryStatus, deleteInquiry } from '../../../lib/db';

export const POST: APIRoute = async ({ request, cookies }) => {
  const session = cookies.get('sps_admin_session');
  if (!session || !session.value) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  try {
    const { action, id, status } = await request.json();

    if (action === 'update-status') {
      updateInquiryStatus(Number(id), status);
      return new Response(JSON.stringify({ success: true }), { status: 200 });
    }

    if (action === 'delete') {
      deleteInquiry(Number(id));
      return new Response(JSON.stringify({ success: true }), { status: 200 });
    }

    return new Response(JSON.stringify({ error: 'Invalid action' }), { status: 400 });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message }), { status: 500 });
  }
};
