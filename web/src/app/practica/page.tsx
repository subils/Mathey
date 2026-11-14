"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import LedMatrix from "@/components/LedMatrix";
import {
  api,
  imageUrl,
  LETTERS,
  type AnswerResult,
  type ExplainResult,
  type HintResult,
  type Letter,
  type Matrix,
  type Problem,
  type NextResult,
} from "@/lib/api";
import { now, saveSession, useSession } from "@/lib/session";

const THINKING: Matrix = Array.from({ length: 8 }, (_, r) =>
  Array.from({ length: 13 }, (_, c) => ((r === 3 || r === 4) && [2, 6, 10].includes(c) ? 7 : 0)),
);

const RUNGS = [
  { rung: 1, label: "Una estratègia" },
  { rung: 2, label: "La dada clau" },
  { rung: 3, label: "Un problema germà més fàcil" },
  { rung: 4, label: "El primer pas" },
  { rung: 5, label: "La solució" },
];

const LEVEL_NAMES = ["5è de primària", "6è de primària", "1r d'ESO", "2n d'ESO"];

type Phase = "loading" | "answering" | "wrong" | "correct" | "done" | "error";

export default function Practica() {
  const router = useRouter();
  const session = useSession();
  const [problem, setProblem] = useState<Problem | null>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [message, setMessage] = useState("");
  const [matrix, setMatrix] = useState<Matrix | undefined>();
  const [easyOverride, setEasy] = useState<boolean | null>(null);
  const easy = easyOverride ?? session?.easy_mode ?? false;
  const [wrongLetters, setWrongLetters] = useState<Letter[]>([]);
  const [lastLetter, setLastLetter] = useState<Letter | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [hints, setHints] = useState<HintResult[]>([]);
  const [hintBusy, setHintBusy] = useState(false);
  const [confirmSolution, setConfirmSolution] = useState(false);
  const [explainText, setExplainText] = useState("");
  const [explaining, setExplaining] = useState(false);
  const [explained, setExplained] = useState<ExplainResult | null>(null);
  const [original, setOriginal] = useState<Problem | null>(null);
  const [levelState, setLevel] = useState<number | null>(null);
  const level = levelState ?? session?.level ?? null;
  const shownAt = useRef<number>(0);

  const resetProblemState = () => {
    setWrongLetters([]);
    setLastLetter(null);
    setResult(null);
    setHints([]);
    setConfirmSolution(false);
    setExplainText("");
    setExplained(null);
    setMessage("");
  };

  // Aplica el resultat de /api/next (sempre des d'una promesa, mai durant el render)
  const applyNext = useCallback((next: NextResult) => {
    if (next.matrix) setMatrix(next.matrix);
    if (typeof next.level === "number") setLevel(next.level);
    if (!next.problem) {
      setProblem(null);
      setMessage(next.message ?? "No queden problemes.");
      setPhase("done");
      return;
    }
    setProblem(next.problem);
    setPhase("answering");
    shownAt.current = now();
    api.warm(next.problem.id).catch(() => undefined); // la placa llegeix el problema per endavant
  }, []);

  const applyError = useCallback((e: Error) => {
    setMessage(e.message);
    setPhase("error");
  }, []);

  const studentId = session?.student;
  useEffect(() => {
    if (session === undefined) return; // encara no som al navegador
    if (session === null) {
      router.replace("/");
      return;
    }
    const wanted = new URLSearchParams(window.location.search).get("id") ?? undefined;
    api.next(session.student, wanted).then(applyNext, applyError);
    // Només quan canvia l'alumne, no cada cop que es desa el nivell
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentId]);

  function goTo(id?: string) {
    if (!session) return;
    setPhase("loading");
    resetProblemState();
    api.next(session.student, id).then(applyNext, applyError);
  }

  async function choose(letter: Letter) {
    if (!session || !problem) return;
    setLastLetter(letter);
    const seconds = Math.round((now() - shownAt.current) / 1000);
    try {
      const r = await api.answer(session.student, problem.id, letter, seconds);
      setResult(r);
      setMatrix(r.matrix);
      setLevel(r.level);
      saveSession({ ...session, level: r.level });
      if (r.correct) {
        setPhase("correct");
        setMessage(r.level_change > 0 ? `Puges de nivell: ara fas problemes de ${LEVEL_NAMES[r.level]}!` : "");
      } else {
        setWrongLetters((w) => [...w, letter]);
        setExplained(null);
        setExplainText("");
        setPhase("wrong");
        setMessage(r.level_change < 0 ? `Baixem un nivell per agafar confiança: ${LEVEL_NAMES[r.level]}.` : "");
      }
    } catch (e) {
      setMessage((e as Error).message);
    }
  }

  async function explain(event: React.FormEvent) {
    event.preventDefault();
    if (!session || !problem || !lastLetter || !explainText.trim()) return;
    setExplaining(true);
    const before = matrix;
    setMatrix(THINKING);
    try {
      setExplained(await api.explain(session.student, problem.id, lastLetter, explainText.trim()));
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setMatrix(before);
      setExplaining(false);
    }
  }

  async function nextHint(confirm = false) {
    if (!session || !problem) return;
    const rung = hints.length + 1;
    if (rung > 5) return;
    if (rung === 5 && !confirm) {
      setConfirmSolution(true);
      return;
    }
    setHintBusy(true);
    try {
      const h = await api.hint(session.student, problem.id, rung, confirm);
      setHints((list) => [...list, h]);
      setConfirmSolution(false);
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setHintBusy(false);
    }
  }

  function trySibling(sibling: Problem) {
    if (!session || !problem) return;
    setOriginal(problem);
    goTo(sibling.id);
  }

  function backToOriginal() {
    if (!session || !original) return;
    const id = original.id;
    setOriginal(null);
    goTo(id);
  }

  if (!session) return null;

  return (
    <main className="mx-auto grid w-full max-w-5xl flex-1 gap-6 px-4 py-6 lg:grid-cols-[minmax(0,1fr)_300px]">
      {/* ---------------------------------------------- el problema */}
      <section className="flex min-w-0 flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-zinc-500">
          <span>
            {session.alias} · Nivell {level ?? "?"} {level !== null && `(${LEVEL_NAMES[level] ?? ""})`}
            {problem && ` · ${problem.topic}`}
          </span>
          {original && (
            <span className="rounded-full bg-violet-100 px-3 py-1 text-violet-800 dark:bg-violet-900/40 dark:text-violet-200">
              Problema germà del que estaves fent
            </span>
          )}
        </div>

        {phase === "loading" && <p className="py-20 text-center text-zinc-500">Carregant el problema…</p>}
        {(phase === "done" || phase === "error") && (
          <div className="rounded-2xl border border-zinc-200 bg-white p-8 text-center dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-lg">{message}</p>
          </div>
        )}

        {problem && phase !== "loading" && phase !== "done" && (
          <>
            <article className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-2 dark:border-zinc-800">
                <span className="text-xs uppercase tracking-wide text-zinc-500">
                  Cangur {problem.year} · nivell {problem.level}
                </span>
                <button
                  onClick={() => setEasy(!easy)}
                  className="rounded-full border border-zinc-300 px-3 py-1 text-xs hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  {easy ? "Veure l'original" : "Lectura fàcil"}
                </button>
              </div>
              {easy && problem.easy_text ? (
                <div className="flex flex-col gap-4 p-6">
                  <p className="whitespace-pre-line text-2xl leading-relaxed tracking-wide">{problem.easy_text}</p>
                  {problem.has_figure && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={imageUrl(problem)} alt="Figura del problema" className="w-full rounded-lg bg-white" />
                  )}
                </div>
              ) : (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={imageUrl(problem)} alt={problem.text} className="w-full bg-white" />
              )}
            </article>

            <div className="grid grid-cols-5 gap-2">
              {LETTERS.map((letter) => {
                const wrong = wrongLetters.includes(letter);
                const right = phase === "correct" && result?.answer === letter;
                return (
                  <button
                    key={letter}
                    onClick={() => choose(letter)}
                    disabled={phase === "correct" || wrong}
                    className={`flex flex-col items-center gap-0.5 rounded-2xl border-2 px-2 py-3 text-2xl font-bold transition ${
                      right
                        ? "border-emerald-500 bg-emerald-50 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200"
                        : wrong
                          ? "border-red-200 bg-red-50 text-red-300 line-through dark:border-red-900 dark:bg-red-950/40"
                          : "border-zinc-200 bg-white hover:border-amber-400 hover:bg-amber-50 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:bg-zinc-800"
                    }`}
                  >
                    {letter}
                    {problem.options[letter] && (
                      <span className="max-w-full truncate text-xs font-normal text-zinc-500">{problem.options[letter]}</span>
                    )}
                  </button>
                );
              })}
            </div>

            {message && <p className="rounded-xl bg-amber-100 px-4 py-2 text-amber-900 dark:bg-amber-900/30 dark:text-amber-100">{message}</p>}

            {phase === "correct" && result && (
              <div className="flex flex-col gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 dark:border-emerald-900 dark:bg-emerald-950/40">
                <p className="text-xl font-semibold text-emerald-800 dark:text-emerald-200">
                  Molt bé! Era la {result.answer}.
                </p>
                {result.key_idea && <p className="text-emerald-900 dark:text-emerald-100">💡 {result.key_idea}</p>}
                {result.solution && (
                  <details className="text-sm">
                    <summary className="cursor-pointer text-emerald-800 dark:text-emerald-300">Mira com es resol</summary>
                    <ol className="mt-2 list-decimal space-y-1 pl-5">
                      {result.solution.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ol>
                  </details>
                )}
                <div className="flex flex-wrap gap-2">
                  {original ? (
                    <button onClick={backToOriginal} className="rounded-full bg-violet-600 px-5 py-2 font-medium text-white hover:bg-violet-700">
                      Ara torna al problema d&apos;abans
                    </button>
                  ) : (
                    <button onClick={() => goTo()} className="rounded-full bg-emerald-600 px-5 py-2 font-medium text-white hover:bg-emerald-700">
                      Següent problema
                    </button>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </section>

      {/* ---------------------------------------------- el mentor */}
      <aside className="flex flex-col gap-4">
        <div className="flex justify-center rounded-2xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <LedMatrix matrix={matrix} size={12} />
        </div>

        {phase === "wrong" && lastLetter && (
          <div className="flex flex-col gap-3 rounded-2xl border border-red-200 bg-white p-4 dark:border-red-900 dark:bg-zinc-900">
            <p className="font-semibold">La {lastLetter} no és. Com ho has pensat?</p>
            {!explained ? (
              <form onSubmit={explain} className="flex flex-col gap-2">
                <textarea
                  value={explainText}
                  onChange={(e) => setExplainText(e.target.value)}
                  rows={3}
                  maxLength={300}
                  placeholder="Explica en una frase què has fet…"
                  className="rounded-xl border border-zinc-300 p-3 text-sm outline-none focus:border-amber-500 dark:border-zinc-700 dark:bg-zinc-950"
                />
                <button
                  disabled={explaining || !explainText.trim()}
                  className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
                >
                  {explaining ? "La placa està pensant…" : "Explica-li al mentor"}
                </button>
              </form>
            ) : (
              <div className="flex flex-col gap-2">
                <p className="rounded-xl bg-amber-50 p-3 text-base dark:bg-amber-950/40">{explained.reply}</p>
                <p className="text-[11px] text-zinc-500">
                  {explained.source === "placa"
                    ? `Pregunta de la IA de la placa · ${explained.seconds.toLocaleString("ca")} s`
                    : "Ajuda preparada (la IA de la placa no ha respost a temps)"}
                </p>
              </div>
            )}
            <p className="text-sm text-zinc-500">Torna-ho a provar quan ho vegis clar.</p>
          </div>
        )}

        {problem && phase !== "correct" && phase !== "loading" && phase !== "done" && (
          <div className="flex flex-col gap-3 rounded-2xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
            <p className="font-semibold">Escala d&apos;ajudes</p>
            <ol className="flex flex-col gap-2">
              {hints.map((h) => (
                <li key={h.rung} className="rounded-xl bg-zinc-50 p-3 text-sm dark:bg-zinc-800/60">
                  <span className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                    {h.rung}. {RUNGS[h.rung - 1].label}
                  </span>
                  {h.type === "germa" ? (
                    h.problem ? (
                      <div className="flex flex-col gap-2">
                        <span>{h.text}</span>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={imageUrl(h.problem)} alt="Problema germà" className="rounded-lg border bg-white" />
                        <button
                          onClick={() => trySibling(h.problem as Problem)}
                          className="self-start rounded-full bg-violet-600 px-4 py-1.5 text-white hover:bg-violet-700"
                        >
                          Fes aquest primer
                        </button>
                      </div>
                    ) : (
                      <span>{h.text}</span>
                    )
                  ) : h.type === "solucio" ? (
                    <div>
                      <ol className="list-decimal space-y-1 pl-5">
                        {h.steps?.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ol>
                      <p className="mt-2 font-semibold">
                        Resposta: {h.answer} ({h.answer_text})
                      </p>
                    </div>
                  ) : (
                    <span>{h.blocked ? "Aquesta pista no ha passat el control. Prova el graó següent." : h.text}</span>
                  )}
                </li>
              ))}
            </ol>
            {hints.length < 5 &&
              (confirmSolution ? (
                <div className="flex flex-col gap-2 rounded-xl border border-amber-300 p-3 text-sm">
                  <span>Segur que vols veure la solució? Encara pots provar-ho sol.</span>
                  <div className="flex gap-2">
                    <button onClick={() => nextHint(true)} className="rounded-full bg-amber-500 px-3 py-1 text-white">
                      Sí, ensenya-me-la
                    </button>
                    <button onClick={() => setConfirmSolution(false)} className="rounded-full border px-3 py-1">
                      Ho provo una mica més
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => nextHint()}
                  disabled={hintBusy}
                  className="rounded-full border border-amber-400 px-4 py-2 text-sm font-medium text-amber-800 hover:bg-amber-50 disabled:opacity-50 dark:text-amber-200 dark:hover:bg-amber-950/40"
                >
                  {hints.length === 0 ? "Necessito ajuda" : `Més ajuda: ${RUNGS[hints.length].label.toLowerCase()}`}
                </button>
              ))}
          </div>
        )}

        <Link href="/perfil/" className="text-center text-sm text-zinc-500 underline-offset-2 hover:underline">
          Mira el teu progrés
        </Link>
      </aside>
    </main>
  );
}
