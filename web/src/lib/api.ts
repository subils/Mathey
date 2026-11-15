// Client de l'API del mentor. Contracte: docs/ARQUITECTURA.md, secció 5.
//
// A la placa, la web i l'API comparteixen origen (port 7000), així que la base
// és buida. Amb `pnpm dev`, la web corre al 3000 i l'API al 7000.
import { useSyncExternalStore } from "react";
import { DEMO_STUDENT, DemoError, demoCall, demoChat, resetDemo } from "./demo";
import { clearSession, loadSession } from "./session";

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
  /** Nivell de l'examen del Cangur d'on surt el problema (dada del problema, no de l'alumne). */
  level: number;
  elo: number;
  year: number;
  topic: string;
  has_figure: boolean;
  text: string;
  options: Partial<Record<Letter, string>>;
  image_url: string;
};

export type Session = {
  student: number;
  alias: string;
  grade: string;
  elo: number;
  matrix?: Matrix;
  /** Només al navegador: la ratxa que ha tornat l'última resposta. */
  streak?: number;
};

export type NextResult = {
  problem: Problem | null;
  elo?: number;
  target_elo?: number;
  /** [mínim, màxim] de l'Elo dels problemes on es pot practicar. */
  elo_range?: [number, number] | null;
  streak?: number;
  message?: string;
  matrix?: Matrix;
};

export type AnswerResult = {
  correct: boolean;
  first_try: boolean;
  streak: number;
  elo: number;
  elo_change: number;
  problem_elo: number;
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
  elo: number;
  elo_start: number;
  elo_peak: number;
  streak: number;
  attempts: number;
  correct: number;
  accuracy: number | null;
  by_topic: { topic: string; attempts: number; correct: number; accuracy: number; avg_hints: number }[];
  recent: { problem_id: string; letter: string; correct: number; hints_used: number; topic: string;
    problem_elo: number | null; elo_before: number | null; elo_after: number | null; ts: string }[];
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
  /** El semblant s'assembla prou (≥ 0,50) perquè la seva idea guiï la IA. */
  same_idea?: boolean;
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
  timings?: Record<string, number>;
};

/** El missatge exacte de mentor/service.py (_student) quan l'alumne no existeix. */
export const UNKNOWN_STUDENT = "alumne desconegut";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

/** La sessió del navegador apunta a un alumne que la placa ja no coneix (state.db esborrat). */
export const isUnknownStudent = (error: unknown) =>
  error instanceof ApiError && error.status === 404 && /alumne/i.test(error.message);

/** Opcions per crida: `signal` per aturar-la i `timeoutMs` (per defecte 70 s, més que el
 *  timeout de la IA de la placa, 40 s, i el de l'OCR, 60 s). */
export type CallOptions = { signal?: AbortSignal; timeoutMs?: number };

/* ------------------------------------------------------------------ */
/* Placa o mode demo                                                   */
/* ------------------------------------------------------------------ */
//
// Si no hi ha cap placa (l'API no respon), la web passa sola al mode demo:
// un backend simulat al navegador (lib/demo.ts) amb problemes inventats. Així
// es pot navegar i dissenyar sense l'Arduino. `?demo=1` el força.

export type BackendMode = "unknown" | "live" | "demo";
let mode: BackendMode = "unknown";
const modeListeners = new Set<() => void>();
const FORCE_KEY = "mathey-force-demo";

function forced() {
  try {
    if (new URLSearchParams(window.location.search).get("demo") === "1") sessionStorage.setItem(FORCE_KEY, "1");
    return sessionStorage.getItem(FORCE_KEY) === "1";
  } catch {
    return false;
  }
}

function setMode(next: BackendMode) {
  if (mode === next) return;
  mode = next;
  modeListeners.forEach((l) => l());
}

/** "unknown" fins a la primera crida; després "live" (placa) o "demo". */
export function useBackendMode(): BackendMode {
  return useSyncExternalStore(
    (l) => {
      modeListeners.add(l);
      return () => modeListeners.delete(l);
    },
    () => mode,
    () => "unknown",
  );
}

/** Torna a buscar la placa. Si respon, surt del mode demo (i l'alumne de demo torna a l'entrada). */
export async function retryLive(): Promise<boolean> {
  try {
    sessionStorage.removeItem(FORCE_KEY);
  } catch {
    /* res */
  }
  try {
    const r = await fetch(`${API_BASE}/api/health`, { cache: "no-store", signal: AbortSignal.timeout(3000) });
    if (!r.ok || !(r.headers.get("content-type") ?? "").includes("json")) return false;
    if (loadSession()?.student === DEMO_STUDENT) clearSession();
    resetDemo();
    setMode("live");
    return true;
  } catch {
    return false;
  }
}

async function viaDemo<T>(method: string, path: string, body?: object): Promise<T> {
  setMode("demo");
  try {
    return (await demoCall(method, path, body as Record<string, unknown>)) as T;
  } catch (error) {
    if (error instanceof DemoError) throw new ApiError(error.status, error.message);
    throw error;
  }
}

