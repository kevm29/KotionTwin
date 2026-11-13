// Sérialisation Haxe 2 (haxe.Serializer / haxe.Unserializer), sous-ensemble utile aux
// protocoles client/serveur des jeux Motion Twin. Les énumérations sont représentées par
// { $enum: 'Nom', $tag: 'Constructeur', $args: [...] }.
export const E = (e, tag, ...args) => ({ $enum: e, $tag: tag, $args: args });

export function serialize(v) {
  const strs = new Map(); let out = '';
  const str = s => {
    if (strs.has(s)) { out += 'R' + strs.get(s); return; }
    strs.set(s, strs.size);
    const e = encodeURIComponent(s);
    out += 'y' + e.length + ':' + e;
  };
  const any = v => {
    if (v == null) out += 'n';
    else if (v === true) out += 't';
    else if (v === false) out += 'f';
    else if (typeof v === 'number') {
      if (Number.isInteger(v)) out += v === 0 ? 'z' : 'i' + v;
      else if (Number.isNaN(v)) out += 'k';
      else if (!Number.isFinite(v)) out += v < 0 ? 'm' : 'p';
      else out += 'd' + v;
    } else if (typeof v === 'string') str(v);
    else if (Array.isArray(v)) {
      out += 'a'; let nulls = 0;
      for (const x of v) {
        if (x == null) { nulls++; continue; }
        if (nulls) { out += nulls === 1 ? 'n' : 'u' + nulls; nulls = 0; }
        any(x);
      }
      if (nulls) out += nulls === 1 ? 'n' : 'u' + nulls;
      out += 'h';
    } else if (v.$enum) {
      out += 'w'; str(v.$enum); str(v.$tag); out += ':' + v.$args.length;
      for (const a of v.$args) any(a);
    } else {
      out += 'o';
      for (const [k, x] of Object.entries(v)) { str(k); any(x); }
      out += 'g';
    }
  };
  any(v);
  return out;
}

export function unserialize(s) {
  let p = 0; const strs = [];
  const int = () => { const m = /^-?\d+/.exec(s.slice(p)); p += m[0].length; return +m[0]; };
  const any = () => {
    const c = s[p++];
    switch (c) {
      case 'n': return null;
      case 't': return true;
      case 'f': return false;
      case 'z': return 0;
      case 'i': return int();
      case 'd': { const m = /^[-+0-9.eE]+/.exec(s.slice(p)); p += m[0].length; return parseFloat(m[0]); }
      case 'k': return NaN;
      case 'm': return -Infinity;
      case 'p': return Infinity;
      case 'y': { const n = int(); p++; const v = decodeURIComponent(s.substr(p, n)); p += n; strs.push(v); return v; }
      case 'R': return strs[int()];
      case 'a': {
        const a = [];
        for (;;) {
          if (s[p] === 'h') { p++; return a; }
          if (s[p] === 'u') { p++; const n = int(); for (let i = 0; i < n; i++) a.push(null); continue; }
          a.push(any());
        }
      }
      case 'o': {
        const o = {};
        while (s[p] !== 'g') { const k = any(); o[k] = any(); }
        p++; return o;
      }
      case 'w': {
        const e = any(), tag = any(); p++; const n = int(); const args = [];
        for (let i = 0; i < n; i++) args.push(any());
        return { $enum: e, $tag: tag, $args: args };
      }
      default: throw new Error(`Unserializer : code « ${c} » inattendu en ${p - 1}`);
    }
  };
  return any();
}
