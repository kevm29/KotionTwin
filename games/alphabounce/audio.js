// Bruitages et musique ajoutés par KotionTwin à Alphabounce (le jeu d'origine était muet).
// Bruitages : Web Audio (sons courts décodés une fois, rejoués sans délai).
// Musique : un élément <audio> qui enchaîne les morceaux en boucle.
// Les navigateurs n'autorisent le son qu'après un geste du joueur : tout démarre au premier clic ou à la première touche.
const SFX = {
  // [fichier, début en secondes (silence de tête coupé)]
  ball: [['ball-a.mp3', 0.027], ['ball-b.mp3', 0], ['ball-c.mp3', 0.035], ['ball-d.mp3', 0.046]],
  brick: [['break-brick.mp3', 0]],
  bonus: [['bonus-a.mp3', 0], ['bonus-b.mp3', 0]],
};
const ALIAS = { 'bank.wav': 'ball' };
const MUSIC = ['ambiance-a.mp3', 'ambiance-b.mp3'];
const VOL = { ball: 0.55, brick: 0.45, bonus: 0.7, music: 0.35 };
const MIN_GAP = { ball: 0.04, brick: 0.05, bonus: 0.1 };   // écart mini entre deux sons du même type
const MAX_VOICES = 8;
const PREF = 'kt.alphabounce.audio';

export function createAudio(base) {
  let prefs = { sfx: true, music: true };
  try { Object.assign(prefs, JSON.parse(localStorage.getItem(PREF) || '{}')); } catch {}
  const save = () => { try { localStorage.setItem(PREF, JSON.stringify(prefs)); } catch {} };

  let ctx = null, gain = null;
  const buffers = {}, last = {}, turn = {};
  let voices = 0;
  const loadAll = () => Object.values(SFX).flat().forEach(([f]) => {
    buffers[f] = fetch(base + f).then(r => r.arrayBuffer()).then(b => ctx.decodeAudioData(b)).catch(() => null);
  });

  const music = new Audio();
  music.preload = 'none';
  music.volume = VOL.music;
  let track = Math.floor(Math.random() * MUSIC.length), musicStarted = false;
  const playTrack = () => { music.src = base + MUSIC[track]; music.play().catch(() => {}); };
  music.addEventListener('ended', () => { track = (track + 1) % MUSIC.length; playTrack(); });

  let unlocked = false;
  const unlock = () => {
    if (!unlocked) {
      unlocked = true;
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) { ctx = new AC(); gain = ctx.createGain(); gain.connect(ctx.destination); loadAll(); }
    }
    if (ctx && ctx.state === 'suspended') ctx.resume();
    if (prefs.music && !musicStarted) { musicStarted = true; playTrack(); }
    else if (prefs.music && music.paused) music.play().catch(() => {});
  };
  ['pointerdown', 'keydown', 'touchstart'].forEach(e => addEventListener(e, unlock, { capture: true }));
  // onglet caché : on coupe la musique, elle reprend au retour
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) music.pause();
    else if (prefs.music && musicStarted) music.play().catch(() => {});
  });

  async function play(kind) {
    kind = ALIAS[kind] || kind;
    const list = SFX[kind];
    if (!list || !prefs.sfx || !ctx || ctx.state !== 'running') return;
    const now = ctx.currentTime;
    if (now - (last[kind] ?? -1) < MIN_GAP[kind] || voices >= MAX_VOICES) return;
    last[kind] = now;
    // rebond : variante au hasard (jamais deux fois la même) ; bonus : en alternance
    let i = turn[kind] ?? 0;
    if (kind === 'ball' && list.length > 1) { const j = Math.floor(Math.random() * (list.length - 1)); i = j >= i ? j + 1 : j; }
    else i = (i + 1) % list.length;
    turn[kind] = i;
    const [file, offset] = list[i];
    const buf = await buffers[file];
    if (!buf) return;
    const src = ctx.createBufferSource(), g = ctx.createGain();
    src.buffer = buf; g.gain.value = VOL[kind];
    src.connect(g).connect(gain);
    voices++;
    src.onended = () => voices--;
    src.start(0, offset);
  }

  return {
    play,
    get: key => prefs[key],
    set(key, on) {
      prefs[key] = on; save();
      if (key === 'music') {
        if (!on) music.pause();
        else if (unlocked) { if (!musicStarted) { musicStarted = true; playTrack(); } else music.play().catch(() => {}); }
      }
    },
  };
}
