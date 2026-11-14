// Serveur Alphabounce simulé dans le navigateur.
// Le client d'origine (game.swf, version « prod ») dialogue avec /play/intercom en envoyant
// une requête _ServerRequest sérialisée (haxe.Serializer) ; on intercepte fetch() pour lui
// répondre. La logique reprend l'« émulation serveur » laissée par Motion Twin dans
// client/src/Api.hx et com/PlayerInfo.hx (addItem, buyShopItem, checkMission…).
import { serialize, unserialize, E } from '../../platforms/flash8/haxeser.js';
import { encode as persist } from '../../platforms/flash8/persistcodec.js';
import { store } from '../../platforms/flash8/kt-host.js';

const KEY = 'kt.alphabounce.save';
const R = (tag, ...args) => E('_ServerResponse', tag, ...args);

export async function createServer(onEvent = () => {}) {
  const D = await (await fetch('data.json')).json();
  const M = D.MissionInfo, S = D.ShopInfo;

  // ---------------------------------------------------------------- état du joueur
  const fresh = () => ({
    pid: Math.floor(Math.random() * 200), x: 0, y: 0, ox: 0, oy: 0,
    chl: 3, chs: 0, minerai: 0, missions: [0], missile: 0, missileMax: 0,
    engine: 1, radar: 1, life: 3, drone: 0,
    items: [M.TRIGGER], shopItems: [], comp: new Array(D.planets.length).fill(0),
    travel: [], visited: { '0,0': 1 }, mined: {}, landed: {}, houses: [],
  });
  let P = null;
  function save() { store.set(KEY, P); onEvent('save', P); }

  // ---------------------------------------------------------------- règles (PlayerInfo.hx)
  const gotItem = n => P.items[n] === M.COLLECTED || P.items[n] === M.COLLECTED_INV;
  function addItem(id) {
    if (id == null || id < 0) return;
    P.items[id] = P.items[id] === M.TRIGGER ? M.COLLECTED_INV : M.COLLECTED;
    if (id >= M.MISSILE && id < M.MISSILE + M.MISSILE_MAX) { P.missileMax++; P.missile = P.missileMax; }
    if (id === M.SUPER_RADAR) P.radar++;
  }
  function addStuff(a) {
    switch (a[0]) {
      case M.MINERAI: P.minerai += a[1]; break;
      case M.NEW_LIFE: P.life++; break;
      case M.LOSS_LIFE: P.life--; break;
      case M.NEW_RADAR: P.radar++; break;
      case M.LOSS_RADAR: P.radar--; break;
      case M.RESET_MISSION: P.missions[a[1]] = null; break;
      case M.CHS: P.chs += a[1] ?? 1; break;
      case M.ENABLE_LEVEL_MISSIONS: case M.ENABLE_REBEL_MISSIONS: case M.DISABLE_LEVEL_MISSIONS: break;
      default: P.items[a[0]] = a[1];
    }
  }
  const dist = (a) => Math.hypot(a[1] - P.x, a[2] - P.y);
  function condOk(a) {
    switch (a[0]) {
      case M.GOT_ITEM: return a.slice(1).every(gotItem);
      case M.NOT_ITEM: return !gotItem(a[1]);
      case M.GOT_SHOPITEM: return a.slice(1).every(n => P.shopItems[n] === 1);
      case M.GOT_PLANET: return (P.comp[a[1]] ?? 0) >= 100;
      case M.GOT_MINERAI: return a[1] <= P.minerai;
      case M.ENTER_ZONE: return dist(a) <= a[3];
      case M.LEAVE_ZONE: return dist(a) > a[3];
      case M.GOT_MISSION: return P.missions[a[1]] === 1;
      case M.GOT_MISSILE: return P.missileMax >= (a[1] ?? 1);
      case M.IS_LEVEL: return false;
    }
    return true;
  }
  function checkMission() {
    D.missions.forEach((mi, n) => {
      if (P.missions[n] === 0 && mi.conditions.every(condOk)) {
        P.missions[n] = 1; mi.endItem.forEach(addStuff); onEvent('mission', n);
      }
    });
    D.missions.forEach((mi, n) => {
      if (P.missions[n] == null && mi.startConditions.every(condOk)) {
        P.missions[n] = 0; mi.startItem.forEach(addStuff);
      }
    });
  }
  // mt.OldRandom (libs-haxe2/mt/OldRandom.hx), utilisé pour les prix de la boutique
  function oldRandom(seed) {
    const prec = 55, vals = []; let idx = 0;
    for (let i = 0; i < prec; i++) {
      seed = Math.trunc(seed * 1103515245.0) & 0x3FFFFFFF; seed = (seed + 12345) & 0x3FFFFFFF;
      const sbig = seed & 0x3FFF0000;
      seed = Math.trunc(seed * 1103515245.0) & 0x3FFFFFFF; seed = (seed + 12345) & 0x3FFFFFFF;
      vals.push((seed >> 16) | sbig);
    }
    const int = () => { idx = (idx + 1) % prec; const v = (vals[(idx + 24) % prec] + idx) & 0x3FFFFFFF; vals[idx] = v; return v; };
    return { random: m => int() % m, rand: () => (int() % 1000) / 1000 };
  }
  function price(id) {
    let p = id === S.AMMO ? P.missileMax - P.missile
      : id === S.DRONE ? Math.trunc(Math.pow(P.drone + 6, 4) / 100) * 100 : D.shop[id];
    const seed = oldRandom(Math.trunc(Math.abs(P.x) * 10000) + Math.trunc(Math.abs(P.y) + id * 20));
    const sens = seed.random(2) * 2 - 1; const c = Math.pow(seed.rand(), 4);
    return p + Math.trunc(p * 0.5 * c * sens);
  }
  function buyShopItem(id) {
    const cost = price(id);
    if (id === S.CHS) P.chs++;
    else if (id === S.AMMO) P.missile = P.missileMax;
    else {
      P.shopItems[id] = 1;
      if (id === S.LIFE) P.life++;
      if (id === S.DRONE) P.drone++;
      if (id === S.RADAR) { P.radar++; addItem(M.RADAR_OK); }
      if (id >= S.ENGINE && id < S.ENGINE + S.ENGINE_MAX) P.engine = Math.max(P.engine, 2 + id - S.ENGINE);
      if (id >= S.MISSILE && id < S.MISSILE + 3) { P.missileMax++; P.missile = P.missileMax; }
    }
    P.minerai -= cost;
  }
  // planètes (ZoneInfo.getPlanet, liste « web »)
  const inCircle = (x, y, cx, cy, r) => Math.hypot(cx - x - 0.5, cy - y - 0.5) <= r + 0.3;
  function planetAt(x, y) {
    for (let id = 0; id < D.planets.length; id++) {
      const [cx, cy, r] = D.planets[id].pos;
      if (x >= cx - r && x <= cx + r - 1 && y >= cy - r && y <= cy + r - 1) return inCircle(x, y, cx, cy, r) ? id : null;
    }
    return null;
  }
  function planetSquares(id) {
    const [cx, cy, r] = D.planets[id].pos; let n = 0;
    for (let x = cx - r; x <= cx + r - 1; x++) for (let y = cy - r; y <= cy + r - 1; y++) if (inCircle(x, y, cx, cy, r)) n++;
    return Math.max(n, 1);
  }
  // carburant : l'hydrogène liquide (chl) se recharge chaque jour sur le site d'origine ;
  // ici il remonte à 3 dès qu'il est épuisé, pour qu'on puisse jouer sans attendre.
  function burnFuel() {
    if (P.chl > 0) P.chl--; else if (P.chs > 0) P.chs--;
    if (P.chl <= 0 && P.chs <= 0) P.chl = 3;
  }

  // ---------------------------------------------------------------- données envoyées au client
  function playerData() {
    const fog = [];
    for (let i = 0; i < 400; i++) {
      const x = P.x - 10 + Math.floor(i / 20), y = P.y - 10 + (i % 20);
      fog.push(P.visited[`${x},${y}`] ? 1 : null);
    }
    return {
      _flAdmin: false, _flEditor: false, _pid: P.pid,
      _ox: P.ox, _oy: P.oy, _x: P.x, _y: P.y, _chl: P.chl, _chs: P.chs, _minerai: P.minerai,
      _missions: P.missions, _missile: P.missile, _missileMax: P.missileMax,
      _engine: P.engine, _radar: P.radar, _life: P.life, _drone: P.drone,
      _items: P.items, _shopItems: P.shopItems, _fog: fog, _comp: P.comp, _square: null,
      _travel: P.travel, _pendingLevels: -1,
    };
  }
  const setInfos = () => R('_SetInfos', persist(playerData(), { crc: true }), null, null);

  // ---------------------------------------------------------------- requêtes
  let pending = null; // case visée par le dernier _Play / _PlayLander
  function handle(req) {
    const a = req.$args;
    switch (req.$tag) {
      case '_AskInfos': return setInfos();
      case '_Play': {
        const [x, y] = a; pending = { x, y };
        burnFuel(); save();
        return R('_ConfirmMove', x, y, !P.mined[`${x},${y}`], null);
      }
      case '_EndGame': {
        const [x, y, victory, min, mis, itemId, shopItems] = a;
        P.minerai += min || 0; P.missile = mis ?? P.missile; addItem(itemId);
        if (victory) {
          P.ox = P.x; P.oy = P.y; P.x = x; P.y = y;
          P.visited[`${x},${y}`] = 1;
          if (min > 0) P.mined[`${x},${y}`] = 1;
        }
        for (const id of shopItems || []) P.shopItems[id] = 0;
        checkMission(); save(); onEvent('end', { victory, min });
        return setInfos();
      }
      case '_BuyItem': buyShopItem(a[0]); checkMission(); save(); return R('_Confirm');
      case '_PlayLander': {
        const [x, y] = a; pending = { x, y };
        const capsType = P.chl > 0 ? 0 : 1; burnFuel(); save();
        return R('_ConfirmLander', !P.mined[`L${x},${y}`], capsType, P.houses.some(h => h[0] === x && h[1] === y));
      }
      case '_EndLander': {
        const [victory, min, mis, caps, itemId, travel, markHouse] = a;
        P.minerai += min || 0; P.missile = mis ?? P.missile; addItem(itemId);
        if (travel) P.travel.push(travel);
        if (pending) {
          const { x, y } = pending, k = `${x},${y}`;
          if (min > 0) P.mined[`L${k}`] = 1;
          if (markHouse) P.houses.push([x, y]);
          const pl = planetAt(x, y);
          if (victory && pl != null && !P.landed[k]) {
            P.landed[k] = 1;
            const done = Object.keys(P.landed).filter(s => planetAt(...s.split(',').map(Number)) === pl).length;
            P.comp[pl] = Math.min(100, Math.round(done * 100 / planetSquares(pl)));
          }
        }
        checkMission(); save(); onEvent('end', { victory, min });
        return setInfos();
      }
      case '_Wrap': {
        for (const pair of D.holes) pair.forEach((p, i) => {
          if (p[0] === P.x && p[1] === P.y) { const q = pair[(i + 1) % 2]; P.x = q[0]; P.y = q[1]; P.visited[`${P.x},${P.y}`] = 1; }
        });
        checkMission(); save(); return setInfos();
      }
      case '_EndStory': {
        const [choice, itemId] = a;
        addItem(itemId);
        if (itemId === M.EARTH_PASS) { P.engine++; P.radar++; }
        if (choice === 0) { const keep = P.items[M.EARTH_PASS]; P = fresh(); P.items[M.MODE_DIF] = M.COLLECTED_INV; if (keep) P.items[M.EARTH_PASS] = keep; }
        else { P.x = 0; P.y = 0; }
        checkMission(); save(); return setInfos();
      }
      case '_SubmitLevel': case '_SelectPendingLevel': case '_DeletePendingLevels': case '_ResetLevel':
        return R('_Confirm');
      case '_AskPendingLevels': return R('_PendingLevels', []);
    }
    return R('_Error', 'Requête inconnue : ' + req.$tag);
  }

  P = store.get(KEY, null);
  if (!P) { P = fresh(); checkMission(); save(); }

  const realFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const url = typeof input === 'string' ? input : input.url;
    if (window.KT_DEBUG) console.log('[fetch]', url);
    if (!/\/play\/intercom/.test(url)) return realFetch(input, init);
    let params = new URL(url, location.href).searchParams;
    const body = init?.body ?? (typeof input !== 'string' ? await input.clone().text().catch(() => '') : '');
    if (!params.get('cmd') && body) params = new URLSearchParams(typeof body === 'string' ? body : new TextDecoder().decode(body));
    let resp;
    if (window.KT_DEBUG) console.log('[alphabounce] requête', params.get('cmd'));
    try { resp = handle(unserialize(params.get('cmd'))); }
    catch (e) { console.error('[alphabounce]', e); resp = R('_Error', String(e.message || e)); }
    const xml = `<r>${serialize(resp).replace(/&/g, '&amp;').replace(/</g, '&lt;')}</r>`;
    return new Response(xml, { status: 200, headers: { 'Content-Type': 'text/xml' } });
  };

  return {
    get player() { return P; },
    reset() { P = fresh(); checkMission(); save(); },
    planetName: id => D.planets[id]?.name,
    missionsDone: () => P.missions.filter(x => x === 1).length,
    // Marchand ambulant (ajout KotionTwin) : une vie contre un minerai.
    lifePrice: () => 1,
    buyLife() {
      const cost = 1;
      if (P.minerai < cost) return false;
      P.minerai -= cost; P.life++; P.boughtLives = (P.boughtLives || 0) + 1;
      save(); return true;
    },
  };
}
