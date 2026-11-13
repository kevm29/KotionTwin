// Page d'accueil (index.html) et pages de collection (collection.html?c=<id>).
import { loadCatalog, STATUS, styleOf, coverSrc, store, el, norm } from './data.js';
import { card, shelf, progress, sortGames, gameUrl, collectionUrl } from './ui.js';

const isCollectionPage = document.body.classList.contains('collection-page');
const fixedColl = isCollectionPage ? new URLSearchParams(location.search).get('c') : null;
const state = { q: '', coll: 'all', status: 'all', sort: isCollectionPage ? 'title' : 'collection', fav: false };

function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  state.q = p.get('q') || '';
  state.coll = fixedColl || p.get('c') || 'all';
  state.status = p.get('s') || 'all';
  state.sort = p.get('tri') || state.sort;
  state.fav = p.get('fav') === '1';
}
function writeHash() {
  const p = new URLSearchParams();
  if (state.q) p.set('q', state.q);
  if (!fixedColl && state.coll !== 'all') p.set('c', state.coll);
  if (state.status !== 'all') p.set('s', state.status);
  if (state.sort !== (isCollectionPage ? 'title' : 'collection')) p.set('tri', state.sort);
  if (state.fav) p.set('fav', '1');
  history.replaceState(null, '', location.pathname + location.search + (p.toString() ? '#' + p : ''));
}

let data;
const $ = id => document.getElementById(id);

function filtered() {
  const q = norm(state.q);
  const favs = new Set(store.favorites);
  return data.games.filter(g =>
    (state.coll === 'all' || g.collection === state.coll) &&
    (state.status === 'all' || g.status === state.status) &&
    (!state.fav || favs.has(g.id)) &&
    (!q || norm(`${g.title} ${g.id} ${g.description || ''} ${data.collections[g.collection]?.name || ''}`).includes(q)));
}

function renderToolbar(scope) {
  const sbox = $('statuses');
  const opts = [['all', 'Tous'], ...Object.entries(STATUS)];
  sbox.replaceChildren(...opts.map(([k, label]) => {
    const n = k === 'all' ? scope.length : scope.filter(g => g.status === k).length;
    return el('button', {
      class: 'seg-btn ' + k, type: 'button', 'aria-pressed': String(state.status === k),
      onclick: () => { state.status = k; update(); },
    }, label, el('span', { class: 'n' }, n));
  }));
  $('favs').setAttribute('aria-pressed', String(state.fav));
  $('sort').value = state.sort;
  if ($('coll')) $('coll').value = state.coll;
}

function renderGrid() {
  const { collections } = data;
  const shown = sortGames(filtered(), state.sort === 'collection' ? 'title' : state.sort);
  const groups = $('groups');
  const opts = { collections, showCollection: !fixedColl && state.sort !== 'collection' };
  if (state.sort === 'collection' && !fixedColl) {
    groups.replaceChildren(...Object.entries(collections).map(([k, c]) => {
      const list = shown.filter(g => g.collection === k);
      if (!list.length) return null;
      const st = styleOf(k);
      return el('section', { class: 'group', style: `--hue:${st.hue};--deep:${st.deep}`, 'aria-labelledby': 'g-' + k },
        el('div', { class: 'group-head' },
          el('h3', { id: 'g-' + k }, el('span', { class: 'dot', 'aria-hidden': 'true' }), c.name, ' ', el('small', {}, c.years)),
          el('a', { class: 'more', href: collectionUrl(k) }, 'Page de la collection →')),
        el('div', { class: 'grid' }, list.map(g => card(g, opts))));
    }).filter(Boolean));
  } else {
    groups.replaceChildren(shown.length ? el('div', { class: 'grid' }, shown.map(g => card(g, opts))) : '');
  }
  const total = fixedColl ? data.games.filter(g => g.collection === fixedColl).length : data.games.length;
  $('count').textContent = shown.length === total ? `${total} jeux` : `${shown.length} jeu${shown.length > 1 ? 'x' : ''} sur ${total}`;
  $('empty').hidden = shown.length > 0;
}

function renderShelves() {
  const box = $('shelves');
  if (!box) return;
  const byId = Object.fromEntries(data.games.map(g => [g.id, g]));
  const scope = fixedColl ? data.games.filter(g => g.collection === fixedColl) : data.games;
  const recent = store.recent.map(id => byId[id]).filter(g => g && scope.includes(g));
  const playable = sortGames(scope.filter(g => g.status === 'jouable'), 'title');
  const soon = sortGames(scope.filter(g => g.status === 'en-cours'), 'title');
  const opts = { collections: data.collections };
  box.replaceChildren(...[
    shelf('Reprendre une partie', recent, opts),
    shelf('Prêts à jouer', playable, opts, el('span', { class: 'shelf-note' }, `${playable.length} jeu${playable.length > 1 ? 'x' : ''}`)),
    shelf('Bientôt jouables', soon, opts),
  ].filter(Boolean));
}

