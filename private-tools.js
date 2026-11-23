/* Advanced browser code: Web Crypto, async fetch, event delegation and AbortSignal.
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
  // Prevent the surrounding Drafter form from submitting either secret.
  // Enter dispatches only the button in the textbox's own tool panel.
  window.addEventListener('keydown', event => {
    if (event.key !== 'Enter' || event.isComposing) return;
    if (!event.target.matches('#private-password,#private-email')) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (event.repeat) return;
    const button = event.target.closest('.private-tools').querySelector('[data-private]');
    if (!button.disabled) button.click();
  }, true);
  document.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-private]');
    if (!button) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const section = button.closest('.private-tools');
    const output = section.querySelector('.private-result');
    if (button.disabled) return;
    const mode = button.dataset.private;
    const input = section.querySelector(mode === 'password' ? '#private-password' : '#private-email');
    if (!input.value || !input.checkValidity()) {
      output.dataset.state = 'warning';
      output.textContent = 'Enter a valid ' + (mode === 'password' ? 'password sample.' : 'email address.');
      return;
    }
    if (mode === 'email' && !section.querySelector('#private-consent').checked) {
      output.dataset.state = 'warning';
      output.textContent = 'Please confirm permission and consent before checking.';
      return;
    }
    if (!window.isSecureContext || !window.crypto || !crypto.subtle ||
        typeof AbortSignal === 'undefined' || typeof AbortSignal.timeout !== 'function') {
      output.dataset.state = 'error';
      output.textContent = 'This browser cannot run the check securely here. Nothing was sent.';
      return;
    }
    let secret = input.value;
    // The password is cleared straight away. The email stays until the lookup
    // succeeds, so a rate limit or network error doesn't force retyping it.
    if (mode === 'password') input.value = '';
    let guidance = '';
    button.disabled = true;
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
          headers: {'Add-Padding': 'true'}, cache: 'no-store', credentials: 'omit',
          referrerPolicy: 'no-referrer', signal: AbortSignal.timeout(15000)
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
        const response = await fetch(endpoint, {
          cache: 'no-store', credentials: 'omit', referrerPolicy: 'no-referrer',
          signal: AbortSignal.timeout(15000)
        });
        if (response.status === 429) {
          output.dataset.state = 'warning';
          output.textContent = 'The provider rate limit was reached. Wait before trying again; no result was obtained.';
          return;
        }
        // A clean address comes back as {"Error": "Not found"}, with status 200 or 404.
        const data = await response.json().catch(() => null);
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
      output.dataset.state = 'error';
      output.textContent = (guidance ? guidance + '\n' : '') +
        'The breach lookup could not finish. No conclusion about exposure can be drawn. Try later.';
    } finally {
      secret = '';
      button.disabled = false;
    }
  }, true);
  // Clear visible private fields when navigating away or unloading the document.
  const clear = () => document.querySelectorAll('#private-password,#private-email').forEach(e => {e.value = '';});
  // Theme menu buttons stay on the page, so they don't clear the fields.
  document.addEventListener('click', event => {
    if (event.target.closest('[data-private], .theme-menu')) return;
    if (event.target.closest('a, button')) clear();
  }, true);
  window.addEventListener('pagehide', clear);
})();
