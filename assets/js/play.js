import { loadCatalog, STATUS, PLAN, styleOf, coverSrc, store, el, fmtScore, fmtDate, pseudoError } from './data.js';
import { submitOnline, topOnline, onlineEnabled } from './online.js';
import { shelf, gameUrl, collectionUrl, sortGames, renderPlayerChip } from './ui.js';

// Version de Ruffle épinglée (voir README) ; un dossier vendor/ruffle local est utilisé s'il existe.
const RUFFLE_CDN = 'https://cdn.jsdelivr.net/npm/@ruffle-rs/ruffle@0.7.1/ruffle.js';
const RUFFLE_LOCAL = 'vendor/ruffle/ruffle.js';
const $ = id => document.getElementById(id);
const isTouch = matchMedia('(pointer: coarse)').matches;

function loadScript(src) {
  return new Promise((ok, ko) => {
    const s = document.createElement('script');
    s.src = src; s.onload = ok; s.onerror = () => { s.remove(); ko(new Error('échec du chargement de ' + src)); };
    document.head.append(s);
  });
}
async function ensureRuffle() {
  if (window.RufflePlayer?.newest) return;
  try { await loadScript(RUFFLE_LOCAL); } catch { await loadScript(RUFFLE_CDN); }
}

/*
 * Format de g.entry (rempli par les threads de restauration) :
 *  { "type": "ruffle", "swf": "games/<id>/loader.swf", "width": 300, "height": 320,
 *    "flashvars": { "swf": "game.swf" }, "base": "games/<id>/", "bgcolor": "#ffffff",
 *    "config": { ... options Ruffle supplémentaires ... } }
 *  { "type": "html", "url": "games/<id>/index.html", "width": 800, "height": 600 }
 */
async function mountRuffle(stage, e) {
  await ensureRuffle();
  window.RufflePlayer.config = {
    autoplay: 'on', unmuteOverlay: 'hidden', splashScreen: false, letterbox: 'on',
    warnOnUnsupportedContent: false, showSwfDownload: false, contextMenu: 'rightClickOnly',
    ...(e.config || {}),
  };
  const player = window.RufflePlayer.newest().createPlayer();
  player.setAttribute('tabindex', '0');
  player.setAttribute('aria-label', 'Jeu Flash');
  stage.replaceChildren(player);
  await player.ruffle().load({
    url: e.swf,
    base: e.base,
    parameters: e.flashvars || {},
    backgroundColor: e.bgcolor || null,
    allowScriptAccess: true,
  });
  return player;
}

function mountHtml(stage, e) {
  const f = el('iframe', { src: e.url, title: 'Jeu', allow: 'autoplay; fullscreen; gamepad' });
  stage.replaceChildren(f);
  return f;
}

// Adapte le lecteur à la place disponible en gardant les proportions d'origine.
let currentNode, setPad;
let ctl; // listeners du lecteur courant (remplacés à chaque « Recommencer »)
function fitter(node, e, sig) {
  const w = e.width || 800, h = e.height || 600;
  const wrap = $('stage-wrap');
  const fit = () => {
    const full = document.fullscreenElement === wrap || wrap.classList.contains('pseudo-full');
    const availW = full ? innerWidth : wrap.clientWidth;
    const availH = full ? innerHeight : Math.max(240, innerHeight * (isTouch ? 0.62 : 0.78));
    const maxScale = full ? Infinity : (e.scale || 2);
    const s = Math.max(0.3, Math.min(availW / w, availH / h, maxScale));
    node.style.width = Math.floor(w * s) + 'px';
    node.style.height = Math.floor(h * s) + 'px';
  };
  fit();
  addEventListener('resize', fit, sig);
  document.addEventListener('fullscreenchange', fit, sig);
  return fit;
}

function toast(msg) {
  const t = $('toast');
  t.textContent = msg; t.hidden = false; t.classList.add('show');
  clearTimeout(toast.t);
  toast.t = setTimeout(() => { t.classList.remove('show'); setTimeout(() => { t.hidden = true; }, 300); }, 3200);
}

