/* Colour theme picker: three light and three dark themes.
   The chosen theme id is the only thing this file saves (localStorage key
   "cyber-compass.theme"). Without a saved choice the site follows the
   device's light/dark setting. Drafter redraws the page on every route, so
   the picker is built once and moved back into each new navigation bar.
   After each new page this file also moves keyboard focus to its heading. */
(() => {
  'use strict';
  if (window.cyberCompassTheme) return;

  // page, surface and accent only colour the small previews in the menu;
  // the full palettes live in style.css under :root[data-theme="..."].
  const THEMES = [
    { id: 'daylight', mode: 'light', label: 'Daylight', note: 'Crisp white and teal',
      page: '#f4f7fb', surface: '#ffffff', accent: '#0f766e' },
    { id: 'sand', mode: 'light', label: 'Sand', note: 'Warm paper and terracotta',
      page: '#f8f3ea', surface: '#fffdf8', accent: '#ac4b1b' },
    { id: 'lilac', mode: 'light', label: 'Lilac', note: 'Soft lavender and violet',
      page: '#f6f4fc', surface: '#ffffff', accent: '#6046cd' },
    { id: 'harbor', mode: 'dark', label: 'Harbor', note: 'Slate navy and sea-glass teal',
      page: '#0d1118', surface: '#1f2836', accent: '#86c9bb' },
    { id: 'nebula', mode: 'dark', label: 'Nebula', note: 'Dusky plum and soft lavender',
      page: '#0f0d16', surface: '#2a2540', accent: '#bba9f2' },
    { id: 'forest', mode: 'dark', label: 'Forest', note: 'Pine green and soft gold',
      page: '#0c110e', surface: '#1f2c25', accent: '#e3c47e' },
  ];
  const DEFAULTS = { light: 'daylight', dark: 'harbor' };
  // Themes that were renamed, so an older saved choice still works.
  // BOOT_SCRIPT in main.py maps the same ids.
  const RENAMED = { ember: 'forest' };
  const KEY = 'cyber-compass.theme';
  const root = document.documentElement;
  const system = matchMedia('(prefers-color-scheme: dark)');
  const find = id => THEMES.find(theme => theme.id === id);

  const write = id => {
    try { id ? localStorage.setItem(KEY, id) : localStorage.removeItem(KEY); } catch (_) {}
  };
  const read = () => {
    let id = null;
    try { id = localStorage.getItem(KEY); } catch (_) { return null; }
    if (Object.prototype.hasOwnProperty.call(RENAMED, id)) {
      id = RENAMED[id];
      write(id);
    }
    return find(id) ? id : null;
  };

  let saved = read(); // null = follow the device
  const current = () => saved || DEFAULTS[system.matches ? 'dark' : 'light'];

  // A short-lived class fades colours between themes instead of snapping.
  let fadeTimer = 0;
  function apply(animate) {
    const theme = find(current());
    if (animate) {
      root.classList.add('theme-fade');
      clearTimeout(fadeTimer);
      fadeTimer = setTimeout(() => root.classList.remove('theme-fade'), 400);
    }
    root.dataset.theme = theme.id;
    let meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.name = 'theme-color';
      document.head.append(meta);
    }
    meta.content = theme.page;
    return theme;
  }
  apply(false);

  /* ---------- Build the dropdown ---------- */
  const swatch = theme => {
    const span = document.createElement('span');
    span.className = 'theme-swatch';
    span.setAttribute('aria-hidden', 'true');
    span.style.setProperty('--swatch-page', theme.page);
    span.style.setProperty('--swatch-surface', theme.surface);
    span.style.setProperty('--swatch-accent', theme.accent);
    return span;
  };
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  };

  const menu = el('div', 'theme-menu');
  const trigger = el('button', 'theme-trigger');
  trigger.type = 'button';
  trigger.id = 'theme-trigger';
  trigger.setAttribute('aria-haspopup', 'menu');
  trigger.setAttribute('aria-expanded', 'false');
  trigger.setAttribute('aria-controls', 'theme-popover');
  const triggerSwatch = el('span', 'theme-trigger-swatch');
  triggerSwatch.setAttribute('aria-hidden', 'true');
  const triggerLabel = el('span', 'theme-trigger-label');
  trigger.append(triggerSwatch, triggerLabel, el('span', 'theme-chevron'));

  const popover = el('div', 'theme-popover');
  popover.id = 'theme-popover';
  popover.setAttribute('role', 'menu');
  popover.setAttribute('aria-labelledby', 'theme-trigger');
  popover.hidden = true;
  popover.append(el('p', 'theme-popover-title', 'Appearance'));

  const option = (id, name, note, preview) => {
    const button = el('button', 'theme-option');
    button.type = 'button';
    button.tabIndex = -1;
    button.dataset.themeId = id;
    button.setAttribute('role', 'menuitemradio');
    const text = el('span', 'theme-text');
    text.append(el('span', 'theme-name', name), el('span', 'theme-note', note));
    button.append(preview, text, el('span', 'theme-check'));
    return button;
  };

  for (const [mode, heading] of [['light', 'Light'], ['dark', 'Dark']]) {
    const group = el('div', 'theme-group theme-group-' + mode);
    group.setAttribute('role', 'group');
    group.setAttribute('aria-label', heading + ' themes');
    const label = el('p', 'theme-group-label', heading);
    label.setAttribute('aria-hidden', 'true');
    group.append(label);
    for (const theme of THEMES.filter(item => item.mode === mode)) {
      group.append(option(theme.id, theme.label, theme.note, swatch(theme)));
    }
    popover.append(group);
  }
  const deviceIcon = el('span', 'theme-device-icon');
  deviceIcon.setAttribute('aria-hidden', 'true');
  const device = option('', 'Match my device', '', deviceIcon);
  device.classList.add('theme-device');
  popover.append(el('div', 'theme-separator'), device);
  menu.append(trigger, popover);

  const options = [...popover.querySelectorAll('.theme-option')];

  function render() {
    const theme = find(current());
    for (const item of options) {
      const checked = item.dataset.themeId ? !!saved && item.dataset.themeId === theme.id : !saved;
      item.setAttribute('aria-checked', String(checked));
    }
    device.querySelector('.theme-note').textContent =
      'Now ' + find(DEFAULTS[system.matches ? 'dark' : 'light']).label + ', switches with your device';
    triggerLabel.textContent = theme.label;
    triggerSwatch.style.setProperty('--swatch-accent', theme.accent);
    triggerSwatch.style.setProperty('--swatch-surface', theme.surface);
    trigger.setAttribute('aria-label', 'Colour theme: ' + theme.label + (saved ? '' : ' (matching your device)'));
    trigger.title = 'Change colour theme';
  }

  function setOpen(open, focus) {
    popover.hidden = !open;
    trigger.setAttribute('aria-expanded', String(open));
    if (open && focus) (options.find(item => item.getAttribute('aria-checked') === 'true') || options[0]).focus();
    if (!open && focus) trigger.focus();
  }

  function choose(id) {
    if (id && !find(id)) return;
    saved = id || null;
    write(saved);
    apply(true);
    render();
  }

  trigger.addEventListener('click', () => setOpen(popover.hidden, true));
  trigger.addEventListener('keydown', event => {
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
    event.preventDefault();
    setOpen(true, true);
  });
  popover.addEventListener('click', event => {
    const item = event.target.closest('.theme-option');
    if (!item) return;
    choose(item.dataset.themeId);
    setOpen(false, true);
  });
  popover.addEventListener('keydown', event => {
    const index = options.indexOf(document.activeElement);
    const target = {
      ArrowDown: options[(index + 1) % options.length],
      ArrowUp: options[(index - 1 + options.length) % options.length],
      Home: options[0],
      End: options[options.length - 1],
    }[event.key];
    if (target) {
      event.preventDefault();
      target.focus();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      setOpen(false, true);
    } else if (event.key === 'Tab') {
      setOpen(false, false);
    } else if (event.key === 'Enter' || event.key === ' ') {
      // Stop Enter from reaching the surrounding Drafter form.
      event.preventDefault();
      if (index >= 0) options[index].click();
    }
  });
  document.addEventListener('pointerdown', event => {
    if (!popover.hidden && !menu.contains(event.target)) setOpen(false, false);
  });
  system.addEventListener('change', () => {
    if (saved) return render();
    apply(true);
    render();
  });
  window.addEventListener('storage', event => {
    if (event.key !== null && event.key !== KEY) return;
    saved = read();
    apply(true);
    render();
  });

  // Put the picker at the end of the navigation bar, and back again
  // whenever Drafter replaces the page with a new route.
  function mount() {
    const nav = document.querySelector('.navigation');
    if (!nav || nav.contains(menu)) return;
    setOpen(false, false);
    nav.append(menu);
  }

  // Drafter swaps in the whole new page, so the button or link that was used
  // disappears and keyboard focus falls back to the top of the document.
  // Move it to the new page's heading instead, so keyboard and screen reader
  // users land on the new content. The first page draw is left alone.
  let shownPages = 0;
  function focusHeading() {
    if (shownPages++ === 0) return;
    const active = document.activeElement;
    if (active && active !== document.body && active.isConnected) return;
    const heading = document.querySelector('.page-head h1');
    if (!heading) return;
    heading.tabIndex = -1;
    heading.focus({ preventScroll: true });
  }

  render();
  mount();
  // Drafter fires this after every page it draws (detail.fragment is true
  // when only part of the page changed). Listening to it is much cheaper than
  // watching the whole document for changes.
  window.addEventListener('drafter-page-loaded', event => {
    mount();
    if (!event.detail || !event.detail.fragment) focusHeading();
  });

  window.cyberCompassTheme = { THEMES, choose };
})();
