// Sends both Freelance Ireland forms to the Netlify function at /api/send (which relays to Brevo).
document.querySelectorAll('.quick-enquiry-form').forEach((form) => {
  const type = form.getAttribute('aria-label') === 'Freelancer application' ? 'join' : 'hire';
  const button = form.querySelector('button[type="submit"]');
  const buttonHTML = button.innerHTML;

  const status = document.createElement('p');
  status.className = 'form-status';
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  form.appendChild(status);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;

    const data = new FormData(form);
    data.append('form_type', type);

    button.disabled = true;
    button.textContent = 'Sending…';
    status.textContent = '';

    try {
      const res = await fetch('/api/send', { method: 'POST', body: data });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || !json.ok) throw new Error(json.error || 'Something went wrong. Please try again.');

      form.reset();
      status.textContent = type === 'join'
        ? 'Thanks — your application is in. We’ll be in touch.'
        : 'Thanks — we’ve got your request and will be in touch soon.';
    } catch (err) {
      status.textContent = err.message;
    } finally {
      button.disabled = false;
      button.innerHTML = buttonHTML;
    }
  });
});