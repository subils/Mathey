// Mode demo: un backend simulat dins del navegador, amb el mateix contracte que
// /api (docs/ARQUITECTURA.md §5). Entra sol quan no hi ha cap placa connectada,
// perquè es pugui navegar i dissenyar tota la web sense l'Arduino.
//
// Els problemes d'aquí són INVENTATS per nosaltres (no són de M3Kang): per això
// la resposta pot viure al navegador sense trencar cap regla.

import type {
  AnswerResult,
  ChatEvent,
  ChatTurn,
  ExplainResult,
  Health,
  HintResult,
  Letter,
  Matrix,
  NextResult,
  OwnMatch,
  OwnOcr,
  Problem,
  Profile,
  Session,
  Stats,
} from "./api";

/* ------------------------------------------------------------------ */
/* Banc de demo                                                        */
/* ------------------------------------------------------------------ */

type DemoProblem = {
  id: string;
  topic: string;
  elo: number;
  level: number;
  text: string;
  options: Record<Letter, string>;
  answer: Letter;
  key_idea: string;
  hints: [string, string, string];
  solution: string[];
  traps: Partial<Record<Letter, string>>;
};

const BANK: DemoProblem[] = [
  {
    id: "demo-1",
    topic: "aritmètica",
    elo: 850,
    level: 0,
    text: "La Marta té 3 bosses amb 6 caramels cadascuna. En regala 5 a la seva germana. Quants caramels li queden?",
    options: { A: "9", B: "12", C: "13", D: "18", E: "23" },
    answer: "C",
    key_idea: "Primer compta quants n'hi ha en total (és una multiplicació) i després treu els que regala.",
    hints: [
      "Fes-ho en dos passos: primer quants caramels té, després quants en treu.",
      "Hi ha 3 bosses i cada una en té 6: això és 3 vegades 6.",
      "Primer pas: 3 × 6 = 18 caramels en total.",
    ],
    solution: ["En té 3 × 6 = 18.", "En regala 5: 18 − 5 = 13.", "Li queden 13 caramels."],
    traps: {
      A: "Has sumat 3 + 6 en lloc de fer 3 vegades 6?",
      B: "Has tret 6 caramels en lloc de 5?",
      D: "Has comptat el total però t'has oblidat de treure els que regala?",
      E: "Has sumat els 5 caramels regalats en lloc de restar-los?",
    },
  },
  {
    id: "demo-2",
    topic: "geometria",
    elo: 1000,
    level: 0,
    text: "Un rectangle fa 10 cm de llarg i 4 cm d'ample. Quant fa el seu perímetre?",
    options: { A: "14 cm", B: "24 cm", C: "28 cm", D: "40 cm", E: "20 cm" },
    answer: "C",
    key_idea: "El perímetre és la volta sencera: un rectangle té dos costats llargs i dos de curts.",
    hints: [
      "Dibuixa el rectangle i escriu la mida de cada un dels quatre costats.",
      "Un rectangle té 4 costats: dos fan 10 cm i dos fan 4 cm.",
      "Primer pas: 10 + 4 = 14 és només mitja volta.",
    ],
    solution: ["Els quatre costats fan 10, 4, 10 i 4 cm.", "10 + 4 + 10 + 4 = 28.", "El perímetre és 28 cm."],
    traps: {
      A: "Has sumat un costat llarg i un de curt, però això és només mitja volta?",
      B: "Has sumat dos costats llargs i només un de curt?",
      D: "Has multiplicat 10 × 4? Això és l'àrea, no el perímetre.",
      E: "Has sumat els dos costats llargs però cap dels curts?",
    },
  },
  {
    id: "demo-3",
    topic: "lògica",
    elo: 1150,
    level: 1,
    text: "En una fila de 7 nens, l'Anna és la segona començant per l'esquerra. Quina posició ocupa començant per la dreta?",
    options: { A: "2a", B: "4a", C: "5a", D: "6a", E: "7a" },
    answer: "D",
    key_idea: "Fes un dibuix de la fila: les posicions des de l'esquerra i des de la dreta sumen un més que el total.",
    hints: [
      "Dibuixa 7 rodones en fila i marca l'Anna.",
      "Quants nens hi ha a la dreta de l'Anna?",
      "Primer pas: a la dreta de l'Anna hi ha 5 nens.",
    ],
    solution: ["A la dreta de l'Anna hi ha 7 − 2 = 5 nens.", "Comptant des de la dreta, l'Anna va just després d'aquests 5.", "És la 6a."],
    traps: {
      A: "Has pensat que és la mateixa posició des de les dues bandes?",
      C: "Has comptat els nens de la dreta però no l'Anna?",
      E: "Has comptat tota la fila?",
    },
  },
  {
    id: "demo-4",
    topic: "combinatòria i probabilitat",
    elo: 1250,
    level: 1,
    text: "Tinc 3 samarretes i 2 pantalons diferents. De quantes maneres em puc vestir amb una samarreta i un pantaló?",
    options: { A: "5", B: "6", C: "8", D: "9", E: "3" },
    answer: "B",
    key_idea: "Cada samarreta es pot combinar amb cada pantaló: es multiplica.",
    hints: [
      "Fes una llista ordenada o un arbre amb totes les combinacions.",
      "Per a cada samarreta, quants pantalons hi pots posar?",
      "Primer pas: amb la primera samarreta tens 2 opcions.",
    ],
    solution: ["Cada samarreta va amb 2 pantalons.", "3 samarretes × 2 pantalons = 6.", "Hi ha 6 maneres."],
    traps: {
      A: "Has sumat 3 + 2? Cada samarreta es combina amb cada pantaló.",
      C: "Has fet 2 × 2 × 2?",
      D: "Has fet 3 × 3?",
      E: "Has comptat només les samarretes?",
    },
  },
  {
    id: "demo-5",
    topic: "àlgebra",
    elo: 1350,
    level: 2,
    text: "Penso un nombre. El multiplico per 3 i hi sumo 4. Obtinc 25. Quin nombre he pensat?",
    options: { A: "5", B: "6", C: "7", D: "8", E: "9" },
    answer: "C",
    key_idea: "Desfés els passos al revés: primer treu el 4 i després divideix entre 3.",
    hints: [
      "Comença pel final i ves enrere.",
      "Abans de sumar 4, quant tenies?",
      "Primer pas: 25 − 4 = 21.",
    ],
    solution: ["Abans de sumar 4 tenia 25 − 4 = 21.", "Abans de multiplicar per 3 tenia 21 ÷ 3 = 7.", "He pensat el 7."],
    traps: {
      D: "Has sumat el 4 en lloc de restar-lo en desfer els passos?",
      A: "Has dividit 25 entre 3 i després has restat?",
    },
  },
  {
    id: "demo-6",
    topic: "combinatòria i probabilitat",
    elo: 1500,
    level: 2,
    text: "Quants nombres de dues xifres tenen les dues xifres parelles?",
    options: { A: "16", B: "20", C: "25", D: "40", E: "45" },
    answer: "B",
    key_idea: "Compta les opcions de cada xifra per separat i multiplica. Compte: la primera xifra no pot ser 0.",
    hints: [
      "Pensa en les desenes i en les unitats per separat.",
      "Quines xifres parelles hi ha? I quines poden anar a davant?",
      "Primer pas: a les desenes hi pot anar 2, 4, 6 o 8.",
    ],
    solution: ["Desenes: 2, 4, 6 o 8 (4 opcions; el 0 no hi pot anar).", "Unitats: 0, 2, 4, 6 o 8 (5 opcions).", "4 × 5 = 20 nombres."],
    traps: {
      A: "T'has oblidat que el 0 sí que pot anar a les unitats?",
      C: "Has deixat que el 0 vagi a davant? Llavors no seria de dues xifres.",
    },
  },
  {
    id: "demo-7",
    topic: "geometria",
    elo: 1650,
    level: 3,
    text: "Un quadrat té una àrea de 36 cm². Quant fa el seu perímetre?",
    options: { A: "6 cm", B: "9 cm", C: "18 cm", D: "24 cm", E: "36 cm" },
    answer: "D",
    key_idea: "De l'àrea en treus el costat (quin nombre per si mateix fa 36?) i després fas la volta.",
    hints: [
      "Quin nombre multiplicat per ell mateix fa 36?",
      "El costat del quadrat fa 6 cm.",
      "Primer pas: el quadrat té 4 costats de 6 cm.",
    ],
    solution: ["El costat fa 6 cm, perquè 6 × 6 = 36.", "El perímetre són 4 costats: 4 × 6 = 24.", "Fa 24 cm."],
    traps: {
      A: "Això és el costat. El perímetre és tota la volta.",
      B: "Has dividit 36 entre 4? Això no dona el costat.",
      E: "Has confós l'àrea amb el perímetre?",
    },
  },
  {
    id: "demo-8",
    topic: "lògica",
    elo: 1800,
    level: 3,
    text: "Avui és dimarts. Quin dia de la setmana serà d'aquí a 100 dies?",
    options: { A: "Dilluns", B: "Dimarts", C: "Dimecres", D: "Dijous", E: "Divendres" },
    answer: "D",
    key_idea: "Cada 7 dies tornes al mateix dia: només compta el que sobra en dividir entre 7.",
    hints: [
      "Cada quants dies es repeteix el dimarts?",
      "Quantes setmanes senceres hi ha en 100 dies, i quants dies sobren?",
      "Primer pas: 100 = 14 × 7 + 2.",
    ],
    solution: ["100 dies són 14 setmanes i 2 dies.", "Les 14 setmanes et tornen a dimarts.", "Dos dies més: dijous."],
    traps: {
      B: "Has pensat que 100 és múltiple de 7?",
      C: "T'has descomptat d'un dia en sumar els 2 que sobren?",
    },
  },
];

