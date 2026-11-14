// Client de l'API del mentor. Contracte: docs/ARQUITECTURA.md, secció 5.
//
// A la placa, la web i l'API comparteixen origen (port 7000), així que la base
// és buida. Amb `pnpm dev`, la web corre al 3000 i l'API al 7000.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ??
  (process.env.NODE_ENV === "development" ? "http://127.0.0.1:7000" : "");

export type Matrix = number[][];
export type Letter = "A" | "B" | "C" | "D" | "E";
export const LETTERS: Letter[] = ["A", "B", "C", "D", "E"];

export type Health = {
  ok: boolean;
  mock: boolean;
  host: string;
  problems: number;
  bank_problems?: number;
  llm: "up" | "down" | "mock";
  embeddings: string;
  matrix: string;
  server_time: string;
};

export type Problem = {
  id: string;
  level: number;
  year: number;
  topic: string;
  has_figure: boolean;
  text: string;
  easy_text: string;
  options: Partial<Record<Letter, string>>;
  image_url: string;
};

export type Session = {
  student: number;
  alias: string;
  grade: string;
  level: number;
  easy_mode: boolean;
  matrix?: Matrix;
};

export type NextResult = { problem: Problem | null; level?: number; message?: string; matrix?: Matrix };

export type AnswerResult = {
  correct: boolean;
  first_try: boolean;
  level: number;
  level_change: number;
  streak: number;
  matrix: Matrix;
  answer?: Letter;
  answer_text?: string;
  solution?: string[];
  key_idea?: string;
};

export type HintResult = {
  rung: number;
  type: "estrategia" | "dada_clau" | "germa" | "primer_pas" | "solucio";
  text?: string | null;
  blocked?: boolean;
  problem?: Problem | null;
  steps?: string[];
  answer?: Letter;
  answer_text?: string;
};

export type ExplainResult = {
  reply: string;
  source: "placa" | "preparat";
  seconds: number;
  rejected: string | null;
  timings: Record<string, number>;
};

export type Profile = {
  alias: string;
  grade: string;
  level: number;
  streak: number;
  attempts: number;
  correct: number;
  accuracy: number | null;
  by_topic: { topic: string; attempts: number; correct: number; accuracy: number; avg_hints: number }[];
  recent: { problem_id: string; letter: string; correct: number; hints_used: number; topic: string; level: number; ts: string }[];
};

export type Teacher = {
  students: number;
  attempts: number;
  cells: { topic: string; level: number; attempts: number; correct: number; accuracy: number; avg_hints: number }[];
  traps: { problem_id: string; letter: string; count: number; share: number | null; trap: string; topic: string; level: number; image_url: string }[];
  topics: string[];
  levels: number[];
};

export type Stats = {
  host: string;
  llm: "up" | "down";
  memory: { total_mb: number; available_mb: number } | null;
  bank: { verified: number; prepared: number; built_at: string | null };
  students: number;
  attempts: number;
  hints: number;
  questions: { total: number; from_board: number; fallback: number; median_seconds: number | null; worst_seconds: number | null };
  internet: string;
};

export type OwnOcr = { text: string; engine: string | null; seconds: number | null; empty: boolean };
export type OwnMatch = {
  own_id: number;
  topic: string;
  topic_confidence: number;
  found: boolean;
  siblings: (Problem & { score: number })[];
  strategy: string;
  message: string | null;
};
export type OwnHelp = {
  reply: string;
  source: "placa" | "preparat";
  seconds: number;
  rejected: string | null;
  strategy: string;
  sibling: Problem | null;
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function call<T>(method: "GET" | "POST", path: string, body?: object): Promise<T> {
  const response = await fetch(`${API_BASE}/api${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(response.status, (data as { error?: string }).error ?? response.statusText);
  }
  return data as T;
}

/** Primera lletra en majúscula (el CSS `capitalize` faria «Combinatòria I Probabilitat»). */
export const cap = (text: string) => (text ? text[0].toUpperCase() + text.slice(1) : text);

export const imageUrl = (problem: Pick<Problem, "image_url">) => `${API_BASE}${problem.image_url}`;

export const api = {
  health: () => call<Health>("GET", "/health"),
  session: (alias: string, grade: string, easy_mode: boolean) =>
    call<Session>("POST", "/session", { alias, grade, easy_mode }),
  next: (student: number, id?: string) =>
    call<NextResult>("GET", `/next?student=${student}${id ? `&id=${encodeURIComponent(id)}` : ""}`),
  answer: (student: number, problem_id: string, letter: Letter, seconds: number) =>
    call<AnswerResult>("POST", "/answer", { student, problem_id, letter, seconds }),
  hint: (student: number, problem_id: string, rung: number, confirm = false) =>
    call<HintResult>("POST", "/hint", { student, problem_id, rung, confirm }),
  explain: (student: number, problem_id: string, letter: Letter, text: string) =>
    call<ExplainResult>("POST", "/explain", { student, problem_id, letter, text }),
  warm: (problem_id: string) => call<{ started: boolean }>("POST", "/warm", { problem_id }),
  profile: (student: number) => call<Profile>("GET", `/profile?student=${student}`),
  teacher: () => call<Teacher>("GET", "/teacher"),
  matrix: () => call<{ matrix: Matrix }>("GET", "/matrix"),
  stats: () => call<Stats>("GET", "/stats"),
  ownOcr: (student: number, image: string) => call<OwnOcr>("POST", "/own/ocr", { student, image }),
  ownMatch: (student: number, text: string) => call<OwnMatch>("POST", "/own/match", { student, text }),
  ownHelp: (student: number, own_id: number, doubt: string) =>
    call<OwnHelp>("POST", "/own/help", { student, own_id, doubt }),
};

// Per a la pàgina antiga d'estat
export const getHealth = api.health;
