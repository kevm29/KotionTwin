import { loadCatalog, STATUS, PLAN, el } from './data.js';

// Version de Ruffle épinglée (voir README) ; un dossier vendor/ruffle local est utilisé s'il existe.
const RUFFLE_CDN = 'https://cdn.jsdelivr.net/npm/@ruffle-rs/ruffle@0.7.1/ruffle.js';
const RUFFLE_LOCAL = 'vendor/ruffle/ruffle.js';

function loadScript(src) {
  return new Promise((ok, ko) => {
    const s = document.createElement('script');
    s.src = src; s.onload = ok; s.onerror = () => ko(new Error('échec ' + src));
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
    autoplay: 'on', unmuteOverlay: 'visible', splashScreen: false, letterbox: 'on',
    warnOnUnsupportedContent: false, showSwfDownload: false, contextMenu: 'rightClickOnly',
    ...(e.config || {}),
  };
  const player = window.RufflePlayer.newest().createPlayer();
  sizeTo(player, e);
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
  sizeTo(f, e);
  stage.replaceChildren(f);
  return f;
}

function sizeTo(node, e) {
  const w = e.width || 800, h = e.height || 600;
  const fit = () => {
    const max = Math.min(node.parentElement?.clientWidth || w, w * (e.scale || 2));
    const s = Math.min(max / w, (innerHeight * 0.8) / h, e.scale || 2);
    node.style.width = Math.floor(w * Math.max(s, 0.3)) + 'px';
    node.style.height = Math.floor(h * Math.max(s, 0.3)) + 'px';
  };
  requestAnimationFrame(fit);
  addEventListener('resize', fit);
}

function notYet(stage, g) {
  stage.replaceChildren(el('div', { class: 'notyet' },
    g.thumb ? el('img', { src: g.thumb, alt: `Capture d'origine de ${g.title}` }) : null,
    el('h2', {}, STATUS[g.status] || 'À restaurer'),
    el('p', {}, 'Ce jeu n\'est pas encore jouable sur KotionTwin.'),
    el('p', {}, 'Méthode prévue : ', PLAN[g.plan] || g.plan, '.')));
}

async function main() {
  const id = new URLSearchParams(location.search).get('g');
  const { collections, games } = await loadCatalog();
  const g = games.find(x => x.id === id);
  const stage = document.getElementById('stage');
  if (!g) {
    document.getElementById('title').textContent = 'Jeu introuvable';
    stage.replaceChildren(el('div', { class: 'notyet' }, el('p', {}, 'Ce jeu n\'existe pas dans le catalogue. '), el('a', { href: './' }, 'Retour au catalogue')));
    return;
  }
  document.title = `${g.title} · KotionTwin`;
  document.getElementById('title').textContent = g.title;
  document.getElementById('meta').textContent = [collections[g.collection]?.name, g.year].filter(Boolean).join(' · ');
  document.getElementById('desc').textContent = g.description || collections[g.collection]?.about || '';
  if (g.controls) document.getElementById('controls').replaceChildren(el('p', {}, el('strong', {}, 'Commandes : '), g.controls));
  const src = `https://github.com/motion-twin/WebGamesArchives/tree/master/${g.source.split('/').map(encodeURIComponent).join('/')}`;
  document.getElementById('srclink').href = src;
  const rows = [
    ['État', STATUS[g.status] || g.status],
    ['Technologie', g.tech],
    ['Restauration', PLAN[g.plan] || g.plan],
    ['Notes', g.notes],
    ['Sources', el('a', { href: src }, g.source)],
    ['Crédits', g.credits || 'Motion Twin'],
  ];
  document.getElementById('tech').replaceChildren(...rows.filter(r => r[1]).flatMap(([k, v]) => [el('dt', {}, k), el('dd', {}, v)]));

  if (g.status === 'jouable' && g.entry) {
    try {
      const node = g.entry.type === 'html' ? mountHtml(stage, g.entry) : await mountRuffle(stage, g.entry);
      const fs = document.getElementById('fs');
      fs.hidden = false;
      fs.onclick = () => (node.enterFullscreen ? node.enterFullscreen() : node.requestFullscreen?.());
    } catch (err) {
      stage.replaceChildren(el('div', { class: 'notyet' }, el('h2', {}, 'Le jeu n\'a pas pu démarrer'), el('p', {}, String(err.message || err))));
    }
  } else {
    notYet(stage, g);
  }
}
main();
