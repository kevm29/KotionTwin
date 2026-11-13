import { loadCatalog, STATUS, placeholderColor, initials, el } from './data.js';

const state = { q: '', coll: 'all', status: 'all' };

function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  state.q = p.get('q') || '';
  state.coll = p.get('c') || 'all';
  state.status = p.get('s') || 'all';
}
function writeHash() {
  const p = new URLSearchParams();
  if (state.q) p.set('q', state.q);
  if (state.coll !== 'all') p.set('c', state.coll);
  if (state.status !== 'all') p.set('s', state.status);
  history.replaceState(null, '', p.toString() ? '#' + p : location.pathname);
}

function card(g) {
  const thumb = g.thumb
    ? el('div', { class: 'thumb' }, el('img', { src: g.thumb, alt: '', loading: 'lazy' }))
    : el('div', { class: 'thumb ph', style: `background:linear-gradient(135deg, ${placeholderColor(g.id)}, #12101c)` }, initials(g.title));
  thumb.append(el('span', { class: 'badge ' + g.status }, STATUS[g.status] || g.status));
  return el('a', { class: 'card', href: `play.html?g=${encodeURIComponent(g.id)}` },
    thumb,
    el('div', { class: 'body' },
      el('h3', {}, g.title),
      el('span', { class: 'sub' }, [g.year, g.tech].filter(Boolean).join(' · '))));
}

function chip(label, active, onclick) {
  return el('button', { class: 'chip', type: 'button', 'aria-pressed': String(active), onclick }, label);
}

function render(data) {
  const { collections, games } = data;
  const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const q = norm(state.q);
  const shown = games.filter(g =>
    (state.coll === 'all' || g.collection === state.coll) &&
    (state.status === 'all' || g.status === state.status) &&
    (!q || norm(g.title + ' ' + g.id).includes(q)));

  const cbox = document.getElementById('collections');
  cbox.replaceChildren(chip('Toutes les collections', state.coll === 'all', () => { state.coll = 'all'; update(); }),
    ...Object.entries(collections).map(([k, c]) => chip(`${c.name} (${games.filter(g => g.collection === k).length})`, state.coll === k, () => { state.coll = k; update(); })));
  const sbox = document.getElementById('statuses');
  sbox.replaceChildren(chip('Tous les états', state.status === 'all', () => { state.status = 'all'; update(); }),
    ...Object.entries(STATUS).map(([k, label]) => chip(`${label} (${games.filter(g => g.status === k).length})`, state.status === k, () => { state.status = k; update(); })));

  const groups = document.getElementById('groups');
  groups.replaceChildren(...Object.entries(collections).map(([k, c]) => {
    const list = shown.filter(g => g.collection === k);
    if (!list.length) return null;
    return el('section', { class: 'group', id: k },
      el('h2', {}, c.name, ' ', el('small', { class: 'sub' }, c.years)),
      el('p', { class: 'about' }, c.about),
      el('div', { class: 'grid' }, list.map(card)));
  }).filter(Boolean));
  document.getElementById('empty').hidden = shown.length > 0;

  const playable = games.filter(g => g.status === 'jouable').length;
  document.getElementById('counters').replaceChildren(
    el('span', { class: 'counter' }, el('b', {}, games.length), ' jeux recensés'),
    el('span', { class: 'counter' }, el('b', {}, playable), ' jouables'),
    el('span', { class: 'counter' }, el('b', {}, Object.keys(collections).length), ' collections'));
}

let data;
function update() { writeHash(); render(data); }

readHash();
const q = document.getElementById('q');
q.value = state.q;
q.addEventListener('input', () => { state.q = q.value; update(); });
loadCatalog().then(d => { data = d; render(d); }).catch(e => {
  document.getElementById('groups').textContent = 'Impossible de charger le catalogue : ' + e.message;
});
