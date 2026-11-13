// Page Paramètres : pseudo (obligatoire pour jouer), thème, manette tactile, données locales.
import { store, el, pseudoError, cleanPseudo, applyTheme } from './data.js';
import { renderPlayerChip } from './ui.js';

const $ = id => document.getElementById(id);

function toast(msg) {
  const t = $('toast');
  t.textContent = msg; t.hidden = false; t.classList.add('show');
  clearTimeout(toast.t);
  toast.t = setTimeout(() => { t.classList.remove('show'); setTimeout(() => { t.hidden = true; }, 300); }, 2800);
}

// Retour vers le jeu qui a demandé un pseudo (?retour=play.html?g=…), limité aux pages du site.
const back = new URLSearchParams(location.search).get('retour');
const safeBack = back && /^play\.html\?g=[\w-]+$/.test(back) ? back : null;
if (safeBack) {
  $('return-notice').hidden = false;
  $('return-notice').textContent = 'Choisis un pseudo pour lancer la partie : tu reviendras au jeu juste après.';
}

// Pseudo
const input = $('pseudo');
input.value = store.pseudo;
const err = $('pseudo-err');
$('pseudo-form').addEventListener('submit', e => {
  e.preventDefault();
  const msg = pseudoError(input.value);
  err.hidden = !msg; err.textContent = msg || '';
  input.setAttribute('aria-invalid', String(!!msg));
  if (msg) { input.focus(); return; }
  store.pseudo = input.value;
  input.value = cleanPseudo(input.value);
  renderPlayerChip();
  if (safeBack) { location.href = safeBack; return; }
  toast(`Pseudo enregistré : ${store.pseudo}`);
});
if (!store.pseudo) input.focus();

// Thème
const seg = $('theme-seg');
const syncTheme = () => {
  for (const b of seg.querySelectorAll('button')) b.setAttribute('aria-checked', String((store.theme || '') === b.dataset.theme));
  for (const b of seg.querySelectorAll('button')) b.setAttribute('aria-pressed', b.getAttribute('aria-checked'));
};
seg.addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  store.theme = b.dataset.theme || null; applyTheme(); syncTheme();
  const tb = $('theme'); if (tb) { const dark = (document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark')) === 'dark'; tb.textContent = dark ? '☀' : '☾'; }
});
syncTheme();

// Manette tactile
const pad = $('pad-auto');
pad.checked = store.padAuto;
pad.addEventListener('change', () => { store.padAuto = pad.checked; toast(pad.checked ? 'Manette tactile automatique activée' : 'Manette tactile automatique désactivée'); });

// Données locales
function renderData() {

  const rows = [
    ['favorites', `Favoris : ${store.favorites.length}`, 'Effacer les favoris'],
    ['recent', `Parties récentes : ${store.recent.length}`, 'Effacer l\'historique'],
    ['all', 'Pseudo, favoris, historique et préférences', 'Tout réinitialiser'],
  ];
  $('data-list').replaceChildren(...rows.map(([k, label, btn]) => el('li', {},
    el('span', {}, label),
    el('button', { class: 'tool' + (k === 'all' ? ' danger' : ''), type: 'button', onclick: ev => {
      const b = ev.currentTarget;
      if (b.dataset.armed !== '1') { b.dataset.armed = '1'; b.textContent = 'Confirmer ?'; setTimeout(() => { b.dataset.armed = ''; b.textContent = btn; }, 3000); return; }
      store.clearAll(k);
      if (k === 'all') { input.value = ''; applyTheme(); syncTheme(); pad.checked = store.padAuto; }
      renderPlayerChip(); renderData(); toast('Données effacées');
    } }, btn))));
}
renderData();
