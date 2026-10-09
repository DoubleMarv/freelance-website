/* Freelance Ireland — static page behaviour (no framework needed). */
(function () {
  // Set this to your own endpoint (e.g. Formspree, your API) to receive submissions as JSON.
  // Leave empty to just show the success message.
  var FORM_ENDPOINT = '';

  var tabs = Array.prototype.slice.call(document.querySelectorAll('.request-selector [role="tab"]'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.hero-request-area [role="tabpanel"]'));

  function selectTab(kind) {
    tabs.forEach(function (tab) {
      var active = tab.id.slice(-kind.length - 1) === '-' + kind;
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      tab.setAttribute('data-state', active ? 'active' : 'inactive');
      tab.tabIndex = active ? 0 : -1;
      var panel = document.getElementById(tab.getAttribute('aria-controls'));
      if (panel) {
        panel.setAttribute('data-state', active ? 'active' : 'inactive');
        panel.hidden = !active;
        panel.style.display = active ? '' : 'none';
      }
    });
  }

  tabs.forEach(function (tab, i) {
    tab.addEventListener('click', function () { selectTab(tab.id.split('-').pop()); });
    tab.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      var next = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      next.focus(); next.click();
    });
  });
  panels.forEach(function (p) { if (p.getAttribute('data-state') !== 'active') p.style.display = 'none'; });

  // Call-to-action buttons outside the hero: switch to the right form and scroll to it.
  document.querySelectorAll('button:not([type="submit"]):not([role="tab"])').forEach(function (btn) {
    if (btn.closest('form')) return;
    btn.addEventListener('click', function () {
      var text = btn.textContent.toLowerCase();
      var kind = /join|apply/.test(text) ? 'join' : 'hire';
      selectTab(kind);
      var item = btn.closest('.service-item');
      if (item && kind === 'hire') {
        var title = item.querySelector('h3').textContent.toLowerCase();
        var panel = panels.find(function (p) { return p.id.slice(-5) === '-hire'; });
        var select = panel && panel.querySelector('select[name="service"]');
        if (select) {
          Array.prototype.forEach.call(select.options, function (o) {
            var word = o.text.toLowerCase().split(/[ &]/)[0];
            if (title.indexOf(word) !== -1) select.value = o.value || o.text;
          });
        }
      }
      var area = document.querySelector('.hero-request-area');
      if (area) area.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  });

  // Forms
  document.querySelectorAll('form.enquiry-form').forEach(function (form) {
    var isJoin = !!form.closest('[id$="-join"]');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var old = form.querySelector('.form-error');
      if (old) old.remove();
      var data = Object.fromEntries(new FormData(form).entries());
      if (data.website) return; // honeypot
      data.kind = isJoin ? 'join' : 'hire';
      var submit = form.querySelector('[type="submit"]');
      submit.disabled = true;

      var send = FORM_ENDPOINT
        ? fetch(FORM_ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(data) })
            .then(function (r) { if (!r.ok) throw new Error('Request failed'); })
        : Promise.resolve();

      send.then(function () {
        var original = form.outerHTML;
        var box = document.createElement('div');
        box.className = 'success-state';
        box.setAttribute('role', 'status');
        box.innerHTML =
          '<span class="success-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></span>' +
          '<h3>' + (isJoin ? 'Application received.' : 'Project enquiry received.') + '</h3>' +
          '<p>Your details are with the Freelance Ireland team. ' + (isJoin ? 'We’ll use your email to contact you about suitable work.' : 'We’ll use your email to discuss your brief.') + '</p>' +
          '<button type="button" class="fi-button fi-button-hero inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 py-2 text-sm font-medium">Send another request</button>';
        form.replaceWith(box);
        box.querySelector('button').addEventListener('click', function () { location.reload(); });
      }).catch(function () {
        submit.disabled = false;
        var p = document.createElement('p');
        p.className = 'form-error'; p.setAttribute('role', 'alert');
        p.textContent = 'Something went wrong sending your request. Please try again.';
        form.appendChild(p);
      });
    });
  });
})();
