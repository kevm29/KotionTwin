// Accès partagé au catalogue (data/games.json).
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

export async function loadCatalog() {
  const res = await fetch('data/games.json', { cache: 'no-cache' });
  if (!res.ok) throw new Error('Catalogue introuvable');
  return res.json();
}

const PALETTE = ['#5b3fd1', '#c23a7a', '#1f8a70', '#d9822b', '#2e6fd8', '#8e44ad', '#b03a2e', '#138d90'];
export function placeholderColor(id) {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

export function initials(title) {
  const w = title.replace(/\(.*?\)/g, '').trim().split(/[\s-]+/).filter(Boolean);
  return (w.length > 1 ? w[0][0] + w[1][0] : title.slice(0, 2)).toUpperCase();
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
  for (const k of kids.flat()) if (k != null) n.append(k instanceof Node ? k : document.createTextNode(String(k)));
  return n;
}
