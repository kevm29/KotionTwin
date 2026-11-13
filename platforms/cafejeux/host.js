/*
 * KotionTwin — « serveur » CaféJeux local.
 *
 * Les jeux CaféJeux étaient des duels en ligne : chaque joueur faisait tourner sa copie du jeu
 * et le serveur relayait les messages. Ici, deux lecteurs Ruffle (un par joueur) chargent le même
 * game.swf recompilé avec l'API recréée (platforms/cafejeux/api/MMApi.hx), et cette page joue le
 * rôle du serveur : elle relaie messages, fins de tour et victoire.
 *
 * Modes :
 *  - tour : un seul écran, on passe la souris à chaque tour (le plateau de l'autre est caché) ;
 *  - cote : les deux plateaux côte à côte ;
 *  - ia   : le joueur 2 est joué par l'ordinateur (ai.js), quand une IA existe pour ce jeu.
 *
 * URL : host.html?g=<id du jeu>[&mode=tour|cote|ia]
 */
(function () {
  'use strict';

  const RUFFLE_LOCAL = '../../vendor/ruffle/ruffle.js';
  const RUFFLE_CDN = 'https://cdn.jsdelivr.net/npm/@ruffle-rs/ruffle@0.7.1/ruffle.js';

  const params = new URLSearchParams(location.search);
  const gameId = params.get('g') || 'cj-power4';
  const swfUrl = params.get('swf') || `../../games/${gameId}/game.swf`;
  const ai = window.CJ_AI && window.CJ_AI[gameId];

  const $ = (id) => document.getElementById(id);
  const names = ['Joueur 1', 'Joueur 2'];
  const DEFAULT_COLORS = ['#00e89c', '#d6370a'];

  let mode = params.get('mode') || 'tour';
  if (mode === 'ia' && !ai) mode = 'tour';

  // ------------------------------------------------------------------ état de la partie
  let S;
  function freshState() {
    return {
      players: [null, null],
      ready: [false, false],
      turn: null,        // joueur qui a la main (null avant le premier tour)
      shown: 0,          // joueur dont le plateau est affiché (mode tour)
      buffer: [[], []],  // événements retenus pour le plateau caché (mode tour)
      result: null,      // { winner: 0|1|null }
      ended: false,
      logs: [[], []],
      infos: ['', ''],
      initializer: 1,
      aiModel: null,
      timers: [],
    };
  }
  let round = 0;

  function later(fn, ms) { const t = setTimeout(fn, ms); S.timers.push(t); return t; }

  // ------------------------------------------------------------------ Ruffle
  function loadScript(src) {
    return new Promise((ok, ko) => {
      const s = document.createElement('script');
      s.src = src; s.onload = ok; s.onerror = () => ko(new Error('échec ' + src));
      document.head.append(s);
    });
  }
  async function ensureRuffle() {
    if (window.RufflePlayer && window.RufflePlayer.newest) return;
    try { await loadScript(RUFFLE_LOCAL); } catch (e) { await loadScript(RUFFLE_CDN); }
  }

  async function createPlayer(pid) {
    const ruffle = window.RufflePlayer.newest();
    const player = ruffle.createPlayer();
    const seat = $('seat' + pid);
    seat.replaceChildren(player);
    await player.ruffle().load({
      url: swfUrl,
      parameters: { pid: String(pid) },
      allowScriptAccess: true,
      autoplay: 'on',
      unmuteOverlay: 'hidden',
      splashScreen: false,
      letterbox: 'on',
      contextMenu: 'off',
      warnOnUnsupportedContent: false,
      showSwfDownload: false,
      ...(window.CJ_RUFFLE_CONFIG || {}),
    });
    return player;
  }

  // ------------------------------------------------------------------ envoi vers un plateau
  function push(pid, kind, mine, data) {
    const p = S.players[pid];
    if (!p) return;
    if (DEBUG) console.log('[cj] -> j' + (pid + 1) + ' ' + kind + ' ' + mine + ' ' + String(data).slice(0, 200));
    if (typeof p.cjPush === 'function') p.cjPush(kind, !!mine, String(data));
    else console.warn('[cafejeux] plateau', pid, 'pas encore prêt pour', kind);
    if (S.aiModel && pid === 1) aiObserve(kind, mine, data);
  }
  function deliver(pid, kind, mine, data) {
    if (mode === 'tour' && S.turn !== null && !S.ended && pid !== S.shown) {
      S.buffer[pid].push([kind, mine, data]);
      return;
    }
    push(pid, kind, mine, data);
  }
  function flush(pid) {
    const b = S.buffer[pid];
    S.buffer[pid] = [];
    for (const [k, m, d] of b) push(pid, k, m, d);
  }

  // ------------------------------------------------------------------ réception depuis un plateau
  const DEBUG = params.has('debug');
  window.cjSend = function (pid, kind, data) {
    pid = Number(pid);
    if (DEBUG) console.log('[cj] j' + (pid + 1) + ' -> ' + kind + ' ' + String(data).slice(0, 200));
    if (!S || !S.players[pid] && kind !== 'ready') return;
    switch (kind) {
      case 'ready':
        S.ready[pid] = true;
        if (S.ready[0] && S.ready[1]) later(start, 50);
        break;
      case 'msg':
        later(() => { deliver(pid, 'msg', true, data); deliver(1 - pid, 'msg', false, data); }, 0);
        break;
      case 'endTurn':
        later(() => {
          S.turn = 1 - pid;
          deliver(pid, 'turn', false, '0');
          deliver(1 - pid, 'turn', false, '1');
          updateHud();
          if (mode === 'ia' && S.turn === 1) aiPlaySoon();
        }, 0);
        break;
      case 'turnSeen':
        if (mode === 'tour' && pid === S.shown && data === '0' && S.turn === 1 - pid && !S.ended) {
          later(showRelay, 600);
        }
        break;
      case 'victory':
        if (S.result) break;
        S.result = { winner: data === 'n' ? null : (data === '1' ? pid : 1 - pid) };
        later(() => {
          S.ended = true;
          for (const p of [0, 1]) {
            flush(p);
            const w = S.result.winner;
            push(p, 'victory', false, w === null ? 'n' : (w === p ? '1' : '0'));
          }
          updateHud();
          later(showEnd, 9000); // au cas où le jeu n'appelle jamais gameOver
        }, 0);
        break;
      case 'gameOver':
        if (S.ended) later(showEnd, 900);
        break;
      case 'colors': {
        const [me] = String(data).split(',').map((x) => '#' + (Number(x) >>> 0).toString(16).padStart(6, '0'));
        document.documentElement.style.setProperty('--c' + pid, me);
        break;
      }
      case 'infos':
        S.infos[pid] = names_in(pid, String(data));
        renderInfos();
        break;
      case 'log':
        S.logs[pid].push(names_in(pid, String(data)));
        renderLog();
        break;
      case 'print':
        console.log(`[cafejeux j${pid + 1}]`, data);
        break;
      case 'error':
        console.error(`[cafejeux j${pid + 1}] erreur du jeu :`, data);
        break;
    }
  };

  // Le serveur d'origine remplaçait $me et $other par les pseudos des joueurs.
  function names_in(pid, txt) {
    return txt.replace(/\$me\b/g, names[pid]).replace(/\$other\b/g, names[1 - pid]);
  }

  // ------------------------------------------------------------------ déroulement
  function start() {
    // Le joueur qui initialise envoie le message d'init puis passe la main : l'autre commence.
    push(S.initializer, 'init', true, '');
  }

  function showRelay() {
    if (S.ended || mode !== 'tour' || S.turn === S.shown) return;
    $('relayName').textContent = names[S.turn];
    $('relay').hidden = false;
    $('relayGo').focus();
  }
  function takeSeat() {
    $('relay').hidden = true;
    S.shown = S.turn;
    layout();
    flush(S.shown);
    focusPlayer(S.shown);
  }

  function showEnd() {
    if (!$('end').hidden || !S.result) return;
    $('relay').hidden = true;
    const w = S.result.winner;
    $('endText').textContent = w === null ? 'Match nul !' : `${names[w]} gagne !`;
    $('end').hidden = false;
    $('again').focus();
  }

  // ------------------------------------------------------------------ IA
  function aiObserve(kind, mine, data) {
    try {
      if (kind === 'msg') ai.onMessage(S.aiModel, !!mine, HaxeSer.unserialize(String(data)));
    } catch (e) { console.error('[cafejeux ia]', e); }
  }
  function aiPlaySoon() {
    later(() => {
      if (S.ended || S.turn !== 1) return;
      let move;
      try { move = ai.play(S.aiModel); } catch (e) { console.error('[cafejeux ia]', e); }
      if (!move) return;
      const msgs = Array.isArray(move) ? move : [move];
      for (const m of msgs) window.cjSend(1, 'msg', HaxeSer.serialize(m));
      window.cjSend(1, 'endTurn', '');
    }, ai.delay || 900);
  }

  // ------------------------------------------------------------------ affichage
  function layout() {
    document.body.className = 'mode-' + mode;
    for (const p of [0, 1]) {
      const seat = $('seat' + p);
      const visible = mode === 'cote' || (mode === 'ia' ? p === 0 : p === S.shown);
      seat.classList.toggle('shown', visible);
      seat.classList.toggle('hidden', !visible);
      seat.setAttribute('aria-hidden', String(!visible));
      seat.classList.toggle('mine', mode === 'cote' && S.turn === p);
    }
    for (const b of document.querySelectorAll('.modes button')) {
      b.setAttribute('aria-pressed', String(b.dataset.mode === mode));
    }
    names[1] = mode === 'ia' ? 'Ordinateur' : 'Joueur 2';
    $('p1').querySelector('.name').textContent = names[1];
    renderInfos(); renderLog(); updateHud();
  }
  function viewer() { return mode === 'cote' ? (S.turn ?? 0) : (mode === 'ia' ? 0 : S.shown); }
  function updateHud() {
    for (const p of [0, 1]) $('p' + p).classList.toggle('active', S.turn === p && !S.ended);
    if (mode === 'cote') for (const p of [0, 1]) $('seat' + p).classList.toggle('mine', S.turn === p);
  }
  // setInfos reçoit du HTML écrit par les jeux : on ne garde que quelques balises de mise en forme.
  function safeHtml(html) {
    const doc = new DOMParser().parseFromString('<div>' + html + '</div>', 'text/html');
    const ok = new Set(['B', 'STRONG', 'I', 'EM', 'P', 'BR', 'SPAN', 'FONT', 'U', 'DIV', 'A']);
    const clean = (node) => {
      for (const ch of [...node.childNodes]) {
        if (ch.nodeType === 1) {
          if (!ok.has(ch.tagName)) { ch.replaceWith(...ch.childNodes); continue; }
          const color = ch.tagName === 'FONT' ? ch.getAttribute('color') : null;
          const cls = /^(score0|score1|help)$/.test(ch.getAttribute('class') || '') ? ch.getAttribute('class') : null;
          for (const a of [...ch.attributes]) ch.removeAttribute(a.name);
          if (cls) ch.className = cls;
          if (color && /^#?[0-9a-f]{3,6}$/i.test(color)) ch.style.color = color.startsWith('#') ? color : '#' + color;
          clean(ch);
        } else if (ch.nodeType !== 3) ch.remove();
      }
    };
    const root = doc.body.firstChild;
    clean(root);
    return root.innerHTML;
  }
  function renderInfos() { $('infos').innerHTML = safeHtml(S.infos[viewer()] || ''); }
  function renderLog() {
    const items = S.logs[viewer()].slice(-60).map((t) => { const li = document.createElement('li'); li.textContent = t; return li; });
    $('log').replaceChildren(...items);
    $('log').scrollTop = 1e6;
  }
  function focusPlayer(pid) {
    const p = S.players[pid];
    if (p && p.focus) setTimeout(() => p.focus(), 30);
  }

  // ------------------------------------------------------------------ lancement
  async function newGame() {
    if (S) for (const t of S.timers) clearTimeout(t);
    S = freshState();
    // On alterne qui commence d'une partie à l'autre.
    S.initializer = round % 2 === 0 ? 1 : 0;
    S.shown = 1 - S.initializer;
    round++;
    if (mode === 'ia') { S.aiModel = ai.create(); S.initializer = ai.humanInitializes ? 0 : 1; S.shown = 0; }
    document.documentElement.style.setProperty('--c0', DEFAULT_COLORS[0]);
    document.documentElement.style.setProperty('--c1', DEFAULT_COLORS[1]);
    $('end').hidden = true; $('relay').hidden = true; $('err').hidden = true;
    layout();
    try {
      await ensureRuffle();
      const [a, b] = await Promise.all([createPlayer(0), createPlayer(1)]);
      S.players = [a, b];
      layout();
      focusPlayer(S.shown);
    } catch (e) {
      $('errText').textContent = String(e && e.message || e);
      $('err').hidden = false;
    }
  }

  $('relayGo').addEventListener('click', takeSeat);
  $('again').addEventListener('click', newGame);
  $('restart').addEventListener('click', newGame);
  for (const b of document.querySelectorAll('.modes button')) {
    if (b.dataset.mode === 'ia') b.hidden = !ai;
    b.addEventListener('click', () => {
      if (b.dataset.mode === mode) return;
      mode = b.dataset.mode;
      const u = new URL(location.href); u.searchParams.set('mode', mode); history.replaceState(null, '', u);
      newGame();
    });
  }
  newGame();
})();
