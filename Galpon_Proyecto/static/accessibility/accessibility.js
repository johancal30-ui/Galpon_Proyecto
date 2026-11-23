(() => {
  'use strict';
  const key = 'galpon.accessibility.v1';
  const defaults = { size: '1', contrast: false, spacing: false, motion: false };
  let prefs = { ...defaults };
  try {
    const saved = JSON.parse(localStorage.getItem(key));
    if (saved && typeof saved === 'object') {
      if (['1', '1.15', '1.3', '1.5'].includes(saved.size)) prefs.size = saved.size;
      for (const name of ['contrast', 'spacing', 'motion']) prefs[name] = saved[name] === true;
    }
  } catch (_) { /* Preferences remain usable when storage is unavailable. */ }
  const apply = () => {
    document.documentElement.style.setProperty('--a11y-scale', prefs.size);
    for (const name of ['contrast', 'spacing', 'motion']) {
      document.documentElement.classList.toggle(`a11y-${name}`, prefs[name]);
    }
  };
  apply();
  const tools = document.createElement('aside');
  tools.id = 'a11y-tools';
  tools.setAttribute('aria-label', 'Opciones de accesibilidad');
  tools.innerHTML = `
    <button type="button" id="a11y-toggle" aria-label="Accesibilidad" title="Accesibilidad" aria-expanded="false" aria-controls="a11y-panel">
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <circle cx="16" cy="16" r="14"></circle>
        <circle cx="16" cy="9" r="2" fill="currentColor" stroke="none"></circle>
        <path d="M8 13l8 2 8-2M16 15v6m0-3-5 8m5-8 5 8"></path>
      </svg>
    </button>
    <section id="a11y-panel" aria-labelledby="a11y-title" hidden>
      <h2 id="a11y-title">Facilitar la lectura y el uso</h2>
      <label for="a11y-size">Tamaño del texto</label>
      <select id="a11y-size"><option value="1">Normal (100 %)</option><option value="1.15">Grande (115 %)</option><option value="1.3">Más grande (130 %)</option><option value="1.5">Muy grande (150 %)</option></select>
      <label><input type="checkbox" id="a11y-contrast">Alto contraste</label>
      <label><input type="checkbox" id="a11y-spacing">Mayor espaciado de lectura</label>
      <label><input type="checkbox" id="a11y-motion">Reducir movimiento</label>
      <p>Usa Tab para recorrer los controles y Escape para cerrar. Las preferencias se guardan en este navegador.</p>
      <div class="a11y-actions"><button type="button" id="a11y-reset">Restablecer</button><button type="button" id="a11y-close">Cerrar</button></div>
      <p id="a11y-status" role="status" aria-live="polite"></p>
    </section>`;
  document.body.append(tools);
  const toggle = document.getElementById('a11y-toggle');
  const panel = document.getElementById('a11y-panel');
  const size = document.getElementById('a11y-size');
  const sync = () => {
    size.value = prefs.size;
    for (const name of ['contrast', 'spacing', 'motion']) document.getElementById(`a11y-${name}`).checked = prefs[name];
  };
  const save = () => {
    apply();
    try { localStorage.setItem(key, JSON.stringify(prefs)); }
    catch (_) { document.getElementById('a11y-status').textContent = 'Opciones aplicadas. Este navegador no permite guardarlas.'; return; }
    document.getElementById('a11y-status').textContent = 'Preferencias guardadas.';
  };
  const close = () => { panel.hidden = true; toggle.setAttribute('aria-expanded', 'false'); toggle.focus(); };
  toggle.addEventListener('click', () => {
    if (!panel.hidden) { close(); return; }
    panel.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
    size.focus();
  });
  tools.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) { event.preventDefault(); close(); }
  });
  document.getElementById('a11y-close').addEventListener('click', close);
  size.addEventListener('change', () => { prefs.size = size.value; save(); });
  for (const name of ['contrast', 'spacing', 'motion']) {
    document.getElementById(`a11y-${name}`).addEventListener('change', event => { prefs[name] = event.target.checked; save(); });
  }
  document.getElementById('a11y-reset').addEventListener('click', () => { prefs = { ...defaults }; sync(); save(); });
  sync();
  const main = document.querySelector('main') || document.querySelector('.container, .login-container, form, h1');
  if (main) {
    if (!main.id) main.id = 'contenido-principal';
    if (!main.hasAttribute('tabindex')) main.tabIndex = -1;
    const skip = document.createElement('a');
    skip.className = 'a11y-skip';
    skip.href = `#${main.id}`;
    skip.textContent = 'Saltar al contenido principal';
    skip.addEventListener('click', () => main.focus());
    document.body.prepend(skip);
  }
})();
