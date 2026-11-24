/* Advanced browser code: Web Crypto, async fetch, event delegation and AbortController.
   Secrets never become Drafter route parameters or State. No storage or logging.
   User-controlled/provider strings are displayed via textContent, never HTML.
   Closure-local variables are short-lived, not global application state.
   Each update also sets output.dataset.state (checking, exposed, clear, warning
   or error) so CSS can style the message; it is always a fixed keyword. */
(() => {
  'use strict';
  // Drafter can add this script again when it redraws; register the listeners once.
  if (window.cyberCompassPrivateTools) return;
  window.cyberCompassPrivateTools = true;

  const TIMEOUT_MS = 15000;
  // The check running for each tool ('password' or 'email'), as an
  // AbortController. Kept here rather than on the button, because Drafter
  // draws a fresh, idle button every time the page is shown again.
  const running = new Map();

  // A busy button is marked aria-disabled instead of disabled: disabling the
  // focused button would drop keyboard focus back to the top of the page.
  const setBusy = (button, busy) => {
    if (busy) button.setAttribute('aria-disabled', 'true');
    else button.removeAttribute('aria-disabled');
  };

  // Points the user at a field that needs attention.
  const flag = (field, output, message) => {
    field.setAttribute('aria-invalid', 'true');
    field.focus();
    output.dataset.state = 'warning';
    output.textContent = message;
  };

  // Prevent the surrounding Drafter form from submitting either secret.
  // Enter dispatches only the button in the textbox's own tool panel.
  window.addEventListener('keydown', event => {
    if (event.key !== 'Enter' || event.isComposing) return;
    if (!(event.target instanceof Element) || !event.target.matches('#private-password,#private-email')) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (event.repeat) return;
    const button = event.target.closest('.private-tools').querySelector('[data-private]');
    if (button) button.click();
  }, true);

  document.addEventListener('click', async (event) => {
    const button = event.target instanceof Element ? event.target.closest('[data-private]') : null;
    if (!button) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const mode = button.dataset.private;
    // One check per tool at a time, even if the page was redrawn meanwhile:
    // a second email check would only use up the free hourly limit.
    if (running.has(mode)) return;
    const section = button.closest('.private-tools');
    const output = section.querySelector('.private-result');
    const input = section.querySelector(mode === 'password' ? '#private-password' : '#private-email');
    if (!input.value || !input.checkValidity()) {
      flag(input, output, 'Enter a valid ' + (mode === 'password' ? 'password sample.' : 'email address.'));
      return;
    }
    input.removeAttribute('aria-invalid');
    if (mode === 'email') {
      const consent = section.querySelector('#private-consent');
      if (!consent.checked) {
        flag(consent, output, 'Please confirm permission and consent before checking.');
        return;
      }
      consent.removeAttribute('aria-invalid');
    }
    if (!window.isSecureContext || !window.crypto || !crypto.subtle ||
        typeof AbortController === 'undefined') {
      output.dataset.state = 'error';
      output.textContent = 'This browser cannot run the check securely here. Nothing was sent.';
      return;
    }
    let secret = input.value;
    // The password is cleared straight away. The email stays until the lookup
    // succeeds, so a rate limit or network error doesn't force retyping it.
    if (mode === 'password') input.value = '';
    let guidance = '';
    // Cancelled after TIMEOUT_MS, or as soon as Drafter shows another page
    // (see below), so a late answer never lands on a page that is gone.
    const controller = new AbortController();
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, TIMEOUT_MS);
    const request = {
      cache: 'no-store', credentials: 'omit', referrerPolicy: 'no-referrer', signal: controller.signal
    };
    running.set(mode, controller);
    setBusy(button, true);
    output.dataset.state = 'checking';
    output.textContent = 'Checking…';
    try {
      if (mode === 'password') {
        const length = Array.from(secret).length;
        const pattern = /^(.)\1+$/.test(secret) || /^(password|123456|qwerty|letmein)/i.test(secret);
        guidance = length < 16 || pattern
          ? 'Local check: short or predictable. Prefer a long, unique, randomly generated password.'
          : 'Local check: length is a useful start. Randomness and uniqueness still matter.';
        const bytes = new TextEncoder().encode(secret);
        secret = '';
        const digest = await crypto.subtle.digest('SHA-1', bytes);
        bytes.fill(0);
        const hash = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
        output.textContent = guidance + '\nChecking known exposure…';
        const response = await fetch('https://api.pwnedpasswords.com/range/' + hash.slice(0, 5), {
          ...request, headers: {'Add-Padding': 'true'}
        });
        if (!response.ok) throw new Error('service');
        const text = await response.text();
        const rows = text.trim().split(/\r?\n/);
        if (!rows.length || rows.some(row => !/^[A-F0-9]{35}:\d+$/i.test(row))) throw new Error('format');
        let count = 0;
        for (const row of rows) {
          const [suffix, occurrences] = row.split(':');
          if (suffix.toUpperCase() === hash.slice(5)) count = Number(occurrences);
        }
        output.dataset.state = count > 0 ? 'exposed' : 'clear';
        output.textContent = guidance + '\n' + (count > 0
          ? 'Exposed: found ' + count.toLocaleString() + ' times in HIBP. Do not use it; change it wherever reused.'
          : 'No match in HIBP Pwned Passwords. This does not prove the password is safe.');
      } else {
        const endpoint = 'https://api.xposedornot.com/v1/check-email/' + encodeURIComponent(secret.trim());
        secret = '';
        // The free API allows 2 checks a second, 25 an hour and 100 a day per IP address.
        // Over the limit, its Cloudflare front end answers 429 with an HTML page that has
        // no CORS headers, so the browser cannot read it and fetch throws a TypeError.
        // A blocker or network filter causes the same TypeError, so the message
        // names both. Retrying soon cannot help with an hourly cap.
        let response = null;
        try {
          response = await fetch(endpoint, request);
        } catch (error) {
          // Timeouts, cancelling and an offline browser are not rate limits;
          // report those as errors.
          if (error.name !== 'TypeError' || !navigator.onLine) throw error;
        }
        if (!response || response.status === 429) {
          output.dataset.state = 'warning';
          output.textContent = 'XposedOrNot could not be reached, so nothing was found or ruled out. ' +
            'The usual cause is its free limit of 25 checks an hour (100 a day) for your network; ' +
            'if so, try again in an hour. A privacy extension or network filter that blocks ' +
            'api.xposedornot.com causes the same message.';
          return;
        }
        // A clean address comes back as {"Error": "Not found"}, with status 200 or 404.
        const data = await response.json().catch(error => {
          if (controller.signal.aborted) throw error;
          return null;
        });
        if (data && (response.ok || response.status === 404) &&
            (data.Error === 'Not found' || data.error === 'Not found')) {
          input.value = '';
          output.dataset.state = 'clear';
          output.textContent = 'No match reported by XposedOrNot. Its coverage is incomplete; this is not proof of safety.';
          return;
        }
        if (!response.ok || !data || !Array.isArray(data.breaches)) throw new Error('service');
        const names = data.breaches.flat();
        if (!names.every(name => typeof name === 'string')) throw new Error('format');
        input.value = '';
        output.dataset.state = names.length ? 'exposed' : 'clear';
        output.textContent = names.length
          ? 'XposedOrNot reports exposure in: ' + names.join(', ') +
            '. Change affected or reused passwords, enable MFA, and review account activity.'
          : 'No match reported by XposedOrNot. This does not prove the account is safe.';
      }
    } catch (_) {
      // Cancelled because the user moved to another page: nobody is looking.
      if (controller.signal.aborted && !timedOut) return;
      output.dataset.state = 'error';
      output.textContent = (guidance ? guidance + '\n' : '') +
        'The breach lookup could not finish. No conclusion about exposure can be drawn. Try later.';
    } finally {
      secret = '';
      clearTimeout(timer);
      running.delete(mode);
      setBusy(button, false);
    }
  }, true);

  // Cancel running checks when Drafter replaces the page or the document unloads.
  const cancel = () => {
    for (const controller of running.values()) controller.abort();
  };
  window.addEventListener('drafter-page-loaded', event => {
    if (!event.detail || !event.detail.fragment) cancel();
  });

  // Clear visible private fields when navigating away or unloading the document.
  const clear = () => document.querySelectorAll('#private-password,#private-email').forEach(e => {e.value = '';});
  // Theme menu buttons stay on the page, so they don't clear the fields.
  document.addEventListener('click', event => {
    if (!(event.target instanceof Element)) return;
    if (event.target.closest('[data-private], .theme-menu')) return;
    if (event.target.closest('a, button')) clear();
  }, true);
  window.addEventListener('pagehide', () => {
    cancel();
    clear();
  });
})();