// ---------------------------------------------------------------------------
// API de scores exposée aux jeux.
//  - Flash (Ruffle) : ExternalInterface.call("KotionTwin.submitScore", score) ou "ktSubmitScore".
//    ExternalInterface.call("ktGetBest") renvoie le record local (ou null).
//  - HTML5 (iframe) : parent.postMessage({ type: "kotiontwin:score", score: 1234 }, "*").
//  - Tout autre code de la page : window.KotionTwin.submitScore(1234).
function installScoreApi(g) {
  const submit = (score, extra) => {
    const r = store.addScore(g.id, score, extra && typeof extra === 'object' ? extra : {});
    if (!r) return false;
    renderScores(g);
    submitOnline(g.id, store.pseudo, r.entry.score).then(ok => { if (ok) renderOnline(g); }).catch(() => {});
    if (r.rank === 1 && store.scores(g.id).length > 1) toast(`Nouveau record : ${fmtScore(r.entry.score)} !`);
    else if (r.rank <= 10) toast(`Score enregistré : ${fmtScore(r.entry.score)} (n° ${r.rank})`);
    return true;
  };
  const api = {
    gameId: g.id,
    submitScore: submit,
    getBest: () => store.best(g.id)?.score ?? null,
    getScores: () => store.scores(g.id).map(s => s.score),
    getPlayer: () => store.pseudo,
  };
  window.KotionTwin = api;
  window.ktSubmitScore = submit;
  window.ktGetBest = api.getBest;
  window.ktGetPlayer = api.getPlayer;
  addEventListener('message', ev => {
    const d = ev.data;
    if (d && typeof d === 'object' && d.type === 'kotiontwin:score') submit(d.score, d.extra);
  });
}

function renderScores(g) {
  const list = store.scores(g.id);
  $('scores').replaceChildren(...list.map((s, i) => el('li', {},
    el('span', { class: 'rank' }, i === 0 ? '🏆' : `${i + 1}.`),
    el('span', { class: 'who' }, el('b', {}, fmtScore(s.score)), el('span', { class: 'pname' }, s.name || 'Anonyme')),
    el('span', { class: 'muted small' }, fmtDate(s.date)))));
  $('scores-empty').hidden = list.length > 0;
  $('scores-clear').hidden = list.length === 0;
}

async function renderOnline(g) {
  if (!(await onlineEnabled())) return;
  const panel = $('online-panel'), msg = $('online-msg');
  panel.hidden = false;
  try {
    const rows = await topOnline(g.id, 10);
    const me = store.pseudo.toLowerCase();
    $('online').replaceChildren(...rows.map((s, i) => el('li', { class: s.pseudo.toLowerCase() === me ? 'me' : null },
      el('span', { class: 'rank' }, i === 0 ? '🏆' : `${i + 1}.`),
      el('span', { class: 'who' }, el('b', {}, fmtScore(s.score)), el('span', { class: 'pname' }, s.pseudo)),
      el('span', { class: 'muted small' }, fmtDate(s.created_at)))));
    msg.textContent = rows.length ? 'Meilleur score de chaque joueur, tous appareils confondus.' : 'Personne n\'a encore de score en ligne : à toi de jouer !';
  } catch (e) {
    $('online').replaceChildren();
    msg.textContent = 'Classement en ligne momentanément indisponible.';
  }
}

// ---------------------------------------------------------------------------
// Manette tactile : envoie de vrais événements clavier au lecteur.
function bindPad(getTarget) {
  const pad = $('pad');
  const send = (type, btn) => {
    const key = btn.dataset.key;
    const code = btn.dataset.code || key;
    const init = { key, code, bubbles: true, cancelable: true, composed: true };
    const t = getTarget();
    t?.dispatchEvent(new KeyboardEvent(type, init));
    if (t !== document) document.dispatchEvent(new KeyboardEvent(type, init));
  };
  for (const b of pad.querySelectorAll('button')) {
    b.tabIndex = -1;
    const down = ev => { ev.preventDefault(); b.classList.add('on'); send('keydown', b); };
    const up = ev => { ev.preventDefault(); if (!b.classList.contains('on')) return; b.classList.remove('on'); send('keyup', b); };
    b.addEventListener('pointerdown', down);
    b.addEventListener('pointerup', up);
    b.addEventListener('pointercancel', up);
    b.addEventListener('pointerleave', up);
    b.addEventListener('contextmenu', ev => ev.preventDefault());
  }
  const btn = $('padbtn');
  const set = on => { pad.hidden = !on; btn.setAttribute('aria-pressed', String(on)); };
  btn.addEventListener('click', () => set(pad.hidden));
  return set;
}

