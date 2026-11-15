// Sons ajoutés par KotionTwin à des jeux Flash d'origine muets (Opalus 2, Alchimie…).
// Le SWF (via le loader KadoKado) appelle window.ktSnd(type, valeur) ; la page joue le son.
// Bruitages : Web Audio (sons courts décodés une fois, rejoués sans délai).
// Musique : un élément <audio> qui enchaîne les morceaux au hasard, en boucle.
//
// Configuration dans data/games.json (g.entry.sounds) :
//   { "base": "games/<id>/sons/",
//     "sfx": { "<type>": ["a.mp3", "b.mp3", …] },  // valeur n → n-ième fichier (1 = premier)
//     "volume": { "<type>": 0.6 },                  // volume relatif de chaque type (défaut 0.7)
//     "music": ["ambiance-1.mp3", …], "musicVolume": 0.4 }
// Les silences de tête ont été coupés dans les fichiers : le son part dès l'appel.

const MAX_VOICES = 10;
const MIN_GAP = 0.03;   // écart mini entre deux sons identiques (secondes)

export function createGameAudio(id, cfg) {
  const PREF = 'kt.audio.' + id;
  const prefs = { sfx: 1, music: 1 };
  try { Object.assign(prefs, JSON.parse(localStorage.getItem(PREF) || '{}')); } catch {}
  const save = () => { try { localStorage.setItem(PREF, JSON.stringify(prefs)); } catch {} };
  let muted = false;

  const AC = window.AudioContext || window.webkitAudioContext;
  const ctx = AC ? new AC() : null;   // créé au clic « Lancer la partie » : le son est autorisé
  const master = ctx?.createGain();
  master?.connect(ctx.destination);
  const applySfx = () => { if (master) master.gain.value = muted ? 0 : prefs.sfx; };
  applySfx();

  const buffers = {};
  if (ctx) for (const f of Object.values(cfg.sfx || {}).flat()) {
    buffers[f] = fetch(cfg.base + f).then(r => r.arrayBuffer()).then(b => ctx.decodeAudioData(b)).catch(() => null);
  }
  const last = {};
  let voices = 0;

  async function play(kind, n) {
    const list = cfg.sfx?.[kind];
    if (!list || !ctx || muted || prefs.sfx <= 0) return;
    if (ctx.state === 'suspended') ctx.resume();
    const i = Math.max(0, Math.min(list.length - 1, (Number(n) || 1) - 1));
    const key = kind + i, now = ctx.currentTime;
    if (now - (last[key] ?? -1) < MIN_GAP || voices >= MAX_VOICES) return;
    last[key] = now;
    const buf = await buffers[list[i]];
    if (!buf) return;
    const src = ctx.createBufferSource(), g = ctx.createGain();
    src.buffer = buf; g.gain.value = cfg.volume?.[kind] ?? 0.7;
    src.connect(g).connect(master);
    voices++;
    src.onended = () => voices--;
    src.start();
  }

  // Musique : un morceau tiré au hasard au départ, puis un autre (jamais le même deux fois de suite).
  const tracks = cfg.music || [];
  const music = new Audio();
  music.preload = 'none';
  let track = -1, started = false;
  const applyMusic = () => { music.volume = Math.min(1, (cfg.musicVolume ?? 0.4) * prefs.music); };
  const pick = () => {
    if (tracks.length < 2) return 0;
    let j = Math.floor(Math.random() * (tracks.length - 1));
    return j >= track ? j + 1 : j;
  };
  const next = () => { track = pick(); music.src = cfg.base + tracks[track]; music.play().catch(() => {}); };
  const musicOn = () => !muted && prefs.music > 0 && tracks.length > 0;
  const syncMusic = () => {
    applyMusic();
    if (!musicOn() || document.hidden) { music.pause(); return; }
    if (!started) { started = true; next(); } else if (music.paused) music.play().catch(() => {});
  };
  music.addEventListener('ended', next);
  const onVis = () => syncMusic();
  document.addEventListener('visibilitychange', onVis);
  syncMusic();

  return {
    play,
    hasMusic: tracks.length > 0,
    get: key => prefs[key],
    set(key, v) {
      prefs[key] = Math.max(0, Math.min(1, Number(v)));
      save();
      if (key === 'sfx') applySfx(); else syncMusic();
    },
    mute(on) { muted = on; applySfx(); syncMusic(); },
    stop() {
      music.pause(); music.removeAttribute('src');
      document.removeEventListener('visibilitychange', onVis);
      ctx?.close().catch(() => {});
    },
  };
}
