"use client";

import {
  ArrowUpRight,
  Cpu,
  ImagePlus,
  Lightbulb,
  ListChecks,
  MessageCircleQuestion,
  Puzzle,
  ShieldCheck,
  Sparkles,
  Footprints,
  Lock,
  UserX,
  WifiOff,
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { LedMatrix } from "@/components/app/led-matrix";
import { Logo, Mark } from "@/components/brand/logo";
import { DoubleCard, Eyebrow, Pill } from "@/components/ui/surface";
import { api, cap, useBackendMode } from "@/lib/api";
import { useLive } from "@/lib/use-live";
import { cn } from "@/lib/utils";
import { Reveal } from "./reveal";

/** Contenidor de Faktu per a totes les seccions. */
const CONTAINER = "mx-auto w-full max-w-7xl px-6 md:px-10 lg:px-14";

function SectionHeader({
  eyebrow,
  pill,
  title,
  lead,
}: {
  eyebrow: string;
  pill?: string;
  title: React.ReactNode;
  lead: React.ReactNode;
}) {
  return (
    <Reveal className="grid gap-6 py-10 md:grid-cols-2 md:items-end md:py-14">
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2.5">
          <Eyebrow>{eyebrow}</Eyebrow>
          {pill && <Pill>{pill}</Pill>}
        </div>
        <h2 style={{ fontSize: "clamp(26px, 3.4vw, 46px)", fontWeight: 500, letterSpacing: "-0.025em", lineHeight: 1.08 }}>
          {title}
        </h2>
      </div>
      <p className="max-w-lg text-sm leading-relaxed font-light text-muted-foreground md:text-base">{lead}</p>
    </Reveal>
  );
}

export function SectionDivider() {
  return <div aria-hidden className="h-24 md:h-40" />;
}

/* ------------------------------------------------------------------ */
/* Franja de confiança                                                */
/* ------------------------------------------------------------------ */

export function TrustBar() {
  const { data: health } = useLive(() => api.health(), 15000);
  const items = [
    { icon: WifiOff, label: "Sense internet" },
    { icon: UserX, label: "Sense comptes" },
    { icon: ShieldCheck, label: `${health?.problems ?? 509} problemes verificats` },
    { icon: Cpu, label: "Tot passa a la placa" },
  ];
  return (
    <div className={cn(CONTAINER, "pt-10 md:pt-14")}>
      <Reveal className="flex flex-col items-center gap-5">
        <p className="text-[9px] font-medium tracking-widest text-muted-foreground uppercase md:text-[11px]">
          Pensat per a l&apos;aula: alumnes de 10 a 14 anys
        </p>
        <div className="grid grid-cols-2 gap-x-8 gap-y-4 md:flex md:gap-12">
          {items.map(({ icon: Icon, label }) => (
            <span key={label} className="flex items-center gap-2 text-[13px] font-medium text-foreground/80 md:text-[14px]">
              <Icon className="size-4 text-muted-foreground" /> {label}
            </span>
          ))}
        </div>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Modes: pestanyes que avancen soles                                 */
/* ------------------------------------------------------------------ */

const MODE_TABS = [
  {
    key: "repte",
    title: "Repte Cangur",
    text: "Problemes del Cangur al teu nivell, amb l'Elo que s'ajusta a cada resposta. Si falles, no et diem la bona.",
    visual: <RepteMock />,
  },
  {
    key: "xat",
    title: "Porta el teu problema",
    text: "Fes una foto dels deures. La placa la llegeix, la IA el resol pas a pas amb tu i et proposa un problema del Cangur amb la mateixa idea.",
    visual: <XatMock />,
  },
  {
    key: "facil",
    title: "Lectura fàcil",
    text: "Enunciats amb frases curtes i una idea per línia, per a qui li costa llegir. L'alumne l'activa quan vol; ningú l'etiqueta.",
    visual: <FacilMock />,
  },
];
const TAB_MS = 6000;

export function ModesSection() {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused) return;
    const timer = setTimeout(() => setActive((a) => (a + 1) % MODE_TABS.length), TAB_MS);
    return () => clearTimeout(timer);
  }, [active, paused]);

  return (
    <section id="modes" className={cn(CONTAINER, "scroll-mt-24")}>
      <SectionHeader
        eyebrow="Dos modes"
        pill="A la placa"
        title={
          <>
            Practica el Cangur. <span className="text-gradient">Porta els teus deures.</span>
          </>
        }
        lead="El Repte Cangur entrena el raonament amb 509 problemes verificats. El xat connecta el que fas a classe amb un problema del Cangur que fa servir la mateixa idea."
      />
      <Reveal>
        <DoubleCard
          plain
          className="grid gap-6 p-4 md:grid-cols-[0.9fr_1.1fr] md:p-6"
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
        >
          <div className="flex flex-col gap-2" role="tablist" aria-label="Modes de Mathey">
            {MODE_TABS.map((tab, i) => (
              <button
                key={tab.key}
                role="tab"
                aria-selected={active === i}
                onClick={() => setActive(i)}
                onFocus={() => setPaused(true)}
                onBlur={() => setPaused(false)}
                className={cn(
                  "relative flex flex-col gap-1.5 overflow-hidden rounded-xl p-4 text-left transition-colors md:p-5",
                  active === i ? "bg-white shadow-[0_1px_2px_rgba(0,0,0,0.04),0_6px_20px_rgba(0,0,0,0.05)] ring-1 ring-black/[0.05]" : "hover:bg-black/[0.025]",
                )}
              >
                <span className={cn("text-[17px] font-medium tracking-[-0.01em]", active !== i && "text-muted-foreground")}>
                  {tab.title}
                </span>
                <span className="plegable" data-open={active === i}>
                  <span className="text-[14px] leading-relaxed font-light text-muted-foreground">{tab.text}</span>
                </span>
                {active === i && (
                  <span className="absolute inset-x-4 bottom-0 h-[2px] overflow-hidden rounded-full bg-black/[0.06]">
                    <span
                      key={`${active}-${paused}`}
                      className="block h-full origin-left bg-accent"
                      style={{
                        animation: paused ? "none" : `tab-progress ${TAB_MS}ms linear forwards`,
                        transform: paused ? "scaleX(1)" : undefined,
                      }}
                    />
                  </span>
                )}
              </button>
            ))}
          </div>
          <div className="relative min-h-[320px] overflow-hidden rounded-xl border border-black/[0.05] bg-[radial-gradient(120%_80%_at_80%_0%,#eef5ff,transparent_60%),linear-gradient(#fafafa,#f3f4f3)]">
            <AnimatePresence mode="wait">
              <motion.div
                key={MODE_TABS[active].key}
                initial={{ opacity: 0, scale: 0.98, filter: "blur(6px)" }}
                animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                exit={{ opacity: 0, scale: 0.98, filter: "blur(4px)", transition: { duration: 0.15 } }}
                transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                className="absolute inset-0 flex items-center justify-center p-6"
              >
                {MODE_TABS[active].visual}
              </motion.div>
            </AnimatePresence>
          </div>
        </DoubleCard>
      </Reveal>
      <style>{`@keyframes tab-progress { from { transform: scaleX(0) } to { transform: scaleX(1) } }`}</style>
    </section>
  );
}

