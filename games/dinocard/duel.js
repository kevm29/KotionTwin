// Moteur de duel simplifié : remplace le serveur de Dinocard, qui calculait tout le combat et
// l'envoyait au lecteur Flash sous forme d'une liste d'actions (DataFight). Les règles d'origine
// ne sont pas dans l'archive ; celles-ci reprennent ce que le lecteur sait afficher :
// pioche, réserve d'énergie, œufs qui éclosent, attaques des dinoz, cimetière, points de vie.
const T = { DAMAGES: 0, DINOZSTATE: 1, LIFE: 2, POOL: 3, GRAVEYARD: 4, RAIL: 5, PICK: 8 };
export const ELEMENTS = ['Feu', 'Bois', 'Eau', 'Foudre', 'Ciel'];

function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}

// Deck : 20 cartes, ~70 % de l'élément choisi, le reste piochant dans les autres.
export function buildDeck(cards, element, rand, size = 20) {
  const mine = cards.filter(c => c.element === element), other = cards.filter(c => c.element !== element);
  const pick = (a) => a[Math.floor(rand() * a.length)];
  const deck = [];
  while (deck.length < size) deck.push(deck.length < size * 0.7 ? pick(mine) : pick(other));
  return deck;
}

export function makeFight({ cards, names = ['Vous', 'Adversaire'], elements = [0, 1], seed = Date.now(), life = 12, avatars = [null, null] }) {
  const rand = rng(seed);
  const byId = new Map(cards.map(c => [c.id, c]));
  let nextInst = 1;
  const instances = [], used = new Set();
  const P = [0, 1].map(i => {
    const deck = buildDeck(cards, elements[i], rand).map(c => {
      const inst = nextInst++; instances.push({ $id: inst, $cid: c.id }); used.add(c.id);
      return { inst, card: c };
    });
    for (let k = deck.length - 1; k > 0; k--) { const j = Math.floor(rand() * (k + 1)); [deck[k], deck[j]] = [deck[j], deck[k]]; }
    return { id: i + 1, name: names[i], life, deck, order: deck.map(d => d.inst), rail: [], energies: [] };
  });
  const opp = p => P[1 - P.indexOf(p)];
  const state = d => ({ $type: T.DINOZSTATE, $inst: d.inst, $strength: d.card.strength, $endurance: d.card.endurance,
    $capacities: [], $injuries: d.injuries, $eclosion: d.hatched ? null : d.ecl });

  function upkeep(p) {
    const out = [];
    for (const d of p.rail) if (!d.hatched) {
      d.ecl++;
      if (d.ecl >= d.card.eclosion) d.hatched = true;
      out.push(state(d));
    }
    return out;
  }
  function draw(p) {
    const out = [];
    const d = p.deck.shift();
    if (!d) return out;
    const hasEnergy = p.energies.some(e => e.card.element === d.card.element);
    if (!hasEnergy) {
      p.energies.push(d);
      out.push({ $type: T.PICK, $pid: p.id, $result: 5, $graveyard: null });
      out.push({ $type: T.POOL, $pid: p.id, $from: d.inst, $list: p.energies.map(e => e.inst), $element: d.card.element, $effect: false });
    } else if (p.rail.length >= 3) {
      out.push({ $type: T.PICK, $pid: p.id, $result: 1, $graveyard: null });
      out.push({ $type: T.GRAVEYARD, $pid: p.id, $inst: d.inst, $token: 0 });
    } else {
      d.ecl = 0; d.injuries = 0; d.hatched = false;
      out.push({ $type: T.PICK, $pid: p.id, $result: 0, $graveyard: null });
      out.push({ $type: T.RAIL, $action: 1, $pid: p.id, $from: d.inst, $value: String(d.inst), $place: p.rail.length, $isEgg: true });
      p.rail.push(d);
      out.push(state(d));
    }
    return out;
  }
  function combat() {
    const out = [];
    for (const p of P) {
      for (const a of p.rail.slice()) {
        if (!a.hatched || !p.rail.includes(a)) continue;
        const o = opp(p);
        const targets = o.rail.filter(d => d.hatched);
        const acts = [];
        let def = null;
        if (targets.length) {
          // vise le dinoz qu'il peut abattre, sinon le plus faible
          def = targets.find(d => d.card.endurance - d.injuries <= a.card.strength)
            || targets.reduce((m, d) => (d.card.endurance - d.injuries < m.card.endurance - m.injuries ? d : m));
          def.injuries += a.card.strength;
          acts.push({ $type: T.DAMAGES, $from: a.inst, $target: def.inst, $typeTarget: 1, $value: a.card.strength });
          if (def.injuries >= def.card.endurance) {
            o.rail.splice(o.rail.indexOf(def), 1);
            acts.push({ $type: T.GRAVEYARD, $pid: o.id, $inst: def.inst, $token: 0 });
          } else acts.push(state(def));
          // riposte
          if (o.rail.includes(def)) {
            a.injuries += def.card.strength;
            acts.push({ $type: T.DAMAGES, $from: def.inst, $target: a.inst, $typeTarget: 1, $value: def.card.strength });
            if (a.injuries >= a.card.endurance) {
              p.rail.splice(p.rail.indexOf(a), 1);
              acts.push({ $type: T.GRAVEYARD, $pid: p.id, $inst: a.inst, $token: 0 });
            } else acts.push(state(a));
          }
        } else {
          o.life = Math.max(0, o.life - a.card.strength);
          acts.push({ $type: T.DAMAGES, $from: a.inst, $target: o.id, $typeTarget: 0, $value: a.card.strength });
          acts.push({ $type: T.LIFE, $pid: o.id, $life: o.life });
        }
        out.push({ $type: 10, $aggro: a.inst, $def: def ? def.inst : null, $actions: acts });
        if (o.life <= 0) return out;
      }
    }
    return out;
  }

  const phases = [];
  for (let n = 0; n < 40; n++) {
    const turns = P.map(p => ({ $upkeep: upkeep(p), $actions: draw(p), $end: [] }));
    const fightActs = combat();
    phases.push({ $turn1: turns[0], $turn2: turns[1], $combat: fightActs });
    if (P.some(p => p.life <= 0)) break;
    const idle = P.every(p => !p.deck.length) && P.every(p => !p.rail.some(d => d.hatched) || !p.rail.length);
    if (idle || (P.every(p => !p.deck.length) && n > 30)) break;
  }
  const winner = P[0].life === P[1].life ? 0 : (P[0].life > P[1].life ? 1 : 2);

  const cardData = [...used].map(id => byId.get(id)).map(c => ({
    $id: c.id, $type: 0, $element: c.element, $name: c.name, $energy: c.energy,
    $strength: c.strength, $endurance: c.endurance, $eclosion: c.eclosion, $capacities: [], $desc: '', $flavor: '',
  }));
  return {
    $player1: { $id: 1, $name: names[0], $life: life, $avatar: avatars[0], $cardMax: P[0].order.length, $packName: ELEMENTS[elements[0]] },
    $player2: { $id: 2, $name: names[1], $life: life, $avatar: avatars[1], $cardMax: P[1].order.length, $packName: ELEMENTS[elements[1]] },
    $rounds: [{ $pack1: P[0].order, $pack2: P[1].order, $phases: phases }],
    $winner: winner,
    $newCard: null,
    $elements: { $cards: cardData, $instances: instances, $capacities: [] },
    _result: { winner, life: [P[0].life, P[1].life] },
  };
}