const GRADE_ELO: Record<string, number> = { "5è": 875, "6è": 1025, "1r ESO": 1175, "2n ESO": 1325 };
const STRATEGIES: Record<string, string> = {
  aritmètica: "Fes-ho per passos i escriu el resultat de cada pas abans de seguir.",
  geometria: "Fes un dibuix i escriu-hi totes les mides que saps.",
  lògica: "Fes un dibuix o una taula i prova els casos un per un.",
  "combinatòria i probabilitat": "Fes una llista ordenada de tots els casos, o un arbre, i compta'ls.",
  àlgebra: "Desfés les operacions al revés, començant pel final.",
};

/* ------------------------------------------------------------------ */
/* Estat de l'alumne de demo (al navegador)                            */
/* ------------------------------------------------------------------ */

type Attempt = { problem_id: string; letter: Letter; correct: boolean; first_try: boolean; hints: number; elo_before: number; elo_after: number };
type DemoState = {
  alias: string;
  grade: string;
  elo: number;
  elo_start: number;
  elo_peak: number;
  streak: number;
  attempts: Attempt[];
  hints: Record<string, number>;
  tried: Record<string, Letter[]>;
  matrix: Matrix;
  ownTexts: string[];
};

const KEY = "mathey-demo-state";
export const DEMO_STUDENT = 900001;

