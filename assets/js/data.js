// Accès partagé au catalogue (data/games.json), aux vignettes (data/covers.json)
// et aux données locales du joueur (favoris, parties récentes, scores) stockées en localStorage.

export const STATUS = {
  'jouable': 'Jouable',
  'en-cours': 'En restauration',
  'a-restaurer': 'À restaurer',
};

export const PLAN = {
  'ruffle-shim': 'SWF d\'origine + Ruffle (API de la plateforme simulée)',
  'recompilation': 'Recompilation des sources Haxe/AS',
  'portage': 'Portage HTML5 / logique serveur réimplémentée',
};

// Identité visuelle de chaque collection (couleurs du bandeau, des vignettes générées et des pastilles).
export const COLLECTION_STYLE = {
  kadokado:   { hue: '#ff9f1c', deep: '#7a3b00', glyph: 'K', tagline: 'Des parties de trois minutes et un score à battre.' },
  arkadeo:    { hue: '#29b6f6', deep: '#0b3a66', glyph: 'A', tagline: 'L\'arcade à missions, en Flash AS3.' },
  cafejeux:   { hue: '#c98a5a', deep: '#4a2510', glyph: 'C', tagline: 'Jeux de duel autour d\'une table de café.' },
  frutiparc:  { hue: '#7ccf3a', deep: '#1f4d0b', glyph: 'F', tagline: 'Le bureau fruité des débuts.' },
  muxxu:      { hue: '#ff5c8a', deep: '#5c0f2a', glyph: 'M', tagline: 'Arcade, gestion et duels entre amis.' },
  motiontwin: { hue: '#a77bff', deep: '#2c1466', glyph: 'MT', tagline: 'Les grands jeux web du studio.' },
};
export const styleOf = c => COLLECTION_STYLE[c] || { hue: '#ffcc33', deep: '#3a2a00', glyph: '?', tagline: '' };

let catalogPromise;
export function loadCatalog() {
  catalogPromise ||= Promise.all([
    fetch('data/games.json', { cache: 'no-cache' }).then(r => { if (!r.ok) throw new Error('Catalogue introuvable'); return r.json(); }),
    fetch('data/covers.json', { cache: 'no-cache' }).then(r => (r.ok ? r.json() : {})).catch(() => ({})),
  ]).then(([cat, covers]) => {
    for (const g of cat.games) {
      // La vignette fournie par le thread de restauration (g.thumb) reste prioritaire,
      // sauf si data/covers.json en propose une meilleure (cas des icônes 16×16 d'Arkadeo).
      const c = covers.games?.[g.id];
      g.cover = (c && (c.override || !g.thumb)) ? c.src : (g.thumb || null);
      g.coverPixel = !!c?.pixel;
    }
    return cat;
  });
  return catalogPromise;
}

// Accents et casse ignorés pour la recherche.
export const norm = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

export function initials(title) {
  const w = title.replace(/\(.*?\)/g, '').trim().split(/[\s-]+/).filter(Boolean);
  return (w.length > 1 ? w[0][0] + w[1][0] : title.slice(0, 2)).toUpperCase();
}

function hash(s) { let h = 0; for (const c of s) h = (h * 31 + c.charCodeAt(0)) >>> 0; return h; }

// Vignette générée (SVG) pour les jeux sans image : couleurs de la collection, motif propre au jeu.
export function generatedCover(g) {
  const st = styleOf(g.collection);
  const h = hash(g.id);
  const shapes = [];
  for (let i = 0; i < 9; i++) {
    const x = (h >> (i * 3)) % 400, y = ((h >> (i * 2)) * 7 + i * 53) % 300, r = 18 + ((h >> i) % 46);
    shapes.push(i % 3 === 0
      ? `<rect x="${x - r / 2}" y="${y - r / 2}" width="${r}" height="${r}" rx="${r / 4}" transform="rotate(${(h >> i) % 90} ${x} ${y})"/>`
      : `<circle cx="${x}" cy="${y}" r="${r / 2}"/>`);
  }
  const t = initials(g.title);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${st.hue}"/><stop offset="1" stop-color="${st.deep}"/></linearGradient></defs>
<rect width="400" height="300" fill="url(#g)"/>
<g fill="#fff" opacity=".13">${shapes.join('')}</g>
<text x="200" y="172" text-anchor="middle" font-family="Fredoka, Trebuchet MS, sans-serif" font-weight="700" font-size="104" fill="#000" opacity=".22">${t}</text>
<text x="200" y="166" text-anchor="middle" font-family="Fredoka, Trebuchet MS, sans-serif" font-weight="700" font-size="104" fill="#fff">${t}</text>
</svg>`;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

export function coverSrc(g) { return g.cover || generatedCover(g); }

// ---------------------------------------------------------------------------
// Données locales du joueur. Toutes les lectures/écritures sont protégées :
// navigation privée ou stockage bloqué ⇒ le site fonctionne sans mémoire.
const KEY = 'kotiontwin:v1';
function readStore() {
  try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch { return {}; }
}
function writeStore(s) {
  try { localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* stockage indisponible */ }
}
export const store = {
  get favorites() { return readStore().favorites || []; },
  isFavorite(id) { return this.favorites.includes(id); },
  toggleFavorite(id) {
    const s = readStore(); const f = new Set(s.favorites || []);
    f.has(id) ? f.delete(id) : f.add(id);
    s.favorites = [...f]; writeStore(s); return f.has(id);
  },
  get recent() { return readStore().recent || []; },
  markPlayed(id) {
    const s = readStore();
    s.recent = [id, ...(s.recent || []).filter(x => x !== id)].slice(0, 12);
    writeStore(s);
  },
  scores(id) { return (readStore().scores || {})[id] || []; },
  best(id) { return this.scores(id)[0] || null; },
  addScore(id, score, extra = {}) {
    const n = Number(score);
    if (!Number.isFinite(n)) return null;
    const s = readStore(); s.scores ||= {};
    const list = s.scores[id] || [];
    const entry = { score: n, date: new Date().toISOString(), ...extra };
    list.push(entry);
    list.sort((a, b) => b.score - a.score);
    s.scores[id] = list.slice(0, 10);
    writeStore(s);
    return { entry, rank: s.scores[id].indexOf(entry) + 1 };
  },
  clearScores(id) { const s = readStore(); if (s.scores) delete s.scores[id]; writeStore(s); },
  get theme() { return readStore().theme || null; },
  set theme(v) { const s = readStore(); s.theme = v; writeStore(s); },
};

// Thème clair/sombre choisi par le joueur (sinon celui du système).
export function applyTheme() {
  const t = store.theme;
  if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme;
}
export function bindThemeToggle(btn) {
  if (!btn) return;
  const isDark = () => (document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark')) === 'dark';
  const label = () => {
    btn.setAttribute('aria-label', isDark() ? 'Passer au thème clair' : 'Passer au thème sombre');
    btn.textContent = isDark() ? '☀' : '☾';
  };
  btn.addEventListener('click', () => { store.theme = isDark() ? 'light' : 'dark'; applyTheme(); label(); });
  label();
}

export function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') n.className = v;
    else if (k === 'style') n.style.cssText = v;
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? '' : v);
  }
  for (const k of kids.flat()) if (k != null && k !== false) n.append(k instanceof Node ? k : document.createTextNode(String(k)));
  return n;
}

export const fmtScore = n => Number(n).toLocaleString('fr-FR');
export const fmtDate = iso => new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });
