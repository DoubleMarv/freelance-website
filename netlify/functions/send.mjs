// Freelance Ireland – relays both site forms to Brevo transactional email.
// Brevo API key is read from the Netlify env var "brevage".

const TO_EMAIL     = 'info@doublemarvellous.com';     // where submissions go
const TO_NAME      = 'Barry English';
const SENDER_EMAIL = 'info@doublemarvellous.com'; // must be a verified sender in Brevo
const SENDER_NAME  = 'Freelance Ireland website';

// Brevo contact list IDs (Contacts → Lists; the ID is shown next to each list).
const LIST_IDS = { hire: 5, join: 6 }; // e.g. { hire: 7, join: 8 }

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const isEmail = (s) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
const isUrl = (s) => { try { return /^https?:$/.test(new URL(s).protocol); } catch { return false; } };

export default async (req) => {
  if (req.method !== 'POST') return json({ ok: false, error: 'Method not allowed' }, 405);

  const apiKey = process.env.brevage;
  if (!apiKey) return json({ ok: false, error: 'Mail is not configured' }, 500);

  // Accepts JSON (from script.js) or form data.
  let data;
  try {
    data = (req.headers.get('content-type') || '').includes('application/json')
      ? await req.json()
      : Object.fromEntries(await req.formData());
  } catch { return json({ ok: false, error: 'Bad request' }, 400); }
  const get = (k) => String(data?.[k] ?? '').trim();

  // Honeypot: bots fill the hidden "website" field. Pretend success.
  if (get('website')) return json({ ok: true });

  const type = (get('kind') || get('form_type')) === 'join' ? 'join' : 'hire';
  const name = get('name');
  const email = get('email');
  const details = get('details');

  if (!name || name.length > 100)                     return json({ ok: false, error: 'Please enter your name.' }, 422);
  if (!isEmail(email) || email.length > 255)          return json({ ok: false, error: 'Please enter a valid email.' }, 422);
  if (details.length < 10 || details.length > 3000)   return json({ ok: false, error: 'Please add a few more details.' }, 422);
  if (!get('consent'))                                return json({ ok: false, error: 'Please tick the consent box.' }, 422);

  const fields = { Name: name, Email: email };
  let subject;

  if (type === 'hire') {
    subject = `New project enquiry – ${name}`;
    fields.Service = get('service');
    fields.Budget = get('budget');
    fields.Project = details;
  } else {
    const portfolio = get('portfolio');
    if (!isUrl(portfolio) || portfolio.length > 500) return json({ ok: false, error: 'Please enter a valid portfolio link.' }, 422);
    subject = `New freelancer application – ${name}`;
    fields['Main craft'] = get('service');
    fields.Portfolio = portfolio;
    fields.About = details;
  }

  const rows = Object.entries(fields)
    .map(([k, v]) =>
      `<tr><td style="padding:6px 12px 6px 0;vertical-align:top;font-weight:600">${esc(k)}</td><td style="padding:6px 0">${esc(v).replace(/\n/g, '<br>')}</td></tr>`)
    .join('');
  const html = `<html><body style="font-family:sans-serif"><h2>${esc(subject)}</h2><table>${rows}</table></body></html>`;
  const text = Object.entries(fields).map(([k, v]) => `${k}: ${v}`).join('\n');

  const res = await fetch('https://api.brevo.com/v3/smtp/email', {
    method: 'POST',
    headers: {
      accept: 'application/json',
      'content-type': 'application/json',
      'api-key': apiKey,
    },
    body: JSON.stringify({
      sender: { email: SENDER_EMAIL, name: SENDER_NAME },
      to: [{ email: TO_EMAIL, name: TO_NAME }],
      replyTo: { email, name },
      subject,
      htmlContent: html,
      textContent: text,
      tags: ['freelance-ireland', type],
    }),
  });

  if (!res.ok) {
    console.error('Brevo send failed', res.status, await res.text());
    return json({ ok: false, error: 'Sorry, something went wrong. Please try again.' }, 502);
  }

  // Add/update the submitter as a Brevo contact. Never blocks the form if it fails.
  if (LIST_IDS[type]) {
    try {
      const c = await fetch('https://api.brevo.com/v3/contacts', {
        method: 'POST',
        headers: { accept: 'application/json', 'content-type': 'application/json', 'api-key': apiKey },
        body: JSON.stringify({
          email,
          // Custom attributes must exist in Brevo first (Contacts → Settings → Attributes).
          attributes: type === 'hire'
            ? { FIRSTNAME: name, SERVICE: get('service'), BUDGET: get('budget'), DETAILS: details }
            : { FIRSTNAME: name, SERVICE: get('service'), PORTFOLIO: get('portfolio'), DETAILS: details },
          listIds: [LIST_IDS[type]],
          updateEnabled: true,
        }),
      });
      if (!c.ok) console.error('Brevo contact failed', c.status, await c.text());
    } catch (err) {
      console.error('Brevo contact error', err);
    }
  }

  return json({ ok: true });
};

export const config = { path: '/api/send' };
