/*
 * Lecture/écriture du format haxe.Serializer (Haxe 2) côté page, pour que l'IA puisse
 * comprendre et produire les messages des jeux CaféJeux.
 * Une valeur d'enum Haxe est représentée par { e: 'Msg', c: 'Set', a: [args] }.
 */
(function (root) {
  'use strict';

  function unserialize(str) {
    let pos = 0;
    const scache = [];
    const cache = [];
    const readInt = () => {
      let s = pos;
      if (str[pos] === '-') pos++;
      while (pos < str.length && str[pos] >= '0' && str[pos] <= '9') pos++;
      return parseInt(str.slice(s, pos), 10);
    };
    const readFloat = () => {
      let s = pos;
      while (pos < str.length && /[0-9eE+\-.]/.test(str[pos])) pos++;
      return parseFloat(str.slice(s, pos));
    };
    const read = () => {
      const c = str[pos++];
      switch (c) {
        case 'n': return null;
        case 'z': return 0;
        case 't': return true;
        case 'f': return false;
        case 'k': return NaN;
        case 'm': return -Infinity;
        case 'p': return Infinity;
        case 'i': return readInt();
        case 'd': return readFloat();
        case 'y': {
          const len = readInt(); pos++; // ':'
          const s = decodeURIComponent(str.substr(pos, len)); // escape()/unescape() en Flash 8
          pos += len; scache.push(s); return s;
        }
        case 'R': return scache[readInt()];
        case 'r': return cache[readInt()];
        case 'a': {
          const a = []; cache.push(a);
          for (;;) {
            const ch = str[pos];
            if (ch === 'h') { pos++; break; }
            if (ch === 'u') { pos++; const n = readInt(); for (let i = 0; i < n; i++) a.push(null); continue; }
            a.push(read());
          }
          return a;
        }
        case 'l': {
          const a = []; cache.push(a);
          while (str[pos] !== 'h') a.push(read());
          pos++; return a;
        }
        case 'o': {
          const o = {}; cache.push(o);
          while (str[pos] !== 'g') { const k = read(); o[k] = read(); }
          pos++; return o;
        }
        case 'w': {
          const e = read(); const ctor = read(); pos++; // ':'
          const n = readInt(); const a = [];
          for (let i = 0; i < n; i++) a.push(read());
          const v = { e, c: ctor, a }; cache.push(v); return v;
        }
        case 'j': {
          const e = read(); pos++; const idx = readInt(); pos++;
          const n = readInt(); const a = [];
          for (let i = 0; i < n; i++) a.push(read());
          const v = { e, c: idx, a }; cache.push(v); return v;
        }
        default:
          throw new Error('format haxe inconnu « ' + c + ' » en ' + (pos - 1));
      }
    };
    return read();
  }

  function serialize(v) {
    const out = [];
    const shash = new Map();
    const str = (s) => {
      if (shash.has(s)) { out.push('R' + shash.get(s)); return; }
      shash.set(s, shash.size);
      // StringTools.urlEncode = escape() en Flash 8 : tout ce qui n'est pas alphanumérique est encodé
      const e = encodeURIComponent(s).replace(/[!'()*\-._~]/g, (ch) => '%' + ch.charCodeAt(0).toString(16).toUpperCase());
      out.push('y' + e.length + ':' + e);
    };
    const w = (x) => {
      if (x === null || x === undefined) out.push('n');
      else if (typeof x === 'boolean') out.push(x ? 't' : 'f');
      else if (typeof x === 'number') {
        if (Number.isInteger(x) && Math.abs(x) < 0x40000000) out.push(x === 0 ? 'z' : 'i' + x);
        else if (Number.isNaN(x)) out.push('k');
        else if (!Number.isFinite(x)) out.push(x < 0 ? 'm' : 'p');
        else out.push('d' + x);
      } else if (typeof x === 'string') str(x);
      else if (Array.isArray(x)) {
        out.push('a');
        let nulls = 0;
        for (const it of x) {
          if (it === null || it === undefined) { nulls++; continue; }
          if (nulls) { out.push(nulls === 1 ? 'n' : 'u' + nulls); nulls = 0; }
          w(it);
        }
        if (nulls) out.push(nulls === 1 ? 'n' : 'u' + nulls);
        out.push('h');
      } else if (x.e && x.c !== undefined) {
        out.push('w'); str(x.e); str(String(x.c)); out.push(':' + (x.a ? x.a.length : 0));
        for (const it of x.a || []) w(it);
      } else {
        out.push('o');
        for (const k of Object.keys(x)) { str(k); w(x[k]); }
        out.push('g');
      }
    };
    w(v);
    return out.join('');
  }

  root.HaxeSer = { serialize, unserialize, en: (e, c, ...a) => ({ e, c, a }) };
})(window);