async function call<T>(
  method: "GET" | "POST",
  path: string,
  body?: object,
  { signal, timeoutMs = 70_000 }: CallOptions = {},
): Promise<T> {
  if (mode === "demo" || (mode === "unknown" && forced())) return viaDemo<T>(method, path, body);
  // Mentre no se sap si hi ha placa, l'espera és curta: sense placa, a la demo de seguida
  const timeout = AbortSignal.timeout(mode === "unknown" ? Math.min(timeoutMs, 4000) : timeoutMs);
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store",
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    if (mode !== "live") return viaDemo<T>(method, path, body); // no hi ha placa
    if (timeout.aborted) throw new ApiError(504, "La placa ha trigat massa a respondre.");
    throw new ApiError(0, "No hi ha connexió amb la placa.");
  }
  const isJson = (response.headers.get("content-type") ?? "").includes("json");
  // Una web servida sense el mentor al darrere (p. ex. un servidor estàtic): també és demo
  if (!isJson && mode !== "live") return viaDemo<T>(method, path, body);
  setMode("live");
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = (data as { error?: string }).error ?? response.statusText;
    if (response.status === 404 && message === UNKNOWN_STUDENT) {
      // L'alumne guardat al navegador ja no existeix a la placa (p. ex. un state.db
      // nou després d'un desplegament). S'esborra la sessió i les pàgines tornen a l'entrada.
      clearSession();
    }
    throw new ApiError(response.status, message);
  }
  return data as T;
}

export type ChatTurn = { role: "user" | "assistant"; text: string };
export type ChatEvent =
  | { type: "meta"; own_id: number; sibling: Problem | null; strategy: string }
  | { type: "delta"; text: string }
  | {
      type: "done";
      reply: string;
      source: "placa" | "preparat";
      seconds: number;
      rejected: string | null;
      timings: Record<string, number | null>;
    };

/**
 * Xat del mode 2 (POST /api/own/chat): la resposta arriba a trossos (NDJSON).
 * `onEvent` rep cada esdeveniment a mesura que arriba. Torna quan s'acaba.
 */
async function ownChat(
  student: number,
  own_id: number,
  { message, history, signal, onEvent }: {
    message?: string;
    history?: ChatTurn[];
    signal?: AbortSignal;
    onEvent: (event: ChatEvent) => void;
  },
) {
  if (mode === "demo") return demoChat(own_id, { message, history, signal, onEvent });
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/own/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student, own_id, message, history }),
      cache: "no-store",
      signal,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError(0, "No hi ha connexió amb la placa.");
  }
  if (!response.ok || !response.body) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(response.status, (data as { error?: string }).error ?? response.statusText);
  }
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (value) buffer += value;
    let newline: number;
    while ((newline = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, newline).trim();
      buffer = buffer.slice(newline + 1);
      if (line) onEvent(JSON.parse(line) as ChatEvent);
    }
    if (done) break;
  }
  if (buffer.trim()) onEvent(JSON.parse(buffer) as ChatEvent);
}

/** Primera lletra en majúscula (el CSS `capitalize` faria «Combinatòria I Probabilitat»). */
export const cap = (text: string) => (text ? text[0].toUpperCase() + text.slice(1) : text);

/** URL de la imatge del problema, o "" si no en té (els problemes del mode demo són només text). */
export const imageUrl = (problem: Pick<Problem, "image_url">) => (problem.image_url ? `${API_BASE}${problem.image_url}` : "");

export const api = {
  health: () => call<Health>("GET", "/health"),
  session: (alias: string, grade: string) => call<Session>("POST", "/session", { alias, grade }),
  next: (student: number, id?: string, elo?: number) =>
    call<NextResult>(
      "GET",
      `/next?student=${student}${id ? `&id=${encodeURIComponent(id)}` : ""}${elo ? `&elo=${elo}` : ""}`,
    ),
  answer: (student: number, problem_id: string, letter: Letter, seconds: number) =>
    call<AnswerResult>("POST", "/answer", { student, problem_id, letter, seconds }),
  hint: (student: number, problem_id: string, rung: number, confirm = false) =>
    call<HintResult>("POST", "/hint", { student, problem_id, rung, confirm }),
  explain: (student: number, problem_id: string, letter: Letter, text: string, options?: CallOptions) =>
    call<ExplainResult>("POST", "/explain", { student, problem_id, letter, text }, options),
  warm: (problem_id: string) => call<{ started: boolean }>("POST", "/warm", { problem_id }),
  profile: (student: number) => call<Profile>("GET", `/profile?student=${student}`),
  matrix: () => call<{ matrix: Matrix }>("GET", "/matrix"),
  stats: () => call<Stats>("GET", "/stats"),
  ownOcr: (student: number, image: string, options?: CallOptions) =>
    call<OwnOcr>("POST", "/own/ocr", { student, image }, options),
  ownMatch: (student: number, text: string, options?: CallOptions) =>
    call<OwnMatch>("POST", "/own/match", { student, text }, options),
  ownHelp: (student: number, own_id: number, doubt: string, options?: CallOptions) =>
    call<OwnHelp>("POST", "/own/help", { student, own_id, doubt }, options),
  ownChat,
};