const usesKeyboard = g => /clavier|fl[eè]ches|espace|touche|entr[ée]e|\bzqsd\b/i.test(g.controls || '');

// ---------------------------------------------------------------------------
function launchScreen(stage, g, onStart) {
  const st = styleOf(g.collection);
  const hint = el('p', { class: 'small' }, isTouch && usesKeyboard(g) ? 'Ce jeu se joue au clavier : une manette tactile est proposée.' : 'Le son démarre avec la partie.');
  const box = el('div', { class: 'launch-in' },
    el('img', { class: 'launch-cover' + (g.coverPixel ? ' pixel' : ''), src: coverSrc(g), alt: `Vignette de ${g.title}` }));
  stage.replaceChildren(el('div', { class: 'launch', style: `--hue:${st.hue};--deep:${st.deep}` },
    el('img', { class: 'launch-bg', src: coverSrc(g), alt: '' }), box));

  const ready = () => {
    const btn = el('button', { class: 'launch-btn', type: 'button' }, el('span', { 'aria-hidden': 'true' }, '▶'), ' Lancer la partie');
    btn.addEventListener('click', onStart, { once: true });
    box.replaceChildren(box.firstChild, btn,
      el('p', { class: 'small launch-player' }, 'Joueur : ', el('b', {}, store.pseudo), ' · ', el('a', { href: `settings.html?retour=${encodeURIComponent(location.pathname.split('/').pop() + location.search)}` }, 'changer')),
      hint);
    btn.focus({ preventScroll: true });
  };
  if (store.pseudo) { ready(); return; }

  // Pas de pseudo : on le demande ici même, il est obligatoire pour jouer (il accompagne les scores).
  const input = el('input', { id: 'launch-pseudo', type: 'text', maxlength: '16', autocomplete: 'nickname', required: true, placeholder: 'Ton pseudo', 'aria-describedby': 'launch-err' });
  const err = el('p', { class: 'error', id: 'launch-err', role: 'alert', hidden: true });
  const form = el('form', { class: 'launch-form', novalidate: true },
    el('label', { for: 'launch-pseudo' }, 'Choisis un pseudo pour jouer'),
    el('div', { class: 'pseudo-row' }, input, el('button', { class: 'launch-btn small', type: 'submit' }, el('span', { 'aria-hidden': 'true' }, '▶'), ' Jouer')),
    err,
    el('p', { class: 'small' }, 'Il s\'affiche avec tes scores et se modifie dans les ', el('a', { href: 'settings.html' }, 'Paramètres'), '.'));
  form.addEventListener('submit', e => {
    e.preventDefault();
    const msg = pseudoError(input.value);
    err.hidden = !msg; err.textContent = msg || '';
    input.setAttribute('aria-invalid', String(!!msg));
    if (msg) { input.focus(); return; }
    store.pseudo = input.value;
    renderPlayerChip();
    onStart(); // le clic sur « Jouer » compte comme geste utilisateur : le son peut démarrer
  });
  box.replaceChildren(box.firstChild, form);
  input.focus({ preventScroll: true });
}

function notYet(stage, g) {
  const st = styleOf(g.collection);
  stage.replaceChildren(el('div', { class: 'notyet', style: `--hue:${st.hue};--deep:${st.deep}` },
    el('img', { class: 'notyet-cover' + (g.coverPixel ? ' pixel' : ''), src: coverSrc(g), alt: `Vignette de ${g.title}` }),
    el('div', {},
      el('span', { class: 'badge big ' + g.status }, STATUS[g.status] || 'À restaurer'),
      el('h2', {}, g.status === 'en-cours' ? 'Restauration en cours' : 'Pas encore jouable'),
      el('p', {}, g.status === 'en-cours'
        ? 'Ce jeu est en cours de restauration : il sera jouable dès qu\'il aura passé toutes les vérifications (images, sons, partie complète).'
        : 'Ce jeu fait partie de l\'archive mais n\'a pas encore été restauré.'),
      el('p', { class: 'muted' }, 'Méthode prévue : ', PLAN[g.plan] || g.plan, '.'),
      el('a', { class: 'btn ghost', href: collectionUrl(g.collection) }, 'Voir les autres jeux ', g.collectionName ? `de ${g.collectionName}` : ''))));
}