function RepteMock() {
  return (
    <div className="flex w-full max-w-md flex-col gap-3">
      <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/[0.05]">
        <Eyebrow>Cangur 2019 · Elo 1047</Eyebrow>
        <p className="mt-2 text-[14px] leading-relaxed">
          La Laia té 3 germans. Cada germà té 2 germanes. Quants fills hi ha a la família?
        </p>
      </div>
      <div className="grid grid-cols-5 gap-2">
        {["A", "B", "C", "D", "E"].map((l, i) => (
          <span
            key={l}
            className={cn(
              "flex flex-col items-center gap-1 rounded-xl bg-white py-2.5 text-[13px] ring-1 ring-black/[0.06]",
              l === "B" && "bg-destructive/[0.04] text-muted-foreground line-through ring-destructive/20",
              l === "C" && "bg-success/[0.07] ring-success/40",
            )}
          >
            <span className="font-mono font-semibold">{l}</span>
            <span>{[4, 5, 6, 7, 8][i]}</span>
          </span>
        ))}
      </div>
      <div className="glass flex items-start gap-2.5 rounded-xl p-3 text-[13px]">
        <Sparkles className="mt-0.5 size-4 shrink-0 text-accent" />
        <span>
          <span className="block font-medium">Has comptat la Laia entre les germanes?</span>
          <span className="text-muted-foreground">Pregunta de la IA de la placa · 6,1 s</span>
        </span>
      </div>
    </div>
  );
}

