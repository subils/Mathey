"use client";

import { ArrowUpRight, Check, Plus, RotateCcw, ScanText, Sparkles, TriangleAlert } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import { Mark } from "@/components/brand/logo";
import { Composer } from "@/components/chat/composer";
import { Markdown } from "@/components/chat/markdown";
import { Thinking } from "@/components/chat/thinking";
import { Button } from "@/components/ui/button";
import { ChatContainerContent, ChatContainerRoot, ChatContainerScrollAnchor } from "@/components/ui/chat-container";
import { TextArea } from "@/components/ui/field";
import { Eyebrow } from "@/components/ui/surface";
import { api, ApiError, cap, imageUrl, type ChatTurn, type OwnMatch, type Problem } from "@/lib/api";
import { ImageError, shrinkImage } from "@/lib/image";
import { useStudent } from "@/lib/use-student";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/* Missatges                                                           */
/* ------------------------------------------------------------------ */

type Msg =
  | { id: number; kind: "user"; text: string; image?: string }
  | { id: number; kind: "ocr"; text: string; done: boolean }
  | { id: number; kind: "match"; topic: string; sibling: Problem | null; sameIdea: boolean }
  | {
      id: number;
      kind: "ai";
      text: string;
      streaming: boolean;
      source?: "placa" | "preparat";
      seconds?: number;
    }
  | { id: number; kind: "note"; text: string; tone?: "error" | "info" };

type DistributiveOmit<T, K extends PropertyKey> = T extends unknown ? Omit<T, K> : never;

type Busy = null | "ocr" | "match" | "ai";

const SUGGESTIONS = [
  "Tinc 3 caixes amb 12 pomes cada una i en regalo 7. Quantes pomes em queden?",
  "Un rectangle fa 24 cm de perímetre i 8 cm de llarg. Quina és la seva àrea?",
  "Quants nombres de dues xifres tenen les dues xifres parelles?",
];

let nextId = 1;
const newId = () => nextId++;