function renderCollections() {
  const grid = $('coll-grid');
  if (!grid) return;
  grid.replaceChildren(...Object.entries(data.collections).map(([k, c]) => {
    const list = data.games.filter(g => g.collection === k);
    const st = styleOf(k);
    const pics = list.filter(g => g.cover).slice(0, 3);
    const ok = list.filter(g => g.status === 'jouable').length;
    return el('a', { class: 'coll-card', href: collectionUrl(k), style: `--hue:${st.hue};--deep:${st.deep}` },
      el('div', { class: 'coll-pics', 'aria-hidden': 'true' }, pics.map(g => el('img', { src: coverSrc(g), alt: '', loading: 'lazy', class: g.coverPixel ? 'pixel' : '' }))),
      el('div', { class: 'coll-body' },
        el('span', { class: 'coll-glyph', 'aria-hidden': 'true' }, st.glyph),
        el('h3', {}, c.name),
        el('p', { class: 'coll-years' }, c.years),
        el('p', { class: 'coll-about' }, c.about),
        el('p', { class: 'coll-stats' }, el('b', {}, list.length), ' jeux · ', el('b', {}, ok), ' jouable', ok > 1 ? 's' : '')));
  }));
}

function renderHero() {
  const games = fixedColl ? data.games.filter(g => g.collection === fixedColl) : data.games;
  const playable = games.filter(g => g.status === 'jouable');
  const hp = $('hero-progress');
  if (hp) hp.replaceChildren(progress(playable.length, games.length));
  const rnd = $('random');
  if (rnd) {
    rnd.addEventListener('click', e => {
      e.preventDefault();
      const pool = playable.length ? playable : games;
      location.href = gameUrl(pool[Math.floor(Math.random() * pool.length)]);
    });
    rnd.title = playable.length ? 'Lance un jeu jouable au hasard' : 'Ouvre une fiche au hasard';
  }
  const art = $('hero-art');
  if (art) {
    // Mosaïque de vignettes d'époque, en priorité les jeux jouables.
    // Une vignette par collection à tour de rôle (tirage différent chaque jour), pour montrer la variété de l'archive.
    const day = Math.floor(Date.now() / 864e5);
    const pools = Object.keys(data.collections).map(k => games.filter(g => g.cover && g.collection === k && g.status !== 'jouable'));
    const mix = [];
    for (let i = 0; mix.length < 9 && pools.some(p => p.length); i++) {
      const p = pools[i % pools.length];
      if (p.length) mix.push(p.splice((day * 7 + i * 13) % p.length, 1)[0]);
    }
    const pics = [...playable.filter(g => g.cover), ...mix].slice(0, 9);
    art.replaceChildren(...pics.map((g, i) => el('img', { src: coverSrc(g), alt: '', class: 'tile t' + i + (g.coverPixel ? ' pixel' : ''), loading: 'lazy' })));
  }
}

function renderCollectionHeader() {
  const c = data.collections[fixedColl];
  if (!c) {
    $('c-title').textContent = 'Collection introuvable';
    $('c-about').replaceChildren(el('a', { href: './' }, 'Retour au catalogue'));
    return false;
  }
  const st = styleOf(fixedColl);
  document.title = `${c.name} · KotionTwin`;
  document.body.style.setProperty('--hue', st.hue);
  document.body.style.setProperty('--deep', st.deep);
  $('c-glyph').textContent = st.glyph;
  $('c-title').textContent = c.name;
  $('c-years').textContent = c.years;
  $('c-about').textContent = c.about;
  $('c-tagline').textContent = st.tagline;
  $('crumb').textContent = c.name;
  const others = $('others');
  others.replaceChildren(...Object.entries(data.collections).filter(([k]) => k !== fixedColl).map(([k, o]) =>
    el('a', { class: 'chip', href: collectionUrl(k), style: `--hue:${styleOf(k).hue}` }, el('span', { class: 'dot', 'aria-hidden': 'true' }), o.name)));
  return true;
}

function update() { writeHash(); render(); }
function render() {
  const scope = data.games.filter(g => state.coll === 'all' || g.collection === state.coll);
  renderToolbar(scope);
  renderGrid();
}

function bind() {
  const q = $('q');
  q.value = state.q;
  let t;
  q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => { state.q = q.value; update(); }, 80); });
  addEventListener('keydown', e => {
    if (e.key === '/' && document.activeElement !== q && !/input|select|textarea/i.test(document.activeElement.tagName)) {
      e.preventDefault(); q.focus(); q.select();
    }
  });
  $('sort').addEventListener('change', e => { state.sort = e.target.value; update(); });
  $('favs').addEventListener('click', () => { state.fav = !state.fav; update(); });
  $('reset').addEventListener('click', () => { Object.assign(state, { q: '', status: 'all', fav: false, coll: fixedColl || 'all' }); q.value = ''; update(); });
  document.addEventListener('kt:favorites', () => { if (state.fav) renderGrid(); });
  document.querySelectorAll('[data-fav-link]').forEach(a => a.addEventListener('click', () => { state.fav = true; update(); }));
  const coll = $('coll');
  if (coll) {
    coll.replaceChildren(el('option', { value: 'all' }, 'Toutes les collections'),
      ...Object.entries(data.collections).map(([k, c]) => el('option', { value: k }, `${c.name} (${data.games.filter(g => g.collection === k).length})`)));
    coll.addEventListener('change', e => { state.coll = e.target.value; update(); });
  }
}

readHash();
loadCatalog().then(d => {
  data = d;
  if (isCollectionPage && !renderCollectionHeader()) { $('catalogue').hidden = true; return; }
  renderHero();
  renderShelves();
  renderCollections();
  bind();
  render();
}).catch(e => {
  $('groups').replaceChildren(el('p', { class: 'empty' }, 'Impossible de charger le catalogue : ' + e.message));
});