function XatMock() {
  return (
    <div className="flex w-full max-w-md flex-col gap-3">
      <div className="flex justify-end">
        <span className="flex size-24 items-end overflow-hidden rounded-2xl bg-[linear-gradient(135deg,#e9eef7,#cfd9ea)] p-2 shadow-sm ring-1 ring-black/[0.05]">
          <span className="flex w-full flex-col gap-1">
            <span className="h-1 w-4/5 rounded-full bg-black/20" />
            <span className="h-1 w-3/5 rounded-full bg-black/15" />
            <span className="h-1 w-2/3 rounded-full bg-black/15" />
          </span>
        </span>
      </div>
      <div className="flex gap-2.5">
        <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-black/[0.06]">
          <Mark className="h-3 text-foreground" />
        </span>
        <div className="flex flex-col gap-1.5 text-[13px] leading-relaxed">
          <p>1. Tens 3 caixes de 12 pomes: 3 · 12 = 36.</p>
          <p>2. En regales 7: 36 − 7 = 29.</p>
          <p>
            <strong className="font-semibold">Resultat:</strong> 29 pomes.
          </p>
          <span className="inline-flex w-fit items-center gap-1 rounded-md bg-accent/[0.08] px-1.5 py-0.5 text-[11px] font-medium text-accent">
            <Sparkles className="size-3" /> Proposta de la IA · comprova cada pas
          </span>
        </div>
      </div>
      <div className="glass flex items-center justify-between rounded-2xl p-2 pl-4 text-[13px] text-muted-foreground">
        Què no entens? Pregunta-ho…
        <span className="flex size-7 items-center justify-center rounded-full bg-foreground text-background">
          <ImagePlus className="size-3.5" />
        </span>
      </div>
    </div>
  );
}