export default function Xat() {
  const { session, onApiError } = useStudent();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [draft, setDraft] = useState("");
  const [image, setImage] = useState<{ file: File; preview: string } | null>(null);
  const [busy, setBusy] = useState<Busy>(null);
  const [ownId, setOwnId] = useState<number | null>(null);
  const abort = useRef<AbortController | null>(null);

  const push = (msg: DistributiveOmit<Msg, "id">) => {
    const id = newId();
    setMessages((m) => [...m, { ...msg, id } as Msg]);
    return id;
  };
  const patch = (id: number, change: Partial<Msg>) =>
    setMessages((m) => m.map((x) => (x.id === id ? ({ ...x, ...change } as Msg) : x)));

  const fail = useCallback(
    (error: unknown) => {
      if (onApiError(error)) return;
      if (error instanceof DOMException && error.name === "AbortError") return;
      const text = error instanceof Error ? error.message : "Alguna cosa ha fallat.";
      setMessages((m) => [...m, { id: newId(), kind: "note", tone: "error", text: cap(text) }]);
    },
    [onApiError],
  );

  const attach = useCallback((file: File) => {
    setImage((old) => {
      if (old) URL.revokeObjectURL(old.preview);
      return { file, preview: URL.createObjectURL(file) };
    });
  }, []);
  // En treure-la, s'allibera. En enviar-la, la vista prèvia passa al missatge i es queda.
  const removeImage = useCallback(() => {
    setImage((old) => {
      if (old) URL.revokeObjectURL(old.preview);
      return null;
    });
  }, []);

  /* ---------------- 1. La IA resol (streaming) ---------------- */
  async function solve(id: number, message?: string, history?: ChatTurn[]) {
    if (!session) return;
    const controller = new AbortController();
    abort.current = controller;
    setBusy("ai");
    const aiId = push({ kind: "ai", text: "", streaming: true });
    let text = "";
    try {
      await api.ownChat(session.student, id, {
        message,
        history,
        signal: controller.signal,
        onEvent: (event) => {
          if (event.type === "delta") {
            text += event.text;
            patch(aiId, { text });
          } else if (event.type === "done") {
            patch(aiId, { text: event.reply, streaming: false, source: event.source, seconds: event.seconds });
          }
        },
      });
    } catch (error) {
      if (controller.signal.aborted) {
        patch(aiId, { streaming: false, text: text || "_Aturat._" });
      } else {
        patch(aiId, { streaming: false });
        if (!text) setMessages((m) => m.filter((x) => x.id !== aiId));
        fail(error);
      }
    } finally {
      setMessages((m) => m.map((x) => (x.id === aiId && x.kind === "ai" ? { ...x, streaming: false } : x)));
      setBusy(null);
      abort.current = null;
    }
  }

  /* ---------------- 2. Busca el semblant i resol ---------------- */
  async function startProblem(statement: string) {
    if (!session) return;
    if (statement.trim().split(/\s+/).length < 4) {
      push({ kind: "note", tone: "info", text: "Escriu l'enunciat sencer del problema, com a mínim una frase." });
      return;
    }
    setBusy("match");
    let match: OwnMatch;
    try {
      match = await api.ownMatch(session.student, statement);
    } catch (error) {
      setBusy(null);
      fail(error);
      return;
    }
    setOwnId(match.own_id);
    push({
      kind: "match",
      topic: match.topic,
      sibling: match.found ? (match.siblings[0] ?? null) : null,
      sameIdea: Boolean(match.same_idea),
    });
    await solve(match.own_id);
  }

  /* ---------------- 3. Foto → read_image.py → prompt ---------------- */
  // La placa llegeix la foto amb laptop/read_image.py (enunciat + opcions A–E) i
  // aquest text és el prompt: es resol de seguida, com si l'alumne l'hagués escrit.
  // Només si la lectura és massa curta es demana a l'alumne que la completi.
  async function readPhoto(file: File, preview: string, extra: string) {
    if (!session) return;
    push({ kind: "user", text: extra, image: preview });
    setBusy("ocr");
    let text = "";
    try {
      const data = await shrinkImage(file);
      const ocr = await api.ownOcr(session.student, data);
      text = [ocr.text.trim(), extra.trim()].filter(Boolean).join("\n\n");
      if (ocr.empty || !ocr.text.trim()) {
        text = "";
        push({
          kind: "note",
          tone: "info",
          text: "No he pogut llegir text en aquesta foto. Prova amb més llum i ben de cara, o escriu-me l'enunciat.",
        });
      }
    } catch (error) {
      text = "";
      if (error instanceof ImageError) push({ kind: "note", tone: "error", text: error.message });
      else if (error instanceof ApiError && (error.status === 503 || error.status === 400))
        push({ kind: "note", tone: "info", text: cap(error.message) });
      else fail(error);
    } finally {
      setBusy(null);
    }
    if (!text) return;
    if (text.split(/\s+/).length < 4) {
      push({ kind: "ocr", text, done: false });
      return;
    }
    push({ kind: "ocr", text, done: true });
    await startProblem(text);
  }

  /* ---------------- Enviar ---------------- */
  function submit() {
    const text = draft.trim();
    if (busy || (!text && !image)) return;
    setDraft("");
    if (image) {
      // La vista prèvia es queda al missatge: no es revoca
      const { file, preview } = image;
      setImage(null);
      void readPhoto(file, preview, text);
      return;
    }
    push({ kind: "user", text });
    if (ownId === null) void startProblem(text);
    else void solve(ownId, text, historyFor(messages));
  }

  function reset() {
    abort.current?.abort();
    setMessages([]);
    setOwnId(null);
    setDraft("");
    setImage(null);
  }

  const started = messages.length > 0;
  const pendingOcr = messages.some((m) => m.kind === "ocr" && !m.done);
  if (!session) return null;

  return (
    <main className="mx-auto flex h-[calc(100svh-64px)] w-full max-w-3xl flex-col px-4 md:px-6">
      {!started ? (
        <EmptyState
          composer={
            <Composer
              value={draft}
              onValueChange={setDraft}
              onSubmit={submit}
              image={image?.preview}
              onImage={attach}
              onRemoveImage={removeImage}
              placeholder="Enganxa una foto del problema o escriu-lo aquí…"
              globalDrop
              autoFocus
            />
          }
          onSuggestion={(s) => setDraft(s)}
        />
      ) : (
        <>
          <ChatContainerRoot className="relative -mx-4 flex-1 px-4 md:-mx-6 md:px-6">
            <ChatContainerContent className="gap-5 pt-6 pb-8">
              <div className="flex items-center justify-between">
                <Eyebrow>El meu problema</Eyebrow>
                <Button variant="ghost" size="sm" onClick={reset}>
                  <Plus /> Nou problema
                </Button>
              </div>
              <AnimatePresence initial={false}>
                {messages.map((m) => (
                  <motion.div
                    key={m.id}
                    layout="position"
                    initial={{ opacity: 0, y: 8, filter: "blur(4px)" }}
                    animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                    transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                  >
                    <Message
                      msg={m}
                      busy={busy}
                      onConfirm={(text) => {
                        patch(m.id, { done: true, text });
                        void startProblem(text);
                      }}
                      onRetake={() => patch(m.id, { done: true })}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
              {(busy === "ocr" || busy === "match") && (
                <Thinking
                  label={busy === "ocr" ? "La placa està llegint la foto" : "Buscant problemes semblants al Cangur"}
                />
              )}
              <ChatContainerScrollAnchor />
            </ChatContainerContent>
          </ChatContainerRoot>

          <div className="relative pb-4">
            <div className="pointer-events-none absolute inset-x-0 -top-8 h-8 bg-gradient-to-t from-background to-transparent" />
            <Composer
              value={draft}
              onValueChange={setDraft}
              onSubmit={submit}
              image={image?.preview}
              imageBusy={busy === "ocr"}
              onImage={!pendingOcr ? attach : undefined}
              onRemoveImage={removeImage}
              busy={busy !== null}
              onStop={busy === "ai" ? () => abort.current?.abort() : undefined}
              placeholder={
                ownId === null
                  ? "Enganxa una foto del problema o escriu-lo aquí…"
                  : "Què no entens? Pregunta-ho, o envia la foto d'un altre problema…"
              }
              globalDrop
            />
            <p className="mt-2 text-center text-[11px] text-muted-foreground">
              La IA de la placa pot equivocar-se. Comprova cada pas.
            </p>
          </div>
        </>
      )}
    </main>
  );
}

/** Els últims torns (alumne i IA) del problema actual, per donar context a la pregunta següent. */
function historyFor(messages: Msg[]): ChatTurn[] {
  // Una foto nova a mig xat és un problema nou: només compta des de l'últim «match»
  const start = messages.findLastIndex((m) => m.kind === "match");
  return messages
    .slice(Math.max(start, 0))
    .flatMap((m): ChatTurn[] =>
      m.kind === "user" && m.text
        ? [{ role: "user", text: m.text }]
        : m.kind === "ai" && m.text
          ? [{ role: "assistant", text: m.text }]
          : [],
    )
    .slice(-4);
}

/* ------------------------------------------------------------------ */
/* Estat buit: el compositor al centre                                */
/* ------------------------------------------------------------------ */

function EmptyState({
  composer,
  onSuggestion,
}: {
  composer: React.ReactNode;
  onSuggestion: (text: string) => void;
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 pb-16">
      <div className="flex flex-col items-center gap-4 text-center">
        <Mark className="h-12 text-foreground" />
        <h1 className="text-[clamp(28px,4.4vw,44px)] leading-[1.08] font-medium tracking-[-0.03em]">
          Porta el teu <span className="text-gradient">problema</span>.
        </h1>
        <p className="max-w-md text-[15px] leading-relaxed font-light text-muted-foreground">
          Fes-li una foto o enganxa-la aquí. La IA de la placa el llegeix, el resol pas a pas amb tu i et
          proposa un problema del Cangur que fa servir la mateixa idea.
        </p>
      </div>
      <div className="w-full">{composer}</div>
      <div className="flex w-full flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSuggestion(s)}
            className="max-w-full truncate rounded-full border border-black/[0.06] bg-white/70 px-3.5 py-1.5 text-[13px] text-muted-foreground transition-colors hover:border-black/10 hover:bg-white hover:text-foreground sm:max-w-[280px]"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Un missatge                                                         */
/* ------------------------------------------------------------------ */

function Message({
  msg,
  busy,
  onConfirm,
  onRetake,
}: {
  msg: Msg;
  busy: Busy;
  onConfirm: (text: string) => void;
  onRetake: () => void;
}) {
  switch (msg.kind) {
    case "user":
      return (
        <div className="flex flex-col items-end gap-2">
          {msg.image && (
            // eslint-disable-next-line @next/next/no-img-element -- exportació estàtica
            <img
              src={msg.image}
              alt="La foto del problema"
              className="max-h-64 max-w-[70%] rounded-2xl border border-black/[0.06] object-contain shadow-sm"
            />
          )}
          {msg.text && (
            <p className="max-w-[85%] rounded-[20px] rounded-br-md bg-foreground px-4 py-2.5 text-[15px] leading-relaxed whitespace-pre-wrap text-background">
              {msg.text}
            </p>
          )}
        </div>
      );
    case "ocr":
      return <OcrCard text={msg.text} done={msg.done} busy={busy !== null} onConfirm={onConfirm} onRetake={onRetake} />;
    case "match":
      return <MatchCard topic={msg.topic} sibling={msg.sibling} sameIdea={msg.sameIdea} />;
    case "ai":
      return <AiMessage text={msg.text} streaming={msg.streaming} source={msg.source} seconds={msg.seconds} />;
    case "note":
      return (
        <p
          className={cn(
            "flex items-start gap-2 rounded-xl px-3.5 py-2.5 text-[14px]",
            msg.tone === "error" ? "bg-destructive/[0.07] text-destructive" : "bg-black/[0.04] text-muted-foreground",
          )}
        >
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          {msg.text}
        </p>
      );
  }
}

/** «Resultat: …» en un paràgraf a part i en negreta (la IA l'escriu enganxat a l'últim pas). */
const formatReply = (text: string) => text.replace(/\s*\n?\s*\**Resultat\**\s*:\s*\**/g, "\n\n**Resultat:** ");

function AiAvatar() {
  return (
    <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-black/[0.06]">
      <Mark className="h-3.5 text-foreground" />
    </span>
  );
}

function AiMessage({
  text,
  streaming,
  source,
  seconds,
}: {
  text: string;
  streaming: boolean;
  source?: "placa" | "preparat";
  seconds?: number;
}) {
  return (
    <div className="flex gap-3">
      <AiAvatar />
      <div className="flex min-w-0 flex-1 flex-col gap-2 pt-1">
        {!text && streaming ? (
          <Thinking hint="a la placa, la IA escriu unes 5 paraules per segon" />
        ) : (
          <Markdown streaming={streaming}>{formatReply(text)}</Markdown>
        )}
        {!streaming && source && (
          <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px] text-muted-foreground">
            {source === "placa" ? (
              <>
                <span className="inline-flex items-center gap-1 rounded-md bg-accent/[0.08] px-1.5 py-0.5 font-medium text-accent">
                  <Sparkles className="size-3" /> Proposta de la IA de la placa
                </span>
                <span>Pot equivocar-se: comprova cada pas.</span>
              </>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-md bg-black/[0.05] px-1.5 py-0.5 font-medium">
                Ajuda preparada
              </span>
            )}
            {seconds !== undefined && <span className="font-mono tabular-nums">{seconds.toFixed(1)} s</span>}
          </p>
        )}
      </div>
    </div>
  );
}

function OcrCard({
  text,
  done,
  busy,
  onConfirm,
  onRetake,
}: {
  text: string;
  done: boolean;
  busy: boolean;
  onConfirm: (text: string) => void;
  onRetake: () => void;
}) {
  const [value, setValue] = useState(text);
  return (
    <div className="flex gap-3">
      <AiAvatar />
      <div className="flex min-w-0 flex-1 flex-col gap-3 rounded-2xl border border-black/[0.06] bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
        <div className="flex items-center gap-2 text-[13px] font-medium">
          <ScanText className="size-4 text-accent" />
          Això és el que he llegit
          {!done && <span className="font-normal text-muted-foreground">· corregeix-ho si cal</span>}
        </div>
        {done ? (
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap text-foreground/85">{value}</p>
        ) : (
          <>
            <TextArea value={value} onChange={(e) => setValue(e.target.value)} className="min-h-28 text-[15px]" />
            <div className="flex flex-wrap justify-end gap-2">
              <Button variant="ghost" onClick={onRetake} disabled={busy}>
                <RotateCcw /> Una altra foto
              </Button>
              <Button onClick={() => onConfirm(value)} disabled={busy || value.trim().split(/\s+/).length < 4}>
                <Check /> Està bé, resol-lo
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function MatchCard({ topic, sibling, sameIdea }: { topic: string; sibling: Problem | null; sameIdea: boolean }) {
  return (
    <div className="flex gap-3">
      <AiAvatar />
      <div className="flex min-w-0 flex-1 flex-col gap-3 pt-1">
        <p className="text-[15px] leading-relaxed">
          És un problema de <strong className="font-semibold">{topic}</strong>.
          {sibling
            ? sameIdea
              ? ` He trobat un problema ${sibling.image_url ? "del Cangur" : "d'exemple"} que fa servir la mateixa idea:`
              : ` Aquest problema ${sibling.image_url ? "del Cangur" : "d'exemple"} és del mateix tema, per si vols practicar:`
            : " No he trobat cap problema del Cangur prou semblant, però el resolem igualment."}
        </p>
        {sibling && (
          <Link
            href={`/app/repte/?id=${encodeURIComponent(sibling.id)}`}
            className="group flex items-center gap-4 rounded-2xl border border-black/[0.06] bg-white p-3 pr-4 shadow-[0_1px_3px_rgba(0,0,0,0.03)] transition-colors hover:bg-white/70"
          >
            {sibling.image_url && (
              <>
                {/* eslint-disable-next-line @next/next/no-img-element -- exportació estàtica */}
            <img
              src={imageUrl(sibling)}
              alt=""
              className="h-20 w-28 shrink-0 rounded-lg border border-black/[0.05] bg-white object-contain"
            />
              </>
            )}
            <span className="flex min-w-0 flex-1 flex-col gap-0.5">
              <span className="text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">
                {sibling.image_url ? `Cangur ${sibling.year}` : "Exemple"} · {cap(sibling.topic)}
              </span>
              <span className="line-clamp-2 text-[14px] leading-snug">{sibling.text.replace(/^\d+\.\s*/, "")}</span>
            </span>
            <span className="flex shrink-0 items-center gap-1 text-[13px] font-medium text-accent">
              Practica&apos;l
              <ArrowUpRight className="size-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </span>
          </Link>
        )}
      </div>
    </div>
  );
}