function load(): DemoState {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw) as DemoState;
  } catch {
    /* sense emmagatzematge */
  }
  return { alias: "Demo", grade: "6è", elo: 1025, elo_start: 1025, elo_peak: 1025, streak: 0, attempts: [], hints: {}, tried: {}, matrix: idle(), ownTexts: [] };
}
function save(state: DemoState) {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* res */
  }
}

/* ------------------------------------------------------------------ */
/* Matriu (mentor/matrix.py)                                           */
/* ------------------------------------------------------------------ */

const grid = (rows: string[]): Matrix => rows.map((r) => [...r].map((c) => (c === "#" ? 7 : 0)));
const CHECK = grid([".............", "...........#.", "..........##.", ".........##..", "..#.....##...", "..##...##....", "...##.##.....", "....###......"]);
const CROSS = grid([".............", "...#.....#...", "....#...#....", ".....#.#.....", "......#......", ".....#.#.....", "....#...#....", "...#.....#..."]);
const THINKING = grid([".............", ".............", ".............", "..#...#...#..", "..#...#...#..", ".............", ".............", "............."]);
function idle() {
  return grid([".............", "....#...#....", "....#..#.....", "....#.#......", "....##.......", "....#.#......", "....#..#.....", "....#...#...."]);
}

/* ------------------------------------------------------------------ */
/* Respostes                                                           */
/* ------------------------------------------------------------------ */

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
const cap = (t: string) => t[0].toUpperCase() + t.slice(1);

export class DemoError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