async function start(g) {
  const stage = $('stage');
  const e = g.entry;
  ctl?.abort();
  ctl = new AbortController();
  const sig = { signal: ctl.signal };
  stage.replaceChildren(el('div', { class: 'loading' }, el('span', { class: 'spinner', 'aria-hidden': 'true' }), 'Chargement du jeu…'));
  let node;
  try {
    node = e.type === 'html' ? mountHtml(stage, e) : await mountRuffle(stage, e);
  } catch (err) {
    stage.replaceChildren(el('div', { class: 'notyet' }, el('div', {},
      el('h2', {}, 'Le jeu n\'a pas pu démarrer'), el('p', {}, String(err.message || err)),
      el('button', { class: 'btn primary', type: 'button', onclick: () => start(g) }, 'Réessayer'))));
    return;
  }
  store.markPlayed(g.id);
  const fit = fitter(node, e, sig);
  $('stage-bar').hidden = false;
  node.focus?.({ preventScroll: true });

  // Plein écran sur le conteneur (la manette tactile reste visible) ; repli CSS sur iOS.
  const wrap = $('stage-wrap');
  const toggleFs = async () => {
    if (document.fullscreenElement) { await document.exitFullscreen(); return; }
    if (wrap.classList.contains('pseudo-full')) { wrap.classList.remove('pseudo-full'); document.body.classList.remove('no-scroll'); fit(); return; }
    if (wrap.requestFullscreen) {
      try { await wrap.requestFullscreen({ navigationUI: 'hide' }); screen.orientation?.lock?.('landscape').catch(() => {}); return; } catch { /* repli */ }
    }
    wrap.classList.add('pseudo-full'); document.body.classList.add('no-scroll'); fit();
  };
  $('fs').onclick = toggleFs;
  document.addEventListener('fullscreenchange', () => {
    $('fs').querySelector('.lbl').textContent = document.fullscreenElement ? 'Quitter' : 'Plein écran';
  }, sig);

  // Son : volume de Ruffle (les iframes HTML5 gèrent leur propre son).
  const mute = $('mute');
  if (e.type === 'html') mute.hidden = true;
  else mute.onclick = () => {
    const r = node.ruffle?.() ?? node;
    const on = mute.getAttribute('aria-pressed') !== 'true';
    try { r.volume = on ? 0 : 1; } catch { node.volume = on ? 0 : 1; }
    mute.setAttribute('aria-pressed', String(on));
    mute.querySelector('.ico').textContent = on ? '🔇' : '🔊';
    mute.querySelector('.lbl').textContent = on ? 'Muet' : 'Son';
  };

  $('restart').onclick = () => start(g);

  currentNode = node;
  setPad ||= bindPad(() => currentNode);
  $('padbtn').hidden = !isTouch && !usesKeyboard(g);
  if (isTouch && usesKeyboard(g) && store.padAuto) setPad(true);

  addEventListener('keydown', ev => {
    if (ev.target.closest?.('input, textarea, select')) return;
    if (ev.target === node || node.contains?.(ev.target)) return; // les touches vont au jeu
    if (ev.key === 'f' || ev.key === 'F') { ev.preventDefault(); toggleFs(); }
    if (ev.key === 'm' || ev.key === 'M') { ev.preventDefault(); mute.click(); }
    if (ev.key === 'Escape' && wrap.classList.contains('pseudo-full')) toggleFs();
  }, sig);
}