function FacilMock() {
  return (
    <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/[0.05]">
      <Eyebrow>Lectura fàcil</Eyebrow>
      <p className="mt-3 text-[19px] leading-[1.6] tracking-wide">
        En Lluís té 7 pomes.
        <br />
        També té 2 plàtans.
        <br />
        Dona 2 pomes a en Jordi.
        <br />
        Quants plàtans li ha donat en Jordi?
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Com funciona: l'escala d'ajudes                                    */
/* ------------------------------------------------------------------ */

const LADDER = [
  { icon: MessageCircleQuestion, title: "Com ho has pensat?", text: "Si falles, la IA de la placa et fa una sola pregunta sobre el teu raonament." },
  { icon: Lightbulb, title: "Una estratègia", text: "Fes un dibuix, prova amb números petits, fes una llista ordenada." },
  { icon: ListChecks, title: "La dada clau", text: "Què és el que importa de l'enunciat i potser se t'ha escapat." },
  { icon: Puzzle, title: "Un problema germà", text: "Un problema més fàcil amb la mateixa idea. El fas i tornes al d'abans." },
  { icon: Footprints, title: "El primer pas", text: "Com començar, sense dir-te on acaba." },
  { icon: Lock, title: "La solució", text: "Només si la demanes expressament, i et preguntem si n'estàs segur." },
];

export function HowSection() {
  return (
    <section id="com-funciona" className={cn(CONTAINER, "scroll-mt-24")}>
      <SectionHeader
        eyebrow="Com funciona"
        title={
          <>
            Mai et donem la resposta. <span className="text-gradient">Et donem el camí.</span>
          </>
        }
        lead="Quan t'encalles, Mathey no et resol el problema: et fa pujar per una escala d'ajudes, un graó cada cop. Totes les pistes s'han verificat abans d'arribar a la placa, i cap no revela la resposta."
      />
      <div className="grid grid-cols-1 gap-px sm:grid-cols-2 lg:grid-cols-3">
        {LADDER.map((step, i) => (
          <Reveal key={step.title} delay={i * 70}>
            <DoubleCard index={i} className="flex h-full flex-col gap-5 p-6 transition-colors hover:bg-foreground/[0.015] md:p-8">
              <div className="relative w-fit">
                <span className="flex size-14 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-black/[0.06]">
                  <step.icon className="size-5 text-foreground/80" />
                </span>
                <span className="absolute -top-1 -right-1 flex size-6 items-center justify-center rounded-full border-2 border-white bg-foreground font-mono text-[11px] font-semibold text-background">
                  {i === 0 ? "?" : i}
                </span>
              </div>
              <div className="flex flex-col gap-1.5">
                <h3 className="text-lg font-medium">{step.title}</h3>
                <p className="text-sm leading-relaxed font-light text-muted-foreground">{step.text}</p>
              </div>
            </DoubleCard>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* La placa: dades en directe                                         */
/* ------------------------------------------------------------------ */

export function BoardSection() {
  const { data: stats, error } = useLive(() => api.stats(), 4000);
  const { data: frame } = useLive(() => api.matrix(), 2000);
  const demo = useBackendMode() === "demo";
  const q = stats?.questions;
  const mem = stats?.memory;
  const tiles = [
    {
      label: "IA de la placa",
      value: stats ? (stats.llm === "up" ? "Activa" : "En repòs") : "—",
      note: "Qwen3.5 0.8B amb llama.cpp",
      live: stats?.llm === "up",
    },
    {
      label: "Temps de la IA (mediana)",
      value: q?.median_seconds != null ? `${q.median_seconds.toFixed(1)} s` : "—",
      note: q ? `${q.from_board} de la placa · ${q.fallback} de reserva` : "preguntes en directe",
    },
    {
      label: "Memòria lliure",
      value: mem ? `${(mem.available_mb / 1024).toFixed(1)} GB` : "—",
      note: mem ? `de ${(mem.total_mb / 1024).toFixed(1)} GB` : "a la placa",
    },
    {
      label: "Banc verificat",
      value: stats ? String(stats.bank.verified) : "509",
      note: "problemes amb pistes, solució i trampes",
    },
    {
      label: "A l'aula avui",
      value: stats ? `${stats.students}` : "—",
      note: stats ? `alumnes · ${stats.attempts} respostes · ${stats.hints} ajudes` : "alumnes",
    },
    {
      label: "Internet",
      value: "No cal",
      note: stats?.internet ? cap(stats.internet) : "cap dada surt de l'escola",
    },
  ];
  return (
    <section id="placa" className={cn(CONTAINER, "scroll-mt-24")}>
      <SectionHeader
        eyebrow="La placa"
        pill={demo ? "Mode demo" : error ? "Sense connexió" : "En directe"}
        title={
          <>
            Tot passa aquí. <span className="text-gradient">Ara mateix.</span>
          </>
        }
        lead="Una Arduino UNO Q a cada aula. El model, el banc de problemes i el progrés dels alumnes hi viuen a dins. Aquestes xifres les llegeix ara mateix de la placa que serveix aquesta pàgina."
      />
      <Reveal>
        <div className="grid grid-cols-1 gap-px lg:grid-cols-[1.1fr_1.9fr]">
          <DoubleCard accent className="flex flex-col items-center justify-center gap-5 p-8 md:p-10">
            <LedMatrix matrix={frame?.matrix} dot={14} />
            <div className="flex flex-col items-center gap-1 text-center">
              <h3 className="text-lg font-medium">La matriu de la placa</h3>
              <p className="max-w-xs text-sm font-light text-muted-foreground">
                Encert, error, «pensant», nivell i ratxa, als LEDs de veritat.
              </p>
            </div>
          </DoubleCard>
          <div className="grid grid-cols-2 gap-px md:grid-cols-3">
            {tiles.map((t, i) => (
              <DoubleCard key={t.label} index={i} className="flex flex-col justify-between gap-6 p-6 md:p-7">
                <span className="flex items-center gap-2 text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">
                  {t.live !== undefined && (
                    <span className={cn("size-1.5 rounded-full", t.live ? "bg-success animate-pulse-soft" : "bg-black/20")} />
                  )}
                  {t.label}
                </span>
                <div>
                  <p className="font-mono text-[clamp(24px,2.6vw,34px)] font-semibold tracking-[-0.02em] tabular-nums">{t.value}</p>
                  <p className="mt-1 text-[13px] leading-snug font-light text-muted-foreground">{t.note}</p>
                </div>
              </DoubleCard>
            ))}
          </div>
        </div>
      </Reveal>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Crida final i peu                                                  */
/* ------------------------------------------------------------------ */

export function FinalCta() {
  return (
    <section className={CONTAINER}>
      <Reveal>
        <div className="relative isolate overflow-hidden rounded-2xl p-[5px]">
          <div
            aria-hidden
            className="absolute inset-[-60%] -z-10 animate-spin-slow bg-[conic-gradient(from_0deg,transparent_0%,var(--accent)_12%,transparent_28%,transparent_100%)] motion-reduce:hidden"
          />
          <div className="relative flex flex-col items-center gap-6 rounded-xl bg-white px-6 py-16 text-center md:py-20">
            <Mark className="h-12 text-foreground animate-float" />
            <h2 style={{ fontSize: "clamp(28px, 4vw, 52px)", fontWeight: 500, letterSpacing: "-0.03em", lineHeight: 1.05 }}>
              Som-hi. <span className="text-gradient">El primer problema t&apos;espera.</span>
            </h2>
            <Link
              href="/app/"
              className="inline-flex items-center gap-2 rounded-xl bg-[#1c1c1d] px-6 py-3 text-[15px] font-medium text-white transition-[opacity,transform] hover:opacity-90 active:scale-[0.98]"
            >
              Comença <ArrowUpRight className="size-4" />
            </Link>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

export function SiteFooter() {
  return (
    <footer className={cn(CONTAINER, "pt-24 pb-10")}>
      <div className="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr]">
        <div className="flex flex-col gap-3">
          <Logo className="h-6 self-start text-foreground" />
          <p className="max-w-sm text-sm leading-relaxed font-light text-gray-600">
            Un mentor de matemàtiques que mai dona la resposta. Fet en 24 hores per a la Datathon FME 2026, repte
            Qualcomm «Math on the Edge».
          </p>
        </div>
        <div className="flex flex-col gap-2.5">
          <p className="text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">Producte</p>
          <Link href="/app/" className="text-sm font-light text-gray-600 hover:text-foreground">Comença</Link>
          <Link href="/placa/" className="text-sm font-light text-gray-600 hover:text-foreground">Sala de màquines</Link>
        </div>
        <div className="flex flex-col gap-2.5">
          <p className="text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">Equip</p>
          <p className="text-sm font-light text-gray-600">Subils · Alex · Dídac · David</p>
          <p className="text-[12px] leading-relaxed font-light text-gray-500">
            Problemes: M3Kang (Torres-Camps et al., 2026), només per a recerca. Model: Qwen3.5 0.8B amb llama.cpp.
          </p>
        </div>
      </div>
      <p className="mt-12 text-[10px] text-gray-400">Mathey · Funciona sense internet: totes les dades es queden a la placa de l&apos;aula.</p>
    </footer>
  );
}