function publicOf(p: DemoProblem): Problem {
  return {
    id: p.id,
    level: p.level,
    elo: p.elo,
    year: 2026,
    topic: p.topic,
    has_figure: false,
    text: p.text,
    options: p.options,
    image_url: "", // sense imatge: la web ensenya el text
  };
}
const byId = (id: string) => BANK.find((p) => p.id === id);

function pick(state: DemoState, target: number, exclude?: string): DemoProblem {
  const seen = new Set(state.attempts.filter((a) => a.correct).map((a) => a.problem_id));
  const pool = BANK.filter((p) => p.id !== exclude && !seen.has(p.id));
  const list = pool.length ? pool : BANK.filter((p) => p.id !== exclude);
  return [...list].sort((a, b) => Math.abs(a.elo - target) - Math.abs(b.elo - target))[0];
}

function health(): Health {
  return {
    ok: true,
    mock: true,
    host: "mode demo",
    problems: BANK.length,
    bank_problems: BANK.length,
    llm: "mock",
    embeddings: "demo",
    matrix: "simulada",
    server_time: new Date().toLocaleTimeString("ca"),
  };
}

/** Tradueix una crida de l'API a la resposta simulada. */
export async function demoCall(method: string, path: string, body?: Record<string, unknown>): Promise<unknown> {
  const url = new URL(path, "http://demo");
  const q = Object.fromEntries(url.searchParams);
  const params = { ...q, ...(body ?? {}) } as Record<string, unknown>;
  const state = load();
  await wait(120 + Math.random() * 180); // que s'assembli a una crida de veritat

  switch (`${method} ${url.pathname}`) {
    case "GET /health":
      return health();

    case "POST /session": {
      const grade = String(params.grade ?? "6è");
      const elo = GRADE_ELO[grade] ?? 1025;
      const fresh: DemoState = {
        alias: String(params.alias ?? "Demo").slice(0, 30),
        grade,
        elo,
        elo_start: elo,
        elo_peak: elo,
        streak: 0,
        attempts: [],
        hints: {},
        tried: {},
        matrix: idle(),
        ownTexts: [],
      };
      save(fresh);
      return { student: DEMO_STUDENT, alias: fresh.alias, grade, elo, matrix: fresh.matrix } satisfies Session;
    }

    case "GET /next": {
      const wanted = q.id ? byId(q.id) : undefined;
      if (q.id && !wanted) throw new DemoError(404, "problema desconegut");
      const target = q.elo ? Number(q.elo) : state.elo;
      const p = wanted ?? pick(state, target);
      state.matrix = idle(); // problema nou: s'esborra el ✓/✗ anterior
      save(state);
      return {
        problem: publicOf(p),
        elo: state.elo,
        target_elo: target,
        elo_range: [BANK[0].elo, BANK[BANK.length - 1].elo],
        streak: state.streak,
        matrix: state.matrix,
      } satisfies NextResult;
    }

    case "POST /answer": {
      const p = byId(String(params.problem_id));
      if (!p) throw new DemoError(404, "problema desconegut");
      const letter = String(params.letter) as Letter;
      const tried = state.tried[p.id] ?? [];
      const firstTry = tried.length === 0;
      const correct = letter === p.answer;
      state.tried[p.id] = [...tried, letter];
      const hints = state.hints[p.id] ?? 0;
      let change = 0;
      if (firstTry) {
        const expected = 0.2 + 0.8 / (1 + 10 ** ((p.elo - state.elo) / 400));
        const result = correct ? (hints ? 0.5 : 1) : 0;
        change = Math.round(32 * (result - expected));
      }
      const before = state.elo;
      state.elo += change;
      state.elo_peak = Math.max(state.elo_peak, state.elo);
      if (firstTry) state.streak = correct && !hints ? state.streak + 1 : 0;
      state.attempts.push({ problem_id: p.id, letter, correct, first_try: firstTry, hints, elo_before: before, elo_after: state.elo });
      state.matrix = correct ? CHECK : CROSS;
      save(state);
      return {
        correct,
        first_try: firstTry,
        streak: state.streak,
        elo: state.elo,
        elo_change: change,
        problem_elo: p.elo,
        matrix: state.matrix,
        ...(correct ? { answer: p.answer, answer_text: p.options[p.answer], solution: p.solution, key_idea: p.key_idea } : {}),
      } satisfies AnswerResult;
    }

    case "POST /hint": {
      const p = byId(String(params.problem_id));
      if (!p) throw new DemoError(404, "problema desconegut");
      const rung = Number(params.rung);
      if (rung === 5 && !params.confirm) throw new DemoError(400, "cal confirmar per veure la solució");
      state.hints[p.id] = Math.max(state.hints[p.id] ?? 0, rung);
      save(state);
      if (rung === 1) return { rung, type: "estrategia", text: p.hints[0], blocked: false } satisfies HintResult;
      if (rung === 2) return { rung, type: "dada_clau", text: p.hints[1], blocked: false } satisfies HintResult;
      if (rung === 4) return { rung, type: "primer_pas", text: p.hints[2], blocked: false } satisfies HintResult;
      if (rung === 3) {
        const sibling = BANK.filter((x) => x.id !== p.id && x.topic === p.topic && x.elo <= p.elo).at(-1)
          ?? BANK.filter((x) => x.id !== p.id && x.elo < p.elo).at(-1);
        return sibling
          ? { rung, type: "germa", text: "Prova primer aquest, que fa servir una idea semblant:", problem: publicOf(sibling) }
          : { rung, type: "germa", text: `La idea clau: ${p.key_idea}`, problem: null };
      }
      return { rung: 5, type: "solucio", steps: p.solution, answer: p.answer, answer_text: p.options[p.answer] } satisfies HintResult;
    }

    case "POST /explain": {
      const p = byId(String(params.problem_id));
      const letter = String(params.letter) as Letter;
      state.matrix = THINKING;
      save(state);
      await wait(1600);
      state.matrix = CROSS;
      save(state);
      const trap = p?.traps[letter];
      return {
        reply: trap ?? "Torna a llegir l'enunciat a poc a poc: què et pregunta exactament?",
        source: "preparat",
        seconds: 1.6,
        rejected: "mode demo: sense IA de la placa",
        timings: {},
      } satisfies ExplainResult;
    }

    case "POST /warm":
      return { started: true };

    case "GET /profile": {
      const first = state.attempts.filter((a) => a.first_try);
      const topics = [...new Set(first.map((a) => byId(a.problem_id)?.topic ?? "aritmètica"))];
      return {
        alias: state.alias,
        grade: state.grade,
        elo: state.elo,
        elo_start: state.elo_start,
        elo_peak: state.elo_peak,
        streak: state.streak,
        attempts: first.length,
        correct: first.filter((a) => a.correct).length,
        accuracy: first.length ? first.filter((a) => a.correct).length / first.length : null,
        by_topic: topics.map((topic) => {
          const list = first.filter((a) => byId(a.problem_id)?.topic === topic);
          const ok = list.filter((a) => a.correct).length;
          return { topic, attempts: list.length, correct: ok, accuracy: ok / list.length, avg_hints: list.reduce((s, a) => s + a.hints, 0) / list.length };
        }),
        recent: first.slice(-10).reverse().map((a) => ({
          problem_id: a.problem_id,
          letter: a.letter,
          correct: a.correct ? 1 : 0,
          hints_used: a.hints,
          topic: byId(a.problem_id)?.topic ?? "aritmètica",
          problem_elo: byId(a.problem_id)?.elo ?? null,
          elo_before: a.elo_before,
          elo_after: a.elo_after,
          ts: new Date().toISOString(),
        })),
      } satisfies Profile;
    }

    case "GET /matrix":
      return { matrix: state.matrix };

    case "GET /stats":
      return {
        host: "mode demo",
        llm: "down",
        memory: null,
        bank: { verified: BANK.length, prepared: BANK.length, built_at: null },
        students: 1,
        attempts: state.attempts.length,
        hints: Object.values(state.hints).reduce((s, n) => s + n, 0),
        questions: { total: 0, from_board: 0, fallback: 0, median_seconds: null, worst_seconds: null },
        internet: "no cal (mode demo: cap placa connectada)",
      } satisfies Stats;

    case "POST /own/ocr":
      await wait(1100);
      return {
        text: "Tinc 3 caixes amb 12 pomes cada una i en regalo 7. Quantes pomes em queden?",
        engine: "demo",
        seconds: 1.1,
        empty: false,
      } satisfies OwnOcr;

    case "POST /own/match": {
      const text = String(params.text ?? "");
      if (text.trim().split(/\s+/).length < 4) throw new DemoError(400, "escriu l'enunciat del problema (com a mínim una frase)");
      state.ownTexts.push(text);
      save(state);
      const topic = guessTopic(text);
      const sibling = BANK.find((p) => p.topic === topic) ?? BANK[0];
      return {
        own_id: state.ownTexts.length,
        topic,
        topic_confidence: 0.8,
        found: true,
        same_idea: true,
        siblings: [{ ...publicOf(sibling), score: 0.6 }],
        strategy: STRATEGIES[topic],
        message: null,
      } satisfies OwnMatch;
    }

    default:
      throw new DemoError(404, `ruta desconeguda al mode demo: ${method} ${url.pathname}`);
  }
}

