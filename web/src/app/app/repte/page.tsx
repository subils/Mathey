"use client";

import {
  ArrowRight,
  BookOpenText,
  Check,
  ChevronDown,
  CornerUpLeft,
  Gauge,
  Lightbulb,
  Lock,
  Sparkles,
  Type,
  X,
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { LedMatrix } from "@/components/app/led-matrix";
import { HoppingKangaroo } from "@/components/brand/logo";
import { Composer } from "@/components/chat/composer";
import { Thinking } from "@/components/chat/thinking";
import { Button } from "@/components/ui/button";
import { DoubleCard, Eyebrow } from "@/components/ui/surface";
import {
  api,
  cap,
  imageUrl,
  LETTERS,
  type AnswerResult,
  type ExplainResult,
  type HintResult,
  type Letter,
  type Matrix,
  type NextResult,
  type Problem,
} from "@/lib/api";
import { now, saveSession } from "@/lib/session";
import { useStudent } from "@/lib/use-student";
import { cn } from "@/lib/utils";

/** El «pensant» de mentor/matrix.py, per pintar-lo al mirall mentre la IA respon. */
const THINKING: Matrix = Array.from({ length: 8 }, (_, r) =>
  Array.from({ length: 13 }, (_, c) => ((r === 3 || r === 4) && [2, 6, 10].includes(c) ? 7 : 0)),
);

const RUNGS = [
  { rung: 1, label: "Una estratègia", short: "estratègia" },
  { rung: 2, label: "La dada clau", short: "dada clau" },
  { rung: 3, label: "Un problema germà més fàcil", short: "problema germà" },
  { rung: 4, label: "El primer pas", short: "primer pas" },
  { rung: 5, label: "La solució", short: "solució" },
];

/** Dificultat triada per l'alumne → Elo objectiu respecte del seu (mentor/elo.py). */
const DIFFICULTY = [
  { key: "easier", label: "Més fàcil", delta: -150 },
  { key: "mine", label: "Al meu nivell", delta: 0 },
  { key: "harder", label: "Més difícil", delta: 150 },
] as const;
type Difficulty = (typeof DIFFICULTY)[number]["key"];

type Phase = "loading" | "answering" | "wrong" | "correct" | "done" | "error";

/** Ha creuat una centena cap amunt (p. ex. de 1185 a 1203)? */
const passedHundred = (before: number, after: number) => Math.floor(after / 100) > Math.floor(before / 100);

export default function Repte() {
  const { session, onApiError } = useStudent();
  const [problem, setProblem] = useState<Problem | null>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [message, setMessage] = useState("");
  const [notice, setNotice] = useState("");
  const [matrix, setMatrix] = useState<Matrix | undefined>();
  const [wrongLetters, setWrongLetters] = useState<Letter[]>([]);
  const [lastLetter, setLastLetter] = useState<Letter | null>(null);
  const [shake, setShake] = useState<Letter | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [hints, setHints] = useState<HintResult[]>([]);
  const [hintBusy, setHintBusy] = useState(false);
  const [confirmSolution, setConfirmSolution] = useState(false);
  const [explainText, setExplainText] = useState("");
  const [explaining, setExplaining] = useState(false);
  const [explained, setExplained] = useState<ExplainResult | null>(null);
  const [original, setOriginal] = useState<Problem | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("mine");
  const [eloChange, setEloChange] = useState<number | null>(null);
  const shownAt = useRef(0);
  const easy = session?.easy_mode ?? false;

  const resetProblemState = () => {
    setWrongLetters([]);
    setLastLetter(null);
    setResult(null);
    setHints([]);
    setConfirmSolution(false);
    setExplainText("");
    setExplained(null);
    setMessage("");
    setNotice("");
    setEloChange(null);
  };

  const applyNext = useCallback((next: NextResult) => {
    if (next.matrix) setMatrix(next.matrix);
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

  const applyError = useCallback(
    (error: Error) => {
      if (onApiError(error)) return;
      setMessage(error.message);
      setPhase("error");
    },
    [onApiError],
  );

  const studentId = session?.student;
  useEffect(() => {
    if (!session) return;
    const wanted = new URLSearchParams(window.location.search).get("id") ?? undefined;
    api.next(session.student, wanted).then(applyNext, applyError);
    // Només quan canvia l'alumne, no cada cop que es desa la sessió
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentId]);

  function goTo(id?: string, level: Difficulty = difficulty) {
    if (!session) return;
    setPhase("loading");
    resetProblemState();
    const delta = DIFFICULTY.find((d) => d.key === level)?.delta ?? 0;
    const target = !id && delta && session.elo !== undefined ? session.elo + delta : undefined;
    api.next(session.student, id, target).then(applyNext, applyError);
  }

  async function choose(letter: Letter) {
    if (!session || !problem || phase === "correct" || wrongLetters.includes(letter)) return;
    setLastLetter(letter);
    const seconds = Math.round((now() - shownAt.current) / 1000);
    try {
      const r = await api.answer(session.student, problem.id, letter, seconds);
      setResult(r);
      setMatrix(r.matrix);
      saveSession({ ...session, elo: r.elo, streak: r.streak });
      setEloChange(r.first_try ? r.elo_change : null);
      if (r.correct) {
        setPhase("correct");
        setNotice(passedHundred(r.elo - r.elo_change, r.elo) ? `Has arribat a Elo ${Math.floor(r.elo / 100) * 100}!` : "");
      } else {
        setWrongLetters((w) => [...w, letter]);
        setShake(letter);
        setTimeout(() => setShake(null), 400);
        setExplained(null);
        setExplainText("");
        setPhase("wrong");
        setNotice("");
        // Cada intent compta el temps des d'aquí, no des que es va obrir el problema
        shownAt.current = now();
      }
    } catch (e) {
      if (!onApiError(e)) setNotice((e as Error).message);
    }
  }

  async function explain() {
    if (!session || !problem || !lastLetter || !explainText.trim()) return;
    setExplaining(true);
    const before = matrix;
    setMatrix(THINKING);
    try {
      setExplained(await api.explain(session.student, problem.id, lastLetter, explainText.trim()));
    } catch (e) {
      if (!onApiError(e)) setNotice((e as Error).message);
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
      if (!onApiError(e)) setNotice((e as Error).message);
    } finally {
      setHintBusy(false);
    }
  }

  function trySibling(sibling: Problem) {
    if (!problem) return;
    setOriginal(problem);
    goTo(sibling.id);
  }

  function backToOriginal() {
    if (!original) return;
    const id = original.id;
    setOriginal(null);
    goTo(id);
  }

  // Dreceres de teclat: A–E per respondre, Intro per passar al següent
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target;
      const typing = target instanceof Element && target.closest("textarea, input, [contenteditable]");
      if (typing || e.metaKey || e.ctrlKey || e.altKey) return;
      const key = e.key.toUpperCase();
      if ((phase === "answering" || phase === "wrong") && (LETTERS as string[]).includes(key)) {
        e.preventDefault();
        void choose(key as Letter);
      } else if (phase === "correct" && e.key === "Enter") {
        e.preventDefault();
        if (original) backToOriginal();
        else goTo();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  if (!session) return null;

  return (
    <main className="mx-auto grid w-full max-w-6xl flex-1 gap-6 px-4 pt-6 pb-16 md:px-6 lg:grid-cols-[minmax(0,1fr)_340px]">
      {/* ------------------------------------------------ el problema */}
      <section className="flex min-w-0 flex-col gap-4">
        <TopBar
          problem={problem}
          elo={session.elo}
          eloChange={eloChange}
          difficulty={difficulty}
          onDifficulty={(d) => {
            setDifficulty(d);
            if (phase !== "loading") goTo(undefined, d);
          }}
          original={original}
        />

        {phase === "loading" && (
          <DoubleCard plain className="flex min-h-80 flex-col items-center justify-center gap-4 p-10">
            <HoppingKangaroo className="w-16" label="Carregant el problema" />
            <p className="text-sm font-light text-muted-foreground">Buscant un problema per a tu…</p>
          </DoubleCard>
        )}

        {(phase === "done" || phase === "error") && (
          <DoubleCard plain className="flex flex-col items-center gap-4 p-10 text-center">
            <p className="text-lg">{message}</p>
            <Button onClick={() => goTo()}>Torna-ho a provar</Button>
          </DoubleCard>
        )}

        {problem && phase !== "loading" && phase !== "done" && phase !== "error" && (
          <>
            <ProblemCard
              problem={problem}
              easy={easy}
              onToggleEasy={() => saveSession({ ...session, easy_mode: !easy })}
            />

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-5">
              {LETTERS.map((letter) => (
                <OptionTile
                  key={letter}
                  letter={letter}
                  text={problem.options[letter]}
                  state={
                    phase === "correct" && result?.answer === letter
                      ? "right"
                      : wrongLetters.includes(letter)
                        ? "wrong"
                        : phase === "correct"
                          ? "idle-locked"
                          : "idle"
                  }
                  shake={shake === letter}
                  onClick={() => choose(letter)}
                />
              ))}
            </div>

            <AnimatePresence>
              {notice && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="rounded-xl border border-black/[0.06] bg-white/70 px-4 py-2.5 text-[14px]"
                >
                  {notice}
                </motion.p>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {phase === "correct" && result && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.98, filter: "blur(4px)" }}
                  animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                >
                  <CorrectCard
                    result={result}
                    original={original}
                    onNext={() => goTo()}
                    onBack={backToOriginal}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </section>

      {/* ------------------------------------------------ el mentor */}
      <aside className="flex flex-col gap-4">
        <DoubleCard plain className="flex flex-col items-center gap-3 p-5">
          <LedMatrix matrix={matrix} dot={10} />
          <Eyebrow>La matriu de la placa</Eyebrow>
        </DoubleCard>

        {phase === "wrong" && lastLetter && (
          <DoubleCard accent className="flex flex-col gap-3 p-5">
            <p className="text-[17px] font-medium tracking-[-0.01em]">
              La {lastLetter} no és. <span className="text-muted-foreground">Com ho has pensat?</span>
            </p>
            {explaining ? (
              <Thinking hint="la IA de la placa et prepara una pregunta" />
            ) : explained ? (
              <div className="flex flex-col gap-2">
                <p className="rounded-xl bg-white px-3.5 py-3 text-[15px] leading-relaxed shadow-[0_1px_2px_rgba(0,0,0,0.04)] ring-1 ring-black/[0.05]">
                  {explained.reply}
                </p>
                <p className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
                  {explained.source === "placa" ? (
                    <>
                      <Sparkles className="size-3 text-accent" /> Pregunta de la IA de la placa ·{" "}
                      <span className="font-mono tabular-nums">{explained.seconds.toFixed(1)} s</span>
                    </>
                  ) : (
                    "Ajuda preparada (la IA de la placa no ha respost a temps)"
                  )}
                </p>
                <p className="text-[13px] text-muted-foreground">Torna-ho a provar quan ho vegis clar.</p>
              </div>
            ) : (
              <Composer
                value={explainText}
                onValueChange={(v) => setExplainText(v.slice(0, 300))}
                onSubmit={explain}
                placeholder="Explica en una frase què has fet…"
                autoFocus
              />
            )}
          </DoubleCard>
        )}

        {problem && (phase === "answering" || phase === "wrong") && (
          <HelpLadder
            hints={hints}
            busy={hintBusy}
            confirming={confirmSolution}
            onNext={() => nextHint()}
            onConfirm={() => nextHint(true)}
            onCancel={() => setConfirmSolution(false)}
            onSibling={trySibling}
          />
        )}
      </aside>
    </main>
  );
}

/* ------------------------------------------------------------------ */

function TopBar({
  problem,
  elo,
  eloChange,
  difficulty,
  onDifficulty,
  original,
}: {
  problem: Problem | null;
  elo?: number;
  eloChange: number | null;
  difficulty: Difficulty;
  onDifficulty: (d: Difficulty) => void;
  original: Problem | null;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex flex-wrap items-center gap-2 text-[13px]">
        {problem && (
          <span className="rounded-lg bg-foreground px-2.5 py-1 font-medium text-background">{cap(problem.topic)}</span>
        )}
        {elo !== undefined && (
          <span className="relative inline-flex items-center gap-1.5 rounded-lg border border-black/[0.06] bg-white/70 px-2.5 py-1">
            <span className="text-muted-foreground">Elo</span>
            <span className="font-mono font-medium tabular-nums">{elo}</span>
            <AnimatePresence>
              {eloChange !== null && eloChange !== 0 && (
                <motion.span
                  key={eloChange}
                  initial={{ opacity: 0, y: 6, scale: 0.8 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ type: "spring", visualDuration: 0.3, bounce: 0.4 }}
                  className={cn(
                    "font-mono text-[12px] font-semibold tabular-nums",
                    eloChange > 0 ? "text-success" : "text-destructive",
                  )}
                >
                  {eloChange > 0 ? "+" : ""}
                  {eloChange}
                </motion.span>
              )}
            </AnimatePresence>
          </span>
        )}
        {original && (
          <span className="inline-flex items-center gap-1 rounded-lg bg-accent/10 px-2.5 py-1 font-medium text-accent">
            <CornerUpLeft className="size-3.5" /> Problema germà
          </span>
        )}
      </div>
      <div className="flex items-center gap-1 rounded-xl bg-black/[0.045] p-1" role="radiogroup" aria-label="Dificultat">
        <Gauge className="mx-1.5 size-3.5 text-muted-foreground" />
        {DIFFICULTY.map((d) => (
          <button
            key={d.key}
            role="radio"
            aria-checked={difficulty === d.key}
            onClick={() => onDifficulty(d.key)}
            className={cn(
              "relative rounded-lg px-2.5 py-1 text-[12px] font-medium transition-colors",
              difficulty === d.key ? "text-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {difficulty === d.key && (
              <motion.span
                layoutId="difficulty-pill"
                className="absolute inset-0 -z-10 rounded-lg bg-white shadow-[0_1px_2px_rgba(0,0,0,0.06)]"
                transition={{ type: "spring", visualDuration: 0.25, bounce: 0.15 }}
              />
            )}
            <span className="relative">{d.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function ProblemCard({
  problem,
  easy,
  onToggleEasy,
}: {
  problem: Problem;
  easy: boolean;
  onToggleEasy: () => void;
}) {
  const showEasy = easy && Boolean(problem.easy_text);
  return (
    <DoubleCard plain className="overflow-hidden">
      <div className="flex items-center justify-between gap-3 px-6 pt-5 pb-3">
        <Eyebrow>
          {problem.image_url ? `Cangur ${problem.year}` : "Problema d'exemple"} · Elo {problem.elo}
        </Eyebrow>
        {problem.easy_text && (
          <Button variant="ghost" size="sm" onClick={onToggleEasy}>
            {easy ? <BookOpenText /> : <Type />}
            {easy ? "Veure l'original" : "Lectura fàcil"}
          </Button>
        )}
      </div>
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={`${problem.id}-${showEasy}`}
          initial={{ opacity: 0, filter: "blur(4px)" }}
          animate={{ opacity: 1, filter: "blur(0px)" }}
          exit={{ opacity: 0, transition: { duration: 0.1 } }}
          transition={{ duration: 0.25 }}
          className="px-6 pb-6"
        >
          {showEasy ? (
            <div className="flex flex-col gap-4">
              <p className="text-[clamp(20px,2.4vw,26px)] leading-[1.55] tracking-wide whitespace-pre-line">
                {problem.easy_text}
              </p>
              {problem.has_figure && problem.image_url && (
                // eslint-disable-next-line @next/next/no-img-element -- exportació estàtica
                <img src={imageUrl(problem)} alt="Figura del problema" className="w-full rounded-xl bg-white" />
              )}
            </div>
          ) : problem.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element -- exportació estàtica
            <img src={imageUrl(problem)} alt={problem.text} className="w-full rounded-xl bg-white" />
          ) : (
            // Sense imatge (problemes del mode demo): l'enunciat en text
            <p className="text-[clamp(18px,2vw,22px)] leading-relaxed tracking-[-0.005em]">{problem.text}</p>
          )}
        </motion.div>
      </AnimatePresence>
    </DoubleCard>
  );
}

function OptionTile({
  letter,
  text,
  state,
  shake,
  onClick,
}: {
  letter: Letter;
  text?: string;
  state: "idle" | "idle-locked" | "wrong" | "right";
  shake: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={state !== "idle"}
      aria-label={`Opció ${letter}${text ? `: ${text}` : ""}`}
      className={cn(
        "group relative flex items-center gap-3 rounded-2xl border bg-white p-3 text-left transition-[border-color,background-color,box-shadow,opacity,transform] duration-150 outline-none focus-visible:ring-3 focus-visible:ring-(--app-field-ring) sm:flex-col sm:items-center sm:gap-2 sm:px-2 sm:py-4 sm:text-center",
        state === "idle" &&
          "border-black/[0.07] shadow-[0_1px_2px_rgba(0,0,0,0.04)] hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-[0_6px_20px_rgba(1,113,227,0.10)] active:translate-y-0",
        state === "idle-locked" && "border-black/[0.05] opacity-50",
        state === "wrong" && "border-destructive/20 bg-destructive/[0.04]",
        state === "right" && "border-success/50 bg-success/[0.07] shadow-[0_0_0_4px_color-mix(in_srgb,var(--success)_14%,transparent)]",
        shake && "animate-shake",
      )}
    >
      <span
        className={cn(
          "flex size-10 shrink-0 items-center justify-center rounded-xl font-mono text-[17px] font-semibold transition-colors",
          state === "right"
            ? "bg-success text-white"
            : state === "wrong"
              ? "bg-destructive/10 text-destructive/60"
              : "bg-black/[0.045] text-foreground group-hover:bg-accent group-hover:text-white",
        )}
      >
        {state === "right" ? <Check className="size-5" strokeWidth={3} /> : state === "wrong" ? <X className="size-5" /> : letter}
      </span>
      {text && (
        <span
          className={cn(
            "min-w-0 text-[15px] leading-snug break-words",
            state === "wrong" && "text-muted-foreground line-through decoration-destructive/50",
          )}
        >
          {text}
        </span>
      )}
    </button>
  );
}

function CorrectCard({
  result,
  original,
  onNext,
  onBack,
}: {
  result: AnswerResult;
  original: Problem | null;
  onNext: () => void;
  onBack: () => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative overflow-hidden rounded-2xl border border-success/25 bg-white p-6 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(ellipse 60% 80% at 0% 0%, color-mix(in oklab, var(--success) 12%, transparent), transparent 60%)",
        }}
      />
      <div className="relative flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-full bg-success text-white">
            <Check className="size-5" strokeWidth={3} />
          </span>
          <div>
            <p className="text-[22px] font-medium tracking-[-0.02em]">Molt bé!</p>
            <p className="text-[14px] text-muted-foreground">
              Era la <span className="font-mono font-semibold text-foreground">{result.answer}</span>
              {result.answer_text && <> · {result.answer_text}</>}
              {result.first_try && " · al primer intent"}
            </p>
          </div>
        </div>
        {result.key_idea && (
          <p className="flex gap-2.5 rounded-xl bg-white/80 px-4 py-3 text-[15px] leading-relaxed ring-1 ring-black/[0.05]">
            <Lightbulb className="mt-0.5 size-4 shrink-0 text-amber-500" />
            {result.key_idea}
          </p>
        )}
        {result.solution && result.solution.length > 0 && (
          <div>
            <button
              onClick={() => setOpen((o) => !o)}
              className="flex items-center gap-1.5 text-[14px] font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              <ChevronDown className={cn("size-4 transition-transform duration-200", open && "rotate-180")} />
              Mira com es resol
            </button>
            <div className="plegable" data-open={open}>
              <div>
                <ol className="mt-3 flex flex-col gap-2 pl-1">
                  {result.solution.map((step, i) => (
                    <li key={i} className="flex gap-3 text-[15px] leading-relaxed">
                      <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-black/[0.06] font-mono text-[11px] font-semibold">
                        {i + 1}
                      </span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          </div>
        )}
        <div className="flex flex-wrap items-center gap-2">
          {original ? (
            <Button size="lg" variant="accent" onClick={onBack}>
              <CornerUpLeft /> Ara torna al problema d&apos;abans
            </Button>
          ) : (
            <Button size="lg" onClick={onNext}>
              Següent problema <ArrowRight />
            </Button>
          )}
          <span className="hidden text-[12px] text-muted-foreground sm:inline">
            o prem <kbd className="rounded border border-black/10 bg-white px-1 font-mono text-[11px]">Intro</kbd>
          </span>
        </div>
      </div>
    </div>
  );
}

function HelpLadder({
  hints,
  busy,
  confirming,
  onNext,
  onConfirm,
  onCancel,
  onSibling,
}: {
  hints: HintResult[];
  busy: boolean;
  confirming: boolean;
  onNext: () => void;
  onConfirm: () => void;
  onCancel: () => void;
  onSibling: (p: Problem) => void;
}) {
  const nextRung = hints.length + 1;
  return (
    <DoubleCard plain className="flex flex-col gap-4 p-5">
      <div className="flex items-center justify-between">
        <p className="text-[15px] font-medium">Escala d&apos;ajudes</p>
        <span className="font-mono text-[12px] text-muted-foreground tabular-nums">{hints.length}/5</span>
      </div>
      <ol className="relative flex flex-col gap-3">
        {RUNGS.map((r) => {
          const hint = hints.find((h) => h.rung === r.rung);
          const isNext = r.rung === nextRung;
          return (
            <li key={r.rung} className="relative flex gap-3">
              <span
                className={cn(
                  "z-10 flex size-6 shrink-0 items-center justify-center rounded-full font-mono text-[11px] font-semibold transition-colors",
                  hint ? "bg-foreground text-background" : isNext ? "bg-accent text-white" : "bg-black/[0.06] text-muted-foreground",
                )}
              >
                {r.rung === 5 && !hint ? <Lock className="size-3" /> : r.rung}
              </span>
              {r.rung < 5 && <span aria-hidden className="absolute top-6 left-3 h-[calc(100%-12px)] w-px bg-black/[0.08]" />}
              <div className="flex min-w-0 flex-1 flex-col gap-1.5 pt-0.5">
                <span className={cn("text-[13px] font-medium", !hint && !isNext && "text-muted-foreground")}>{r.label}</span>
                <AnimatePresence initial={false}>
                  {hint && (
                    <motion.div
                      initial={{ opacity: 0, height: 0, filter: "blur(4px)" }}
                      animate={{ opacity: 1, height: "auto", filter: "blur(0px)" }}
                      transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
                      className="overflow-hidden"
                    >
                      <HintBody hint={hint} onSibling={onSibling} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </li>
          );
        })}
      </ol>
      {hints.length < 5 &&
        (confirming ? (
          <div className="flex flex-col gap-2.5 rounded-xl border border-amber-300/70 bg-amber-50/60 p-3.5 text-[14px]">
            <span>Segur que vols veure la solució? Encara ho pots provar tu.</span>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" onClick={onConfirm} disabled={busy}>
                Sí, ensenya-me-la
              </Button>
              <Button size="sm" variant="ghost" onClick={onCancel}>
                Ho provo una mica més
              </Button>
            </div>
          </div>
        ) : (
          <Button variant="outline" size="lg" onClick={onNext} disabled={busy} className="w-full">
            <Lightbulb />
            {busy ? "Un moment…" : hints.length === 0 ? "Necessito ajuda" : `Més ajuda: ${RUNGS[hints.length].short}`}
          </Button>
        ))}
    </DoubleCard>
  );
}

function HintBody({ hint, onSibling }: { hint: HintResult; onSibling: (p: Problem) => void }) {
  if (hint.type === "germa") {
    return (
      <div className="flex flex-col gap-2 text-[14px] leading-relaxed">
        {hint.text && <span>{hint.text}</span>}
        {hint.problem && (
          <>
            {hint.problem.image_url ? (
              // eslint-disable-next-line @next/next/no-img-element -- exportació estàtica
              <img src={imageUrl(hint.problem)} alt="Problema germà" className="rounded-lg border border-black/[0.06] bg-white" />
            ) : (
              <p className="rounded-lg border border-black/[0.06] bg-white p-3">{hint.problem.text}</p>
            )}
            <Button size="sm" variant="accent" className="self-start" onClick={() => onSibling(hint.problem as Problem)}>
              Fes aquest primer <ArrowRight />
            </Button>
          </>
        )}
      </div>
    );
  }
  if (hint.type === "solucio") {
    return (
      <div className="flex flex-col gap-2 text-[14px] leading-relaxed">
        <ol className="list-decimal space-y-1 pl-4">
          {hint.steps?.map((s, i) => <li key={i}>{s}</li>)}
        </ol>
        <p className="font-medium">
          Resposta: <span className="font-mono">{hint.answer}</span>
          {hint.answer_text && <> ({hint.answer_text})</>}
        </p>
      </div>
    );
  }
  return (
    <p className="text-[14px] leading-relaxed text-foreground/85">
      {hint.blocked ? "Aquesta pista no ha passat el control. Prova el graó següent." : hint.text}
    </p>
  );
}
