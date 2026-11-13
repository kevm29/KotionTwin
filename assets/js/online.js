// Classement en ligne partagé entre tous les joueurs (Supabase, API REST, sans bibliothèque).
// Désactivé tant que data/online.json ne contient pas l'URL du projet et la clé publique « anon ».
let cfgPromise;
function config() {
  cfgPromise ||= fetch('data/online.json', { cache: 'no-cache' })
    .then(r => (r.ok ? r.json() : {}))
    .then(c => (c.supabaseUrl && c.anonKey ? { url: c.supabaseUrl.replace(/\/+$/, ''), key: c.anonKey } : null))
    .catch(() => null);
  return cfgPromise;
}
const headers = c => ({ apikey: c.key, Authorization: `Bearer ${c.key}`, 'Content-Type': 'application/json' });

export async function onlineEnabled() { return !!(await config()); }

export async function submitOnline(game, pseudo, score) {
  const c = await config();
  if (!c || !pseudo || !Number.isFinite(score) || score < 0) return false;
  const r = await fetch(`${c.url}/rest/v1/scores`, {
    method: 'POST',
    headers: { ...headers(c), Prefer: 'return=minimal' },
    body: JSON.stringify({ game, pseudo, score: Math.floor(score) }),
  });
  return r.ok;
}

// Meilleur score de chaque joueur pour un jeu, du plus haut au plus bas.
export async function topOnline(game, limit = 10) {
  const c = await config();
  if (!c) return null;
  const q = new URLSearchParams({ game: `eq.${game}`, select: 'pseudo,score,created_at', order: 'score.desc', limit: '200' });
  const r = await fetch(`${c.url}/rest/v1/scores?${q}`, { headers: headers(c) });
  if (!r.ok) throw new Error(`classement indisponible (${r.status})`);
  const seen = new Set(), out = [];
  for (const row of await r.json()) {
    const k = row.pseudo.toLowerCase();
    if (seen.has(k)) continue;
    seen.add(k); out.push(row);
    if (out.length >= limit) break;
  }
  return out;
}