async function main() {
  const id = new URLSearchParams(location.search).get('g');
  const { collections, games } = await loadCatalog();
  const g = games.find(x => x.id === id);
  const stage = $('stage');
  if (!g) {
    $('title').textContent = 'Jeu introuvable';
    stage.replaceChildren(el('div', { class: 'notyet' }, el('div', {}, el('p', {}, 'Ce jeu n\'existe pas dans le catalogue.'), el('a', { class: 'btn primary', href: './' }, 'Retour au catalogue'))));
    document.querySelector('.cols').hidden = true;
    return;
  }
  const coll = collections[g.collection];
  g.collectionName = coll?.name;
  const st = styleOf(g.collection);
  document.body.style.setProperty('--hue', st.hue);
  document.body.style.setProperty('--deep', st.deep);
  document.title = `${g.title} · KotionTwin`;
  $('title').textContent = g.title;
  $('crumb').textContent = g.title;
  $('crumb-coll').textContent = coll?.name || 'Collection';
  $('crumb-coll').href = collectionUrl(g.collection);
  $('meta').replaceChildren(
    el('a', { href: collectionUrl(g.collection) }, coll?.name || g.collection),
    g.year ? ` · ${g.year}` : '',
    ' · ', el('span', { class: 'badge inline ' + g.status }, STATUS[g.status] || g.status));
  $('desc').textContent = g.description || coll?.about || '';
  if (g.controls) $('controls').replaceChildren(el('p', { class: 'controls' }, el('strong', {}, 'Commandes : '), g.controls));
  const src = `https://github.com/motion-twin/WebGamesArchives/tree/master/${g.source.split('/').map(encodeURIComponent).join('/')}`;
  $('srclink').href = src;
  const rows = [
    ['État', STATUS[g.status] || g.status],
    ['Technologie', g.tech],
    ['Restauration', PLAN[g.plan] || g.plan],
    ['Taille d\'origine', g.entry?.width ? `${g.entry.width} × ${g.entry.height} px` : null],
    ['Notes', g.notes],
    ['Sources', el('a', { href: src }, g.source)],
    ['Crédits', g.credits || 'Motion Twin'],
  ];
  $('tech').replaceChildren(...rows.filter(r => r[1]).flatMap(([k, v]) => [el('dt', {}, k), el('dd', {}, v)]));

  // Favori et partage.
  const fav = $('fav');
  const syncFav = () => { const on = store.isFavorite(g.id); fav.setAttribute('aria-pressed', String(on)); fav.querySelector('.lbl').textContent = on ? 'Favori ✓' : 'Favori'; };
  fav.onclick = () => { store.toggleFavorite(g.id); syncFav(); };
  syncFav();
  $('share').onclick = async () => {
    const url = location.href;
    try {
      if (navigator.share && isTouch) await navigator.share({ title: `${g.title} · KotionTwin`, url });
      else { await navigator.clipboard.writeText(url); toast('Lien copié dans le presse-papiers'); }
    } catch { /* partage annulé */ }
  };

  // Scores.
  installScoreApi(g);
  renderScores(g);
  $('scores-clear').onclick = () => { store.clearScores(g.id); renderScores(g); toast('Scores effacés'); };
  if (g.status !== 'jouable') $('scores-panel').hidden = true;
  else renderOnline(g);

  // Jeux voisins dans la collection.
  const siblings = sortGames(games.filter(x => x.collection === g.collection), 'title');
  const i = siblings.indexOf(g);
  const prev = siblings[(i - 1 + siblings.length) % siblings.length];
  const next = siblings[(i + 1) % siblings.length];
  if (siblings.length > 1) {
    $('pager').replaceChildren(
      el('a', { class: 'pager-link prev', href: gameUrl(prev), rel: 'prev' }, el('span', { class: 'muted small' }, '← Précédent'), el('b', {}, prev.title)),
      el('a', { class: 'pager-link next', href: gameUrl(next), rel: 'next' }, el('span', { class: 'muted small' }, 'Suivant →'), el('b', {}, next.title)));
  }
  const related = sortGames(siblings.filter(x => x !== g), 'status').slice(0, 12);
  const rel = shelf(`Dans la collection ${coll?.name || ''}`, related, { collections, showCollection: false },
    el('a', { class: 'more', href: collectionUrl(g.collection) }, 'Tout voir →'));
  if (rel) $('related').replaceChildren(rel);

  if (g.status === 'jouable' && g.entry) {
    if (isTouch && usesKeyboard(g)) {
      $('hint').hidden = false;
      $('hint').textContent = 'Astuce : tournez votre téléphone à l\'horizontale et passez en plein écran pour plus de confort.';
    }
    launchScreen(stage, g, () => start(g));
  } else {
    notYet(stage, g);
  }
}
main().catch(err => {
  $('title').textContent = 'Erreur';
  $('stage').replaceChildren(el('div', { class: 'notyet' }, el('p', {}, String(err.message || err))));
});
