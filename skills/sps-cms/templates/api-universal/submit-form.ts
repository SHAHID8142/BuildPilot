import type { APIRoute } from 'astro';
import { saveInquiry } from '../../../lib/db';

export const POST: APIRoute = async ({ request }) => {
  try {
    let body: any = {};
    const contentType = request.headers.get('content-type') || '';

    if (contentType.includes('application/json')) {
      body = await request.json();
    } else if (contentType.includes('application/x-www-form-urlencoded') || contentType.includes('multipart/form-data')) {
      const formData = await request.formData();
      body = Object.fromEntries(formData.entries());
    }

    const { name, email, phone, subject, message } = body;

    if (!name || !email || !message) {
      return new Response(JSON.stringify({ error: 'Name, email and message are required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const newInquiry = saveInquiry({
      name: String(name).trim(),
      email: String(email).trim(),
      phone: phone ? String(phone).trim() : '',
      subject: subject ? String(subject).trim() : 'Booking / General Inquiry',
      message: String(message).trim()
    });

    return new Response(JSON.stringify({
      success: true,
      message: 'Inquiry received successfully! Our team will contact you shortly.',
      inquiry: newInquiry
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message || 'Server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
};
