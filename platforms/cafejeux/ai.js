/*
 * IA simples pour les jeux CaféJeux (mode « Contre l'ordinateur »).
 * Chaque IA tient son propre modèle du plateau à partir des messages du jeu
 * (décodés par haxe-serializer.js) et renvoie le message à jouer quand c'est son tour.
 *
 * Interface : window.CJ_AI[id] = {
 *   create() -> modèle, onMessage(modèle, mine, msg), play(modèle) -> msg | [msgs], delay?
 * }
 */
window.CJ_AI = window.CJ_AI || {};

/* ------------------------------------------------------------------------------------------
 * Puissance 4 (CaféJeux) : plateau ouvert, un pion neutre au centre. On lance son pion depuis
 * un bord (haut, bas, gauche, droite) : il glisse jusqu'à toucher un autre pion. Il faut aligner
 * 4 pions horizontalement ou verticalement. Message : Set(x, y, dx, dy).
 * ------------------------------------------------------------------------------------------ */
(function () {
  const D = 50, D2 = D * 2;
  const key = (x, y) => x * 1000 + y;

  function create() {
    const cells = new Map();
    cells.set(key(D, D), 'N');
    return { cells, minX: D, maxX: D, minY: D, maxY: D };
  }
  const at = (m, x, y) => m.cells.get(key(x, y));
  function put(m, x, y, who) {
    m.cells.set(key(x, y), who);
    m.minX = Math.min(m.minX, x); m.maxX = Math.max(m.maxX, x);
    m.minY = Math.min(m.minY, y); m.maxY = Math.max(m.maxY, y);
  }
  // Même règle que Level.lookupX/lookupY : la case derrière est occupée et tout est vide jusqu'au bord.
  function free(m, x, y, dx, dy) {
    if (at(m, x - dx, y - dy) === undefined) return false;
    let cx = x, cy = y;
    while (at(m, cx, cy) === undefined) {
      cx += dx; cy += dy;
      if (cx < m.minX - 1 || cx > m.maxX + 1 || cy < m.minY - 1 || cy > m.maxY + 1) return true;
    }
    return false;
  }
  function moves(m) {
    const out = [];
    for (let x = m.minX - 1; x <= m.maxX + 1; x++) {
      for (let y = m.minY - 1; y <= m.maxY + 1; y++) {
        if (at(m, x, y) !== undefined) continue;
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          if (free(m, x, y, dx, dy)) { out.push({ x, y, dx, dy }); break; }
        }
      }
    }
    return out;
  }
  // Longueur de la ligne et ouvertures autour de (x, y) pour le joueur who.
  function line(m, x, y, who, dx, dy) {
    let n = 1, open = 0;
    for (const s of [1, -1]) {
      let cx = x + dx * s, cy = y + dy * s;
      while (at(m, cx, cy) === who) { n++; cx += dx * s; cy += dy * s; }
      if (at(m, cx, cy) === undefined) open++;
    }
    return { n, open };
  }
  function score(m, mv, who) {
    let s = 0;
    for (const [dx, dy] of [[1, 0], [0, 1]]) {
      const l = line(m, mv.x, mv.y, who, dx, dy);
      if (l.n >= 4) return 1e6;
      s += [0, 1, 12, 120][l.n] * (l.open + 1);
    }
    return s;
  }
  function play(m) {
    const list = moves(m);
    if (!list.length) return null;
    let best = null, bestScore = -Infinity;
    for (const mv of list) {
      const attack = score(m, mv, 'A');
      const defend = score(m, mv, 'H');
      let s = attack >= 1e6 ? 2e6 : (defend >= 1e6 ? 1e6 : attack + defend * 0.9);
      // Ne pas offrir une case gagnante à l'adversaire juste après notre coup.
      if (s < 1e6) {
        put(m, mv.x, mv.y, 'A');
        for (const r of moves(m)) if (score(m, r, 'H') >= 1e6) { s -= 5e5; break; }
        m.cells.delete(key(mv.x, mv.y));
      }
      s += Math.random() * 3;
      if (s > bestScore) { bestScore = s; best = mv; }
    }
    return window.HaxeSer.en('Msg', 'Set', best.x, best.y, best.dx, best.dy);
  }
  function onMessage(m, mine, msg) {
    if (msg.c === 'Set') put(m, msg.a[0], msg.a[1], mine ? 'A' : 'H');
  }
  window.CJ_AI['cj-power4'] = { create, play, onMessage, delay: 700 };
})();
