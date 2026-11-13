// Prépare games/alphabounce/ depuis l'archive :
//   node src/alphabounce/build.mjs <chemin>/WebGamesArchives/Alphabounce
// - copie game.swf et planet.swf (client d'origine, compilé en mode « prod ») ;
// - extrait de com/*.hx les données dont le serveur simulé a besoin (missions, boutique,
//   trous noirs, vraie liste des planètes) vers data.json.
import fs from 'fs';
import path from 'path';
const SRC = process.argv[2] || '../WebGamesArchives/Alphabounce';
const OUT = path.join(path.dirname(new URL(import.meta.url).pathname), '../../games/alphabounce');
fs.mkdirSync(OUT, { recursive: true });
import zlib from 'zlib';
fs.copyFileSync(path.join(SRC, 'web/swf/planet.swf'), path.join(OUT, 'planet.swf'));
// game.swf déclare la scène de gfx.swf (742×422) alors que le jeu dessine en 400×360
// (Cs.mcw / Cs.mch) : on corrige l'en-tête pour que Ruffle cadre et agrandisse correctement.
function setStage(buf, w, h) {
  const body = buf.subarray(0, 3).toString() === 'CWS' ? zlib.inflateSync(buf.subarray(8)) : buf.subarray(8);
  const nbits = body[0] >> 3, rl = Math.ceil((5 + 4 * nbits) / 8);
  const vals = [0, w * 20, 0, h * 20], nb = Math.max(...vals.map(v => v.toString(2).length)) + 1;
  let bits = nb.toString(2).padStart(5, '0') + vals.map(v => v.toString(2).padStart(nb, '0')).join('');
  bits = bits.padEnd(Math.ceil(bits.length / 8) * 8, '0');
  const rect = Buffer.from(bits.match(/.{8}/g).map(b => parseInt(b, 2)));
  const nbody = Buffer.concat([rect, body.subarray(rl)]);
  const head = Buffer.from([0x43, 0x57, 0x53, buf[3], 0, 0, 0, 0]); head.writeUInt32LE(nbody.length + 8, 4);
  return Buffer.concat([head, zlib.deflateSync(nbody, { level: 9 })]);
}
fs.writeFileSync(path.join(OUT, 'game.swf'), setStage(fs.readFileSync(path.join(SRC, 'web/swf/game.swf')), 400, 360));

const read = f => fs.readFileSync(path.join(SRC, 'com', f), 'utf8').replace(/^﻿/, '');
const consts = src => {
  const o = {};
  for (const m of src.matchAll(/public static var (\w+)\s*=\s*(-?\d+)\s*;/g)) o[m[1]] = +m[2];
  return o;
};
const mi = read('MissionInfo.hx'), si = read('ShopInfo.hx'), zi = read('ZoneInfo.hx');
const MissionInfo = consts(mi), ShopInfo = consts(si), ZoneInfo = consts(zi);

// Extrait un littéral Haxe (tableau) qui commence après `marker` et l'évalue en JS.
function literal(src, marker) {
  let i = src.indexOf(marker); if (i < 0) throw new Error(marker);
  i = src.indexOf('[', i);
  let depth = 0, j = i;
  for (; j < src.length; j++) {
    const c = src[j];
    if (c === '/' && src[j + 1] === '/') { j = src.indexOf('\n', j); continue; }
    if (c === '/' && src[j + 1] === '*') { j = src.indexOf('*/', j) + 1; continue; }
    if (c === '"') { j = src.indexOf('"', j + 1); continue; }
    if (c === '[') depth++;
    if (c === ']' && --depth === 0) break;
  }
  const text = src.slice(i, j + 1);
  const names = Object.keys(MissionInfo);
  const fn = new Function('MissionInfo', 'ShopInfo', 'ZoneInfo', ...names, `return ${text};`);
  return fn(MissionInfo, ShopInfo, ZoneInfo, ...names.map(n => MissionInfo[n]));
}
const missions = literal(mi, 'public static var LIST').map(m => ({
  conditions: m.conditions, startConditions: m.startConditions, startItem: m.startItem, endItem: m.endItem,
}));
const shop = literal(si, 'public static var ITEMS').map(x => x.price);
const holes = literal(zi, 'public static var holes');
const planets = literal(zi.slice(zi.indexOf('#if web')), 'var a =').map(p => ({ name: p.name, pos: p.pos }));
const data = { MissionInfo, ShopInfo, missions, shop, holes, planets };
fs.writeFileSync(path.join(OUT, 'data.json'), JSON.stringify(data));
console.log(missions.length, 'missions,', shop.length, 'objets de boutique,', planets.length, 'planètes');
