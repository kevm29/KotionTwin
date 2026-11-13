// mt.PersistCodec (Motion Twin), réécrit d'après le bytecode de Pioupiouz/game/swf/code.swf.
// Format binaire empaqueté en base64 « a-zA-Z0-9-_ », bits de poids fort d'abord.
const ALPHA = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_';

class BitWriter {
  constructor() { this.data = ''; this.nbits = 0; this.bits = 0; this.crc = 0; }
  write(n, v) {
    this.nbits += n; this.bits = (this.bits * (1 << n)) + v; // évite le dépassement 32 bits
    while (this.nbits >= 6) {
      this.nbits -= 6;
      const c = Math.floor(this.bits / 2 ** this.nbits) & 63;
      this.bits = this.bits % (2 ** this.nbits);
      this.crc = (((this.crc ^ c) & 0xFFFFFF) * c);
      this.data += ALPHA[c];
    }
  }
  toString() { if (this.nbits > 0) this.write(6 - this.nbits, 0); return this.data; }
  crcStr() { const c = this.crc; return [0, 6, 12, 18].map(s => ALPHA[(c >> s) & 63]).join(''); }
}
class BitReader {
  constructor(d) { this.data = d; this.pos = 0; this.nbits = 0; this.bits = 0; this.crc = 0; this.error = false; }
  read(n) {
    while (this.nbits < n) {
      const c = ALPHA.indexOf(this.data.charAt(this.pos++));
      if (c < 0) { this.error = true; return -1; }
      this.crc = (((this.crc ^ c) & 0xFFFFFF) * c);
      this.nbits += 6; this.bits = (this.bits * 64 + c) % (2 ** 40);
    }
    this.nbits -= n;
    return Math.floor(this.bits / 2 ** this.nbits) & ((1 << n) - 1);
  }
  crcStr() { const c = this.crc; return [0, 6, 12, 18].map(s => ALPHA[(c >> s) & 63]).join(''); }
}

export function encode(o, { crc = false, obfu = false, refs = true } = {}) {
  const bc = new BitWriter(); const fields = new Map(); let nfields = 0, nbits = 0, next = 1;
  const int = n => {
    if (n < 0) { bc.write(3, 7); int(-n); }
    else if (n < 4) { bc.write(2, 0); bc.write(2, n); }
    else if (n < 16) { bc.write(2, 1); bc.write(4, n); }
    else if (n < 64) { bc.write(2, 2); bc.write(6, n); }
    else if (n < 65536) { bc.write(4, 12); bc.write(16, n); }
    else { bc.write(4, 13); bc.write(16, n & 65535); bc.write(16, (n >> 16) & 65535); }
  };
  const str = s => {
    int(s.length);
    if ([...s].every(c => ALPHA.includes(c))) { bc.write(1, 0); for (const c of s) bc.write(6, ALPHA.indexOf(c)); }
    else {
      const ascii = [...s].every(c => c.charCodeAt(0) <= 127);
      bc.write(2, ascii ? 2 : 3);
      for (const c of s) bc.write(ascii ? 7 : 8, c.charCodeAt(0) & 255);
    }
  };
  const flt = x => {
    const s = String(x); bc.write(5, s.length);
    for (const ch of s) {
      const c = ch.charCodeAt(0);
      bc.write(4, c >= 48 && c <= 58 ? c - 48 : ch === '.' ? 10 : ch === '+' ? 11 : ch === '-' ? 12 : 13);
    }
  };
  const any = v => {
    if (v == null) bc.write(4, 15);
    else if (Array.isArray(v)) {
      bc.write(3, 4); let nulls = 0;
      for (const x of v) {
        if (x == null) { nulls++; continue; }
        if (nulls > 0) { bc.write(2, 2); int(nulls); nulls = 0; }
        bc.write(1, 0); any(x);
      }
      bc.write(2, 3);
    } else if (typeof v === 'string') { bc.write(4, 14); str(v); }
    else if (typeof v === 'number') {
      if (Number.isNaN(v)) bc.write(4, 6);
      else if (v === Infinity) bc.write(5, 14);
      else if (v === -Infinity) bc.write(5, 15);
      else if (Number.isInteger(v)) { bc.write(2, 0); int(v); }
      else { bc.write(3, 2); flt(v); }
    } else if (typeof v === 'boolean') bc.write(4, v ? 13 : 12);
    else if (typeof v === 'object') {
      bc.write(3, 5);
      for (let [k, x] of Object.entries(v)) {
        if (typeof x === 'function' || x == null) continue;
        if (obfu && k[0] === '$') k = k.slice(1);
        if (refs && fields.has(k)) { bc.write(1, 0); bc.write(nbits, fields.get(k)); }
        else {
          nfields++; fields.set(k, nfields);
          if (!(nfields < next)) { nbits++; next *= 2; }
          bc.write(2, 2); str(k);
        }
        any(x);
      }
      bc.write(2, 3);
    }
  };
  any(o);
  let out = bc.toString();
  if (crc) out += bc.crcStr();
  return out;
}

export function decode(s, { crc = false, obfu = false } = {}) {
  const bc = new BitReader(s); const tbl = []; let nfields = 0, nbits = 0, next = 1;
  const int = () => {
    const t = bc.read(2);
    if (t === 3) {
      if (bc.read(1) === 1) return -int();
      if (bc.read(1) === 1) { const lo = bc.read(16), hi = bc.read(16); return lo | (hi << 16); }
      return bc.read(16);
    }
    return bc.read((t + 1) * 2);
  };
  const str = () => {
    const n = int(); let s = '';
    if (bc.read(1) === 0) { for (let i = 0; i < n; i++) s += ALPHA[bc.read(6)]; return s; }
    const w = bc.read(1) === 0 ? 7 : 8;
    for (let i = 0; i < n; i++) s += String.fromCharCode(bc.read(w));
    return s;
  };
  const flt = () => {
    const n = bc.read(5); let s = '';
    for (let i = 0; i < n; i++) { const c = bc.read(4); s += c < 10 ? String(c) : '.+-e'[c - 10]; }
    return parseFloat(s);
  };
  const any = () => {
    if (bc.error) throw new Error('PersistCodec : données tronquées');
    if (bc.read(1) === 0) {
      if (bc.read(1) === 0) return int();
      if (bc.read(1) === 0) return flt();
      if (bc.read(1) === 0) return NaN;
      return bc.read(1) === 1 ? -Infinity : Infinity;
    }
    if (bc.read(1) === 0) {
      if (bc.read(1) === 1) {
        const o = {};
        for (;;) {
          let k;
          if (bc.read(1) === 0) k = tbl[bc.read(nbits)];
          else if (bc.read(1) === 1) break;
          else {
            k = str(); if (obfu && k[0] !== '$') k = '$' + k;
            nfields++; tbl[nfields] = k;
            if (!(nfields < next)) { nbits++; next *= 2; }
          }
          o[k] = any();
          if (bc.error) throw new Error('PersistCodec : données tronquées');
        }
        return o;
      }
      const a = []; let pos = 0;
      for (;;) {
        if (bc.read(1) === 0) { a[pos++] = any(); }
        else if (bc.read(1) === 1) break;
        else pos += int();
        if (bc.error) throw new Error('PersistCodec : données tronquées');
      }
      return a;
    }
    const t = bc.read(2);
    return t === 2 ? str() : [false, true, null, null][t];
  };
  const v = any();
  return v;
}
