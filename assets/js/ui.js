// Composants partagés : carte de jeu, en-tête commun.
import { STATUS, styleOf, coverSrc, store, el, fmtScore, applyTheme, bindThemeToggle } from './data.js';

applyTheme();
document.addEventListener('DOMContentLoaded', () => bindThemeToggle(document.getElementById('theme')));

export function gameUrl(g) { return `play.html?g=${encodeURIComponent(g.id)}`; }
export function collectionUrl(k) { return `collection.html?c=${encodeURIComponent(k)}`; }

function coverImg(g, cls = '') {
  const img = el('img', { src: coverSrc(g), alt: '', loading: 'lazy', decoding: 'async', class: cls });
  // Les vignettes d'époque sont souvent minuscules (88×66) : on garde des pixels nets.
  img.addEventListener('load', () => { if (g.coverPixel || (img.naturalWidth && img.naturalWidth < 200)) img.classList.add('pixel'); }, { once: true });
  img.addEventListener('error', () => { img.src = coverSrc({ ...g, cover: null }); }, { once: true });
  return img;
}

export function card(g, { collections, showCollection = true } = {}) {
  const st = styleOf(g.collection);
  const best = store.best(g.id);
  const fav = store.isFavorite(g.id);
  const favBtn = el('button', {
    class: 'fav', type: 'button', 'aria-pressed': String(fav),
    'aria-label': `${fav ? 'Retirer' : 'Ajouter'} ${g.title} ${fav ? 'des' : 'aux'} favoris`,
    onclick: e => {
      e.preventDefault(); e.stopPropagation();
      const on = store.toggleFavorite(g.id);
      favBtn.setAttribute('aria-pressed', String(on));
      favBtn.setAttribute('aria-label', `${on ? 'Retirer' : 'Ajouter'} ${g.title} ${on ? 'des' : 'aux'} favoris`);
      document.dispatchEvent(new CustomEvent('kt:favorites'));
    },
  }, '★');
  const meta = [showCollection && collections?.[g.collection]?.name, g.year].filter(Boolean).join(' · ');
  const a = el('a', { class: `card s-${g.status}`, href: gameUrl(g), style: `--hue:${st.hue};--deep:${st.deep}` },
    el('div', { class: 'thumb' },
      coverImg(g),
      el('span', { class: 'badge ' + g.status }, STATUS[g.status] || g.status),
      g.status === 'jouable' ? el('span', { class: 'play-hint', 'aria-hidden': 'true' }, '▶') : null),
    el('div', { class: 'body' },
      el('h3', {}, g.title),
      el('span', { class: 'sub' }, meta || g.tech),
      best ? el('span', { class: 'best' }, 'Record : ', el('b', {}, fmtScore(best.score))) : null));
  return el('div', { class: 'card-wrap' }, a, favBtn);
}

export function shelf(title, games, opts, extra) {
  if (!games.length) return null;
  return el('section', { class: 'shelf', 'aria-label': title },
    el('div', { class: 'shelf-head' }, el('h2', {}, title), extra || null),
    el('div', { class: 'shelf-row' }, games.map(g => card(g, opts))));
}

export function progress(done, total, label = 'jouables') {
  const pct = total ? Math.round((done / total) * 100) : 0;
  return el('div', { class: 'progress' },
    el('div', { class: 'progress-label' }, el('b', {}, done), ` / ${total} ${label}`, el('span', { class: 'pct' }, `${pct} %`)),
    el('div', { class: 'progress-bar', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': String(total), 'aria-valuenow': String(done), 'aria-label': `${done} jeux ${label} sur ${total}` },
      el('span', { style: `width:${Math.max(pct, done ? 2 : 0)}%` })));
}

export function sortGames(list, mode) {
  const byTitle = (a, b) => a.title.localeCompare(b.title, 'fr', { sensitivity: 'base' });
  const rank = { 'jouable': 0, 'en-cours': 1, 'a-restaurer': 2 };
  const l = [...list];
  if (mode === 'year') l.sort((a, b) => (a.year || 9999) - (b.year || 9999) || byTitle(a, b));
  else if (mode === 'status') l.sort((a, b) => rank[a.status] - rank[b.status] || byTitle(a, b));
  else l.sort(byTitle);
  return l;
}
