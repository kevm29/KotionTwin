// Hôte commun des jeux Flash 8 « autonomes » (Pioupiouz, Miniville, Alphabounce, Dinocard).
// Charge Ruffle (copie locale vendor/ruffle si présente, sinon CDN épinglé) et crée un lecteur.
const RUFFLE_CDN = 'https://cdn.jsdelivr.net/npm/@ruffle-rs/ruffle@0.7.1/ruffle.js';

function loadScript(src) {
  return new Promise((ok, ko) => {
    const s = document.createElement('script');
    s.src = src; s.onload = ok; s.onerror = () => { s.remove(); ko(new Error('échec ' + src)); };
    document.head.append(s);
  });
}

export async function ensureRuffle(root = '../../') {
  if (window.RufflePlayer?.newest) return;
  try { await loadScript(root + 'vendor/ruffle/ruffle.js'); } catch { await loadScript(RUFFLE_CDN); }
}

// Les jeux utilisent BitmapData.draw : il faut le moteur wgpu (WebGPU ou WebGL 2),
// le moteur « webgl » historique et le moteur « canvas » ne savent pas le faire.
export async function mount(container, { swf, base, flashvars = {}, bgcolor = '#000000', config = {}, root }) {
  await ensureRuffle(root);
  window.RufflePlayer.config = {
    autoplay: 'on', unmuteOverlay: 'hidden', splashScreen: false, letterbox: 'on',
    warnOnUnsupportedContent: false, showSwfDownload: false, contextMenu: 'rightClickOnly',
    preferredRenderer: 'wgpu-webgl', allowScriptAccess: true, ...config,
  };
  const player = window.RufflePlayer.newest().createPlayer();
  player.style.width = '100%';
  player.style.height = '100%';
  container.replaceChildren(player);
  await player.ruffle().load({ url: swf, base, parameters: flashvars, backgroundColor: bgcolor, allowScriptAccess: true });
  return player;
}

export const store = {
  get(key, def) { try { const v = localStorage.getItem(key); return v == null ? def : JSON.parse(v); } catch { return def; } },
  set(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch { /* navigation privée */ } },
};

export function h(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? '' : v);
  }
  e.append(...kids.flat().filter(x => x != null && x !== false));
  return e;
}