function guessTopic(text: string) {
  const t = text.toLowerCase();
  if (/rectangle|quadrat|triangle|perímetre|àrea|angle|cercle/.test(t)) return "geometria";
  if (/maneres|combinacions|quants nombres|probabilitat|xifres/.test(t)) return "combinatòria i probabilitat";
  if (/penso un nombre|equació|\bx\b/.test(t)) return "àlgebra";
  if (/dia|fila|posició|mentida|veritat/.test(t)) return "lògica";
  return "aritmètica";
}

/** Resolució simulada del xat, a trossos com la de la placa. */
export async function demoChat(
  own_id: number,
  { message, signal, onEvent }: { message?: string; history?: ChatTurn[]; signal?: AbortSignal; onEvent: (e: ChatEvent) => void },
) {
  const state = load();
  const text = (state.ownTexts[own_id - 1] ?? "").toLowerCase();
  const topic = guessTopic(text);
  onEvent({ type: "meta", own_id, sibling: publicOf(BANK.find((p) => p.topic === topic) ?? BANK[0]), strategy: STRATEGIES[topic] });

  let reply: string;
  if (message) {
    reply = `Bona pregunta. En el mode demo no hi ha IA de la placa, però amb la placa connectada et respondria aquí en dues o tres frases sobre el teu problema. Mentrestant: ${STRATEGIES[topic].toLowerCase()}`;
  } else if (text.includes("pomes")) {
    reply = "1. Tens 3 caixes de 12 pomes: $3 \\cdot 12 = 36$ pomes.\n2. En regales 7: $36 - 7 = 29$.\nResultat: 29 pomes.";
  } else if (text.includes("rectangle") && text.includes("perímetre")) {
    reply = "1. El perímetre és la volta: $2 \\cdot (\\text{llarg} + \\text{ample}) = 24$.\n2. Llavors $\\text{llarg} + \\text{ample} = 12$, i com que el llarg fa 8, l'ample fa $12 - 8 = 4$ cm.\n3. L'àrea és $8 \\cdot 4 = 32$.\nResultat: 32 cm².";
  } else if (text.includes("xifres")) {
    reply = "1. A les desenes hi pot anar 2, 4, 6 o 8: 4 opcions (el 0 no).\n2. A les unitats hi pot anar 0, 2, 4, 6 o 8: 5 opcions.\n3. Es multiplica: $4 \\cdot 5 = 20$.\nResultat: 20 nombres.";
  } else {
    reply = `**Mode demo.** Amb la placa connectada, la IA resoldria aquí el teu problema pas a pas. Així és com es veuria:\n\n1. Llegim l'enunciat i apuntem les dades.\n2. ${cap(STRATEGIES[topic])}\n3. Comprovem que el resultat té sentit.\nResultat: el número que surti, amb les unitats.`;
  }

  await wait(900);
  const pieces = reply.match(/\S+\s*/g) ?? [reply];
  for (const piece of pieces) {
    if (signal?.aborted) throw new DOMException("Aturat", "AbortError");
    onEvent({ type: "delta", text: piece });
    await wait(45 + Math.random() * 40);
  }
  onEvent({ type: "done", reply, source: "preparat", seconds: 0.9 + pieces.length * 0.065, rejected: "mode demo", timings: {} });
}

/** Esborra l'alumne de demo (en sortir del mode demo o en fer «Surt»). */
export function resetDemo() {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* res */
  }
}
