"use client";

import { Logo, Mark } from "@/components/brand/logo";
import { DoubleCard, Eyebrow, Pill } from "@/components/ui/surface";
import { api, useBackendMode } from "@/lib/api";
import { useLive } from "@/lib/use-live";
import { cn } from "@/lib/utils";
import { ArrowUpRight, Cpu, ShieldCheck, UserX, WifiOff } from "lucide-react";
import Link from "next/link";
import { MiniChat, MiniRepte } from "./mini-product";
import { Reveal } from "./reveal";
import {
    VisualAnswer,
    VisualBoard,
    VisualFrame,
    VisualLadder,
    VisualQuestion,
} from "./visuals";

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
    // Com les seccions de Faktu (modulos-section.tsx): etiqueta a dalt; a sota, el
    // títol a l'esquerra i l'entradeta a la dreta, amb la mateixa mida de lletra.
    // El títol no es parteix des de lg; l'entradeta s'encongeix si cal.
    <Reveal className="pb-12 md:pb-16">
      <div className="mb-5 flex items-center gap-2.5 md:mb-8">
        <Eyebrow>{eyebrow}</Eyebrow>
        {pill && <Pill>{pill}</Pill>}
      </div>
      <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between md:gap-12">
        <h2
          className="md:max-w-xl lg:max-w-none lg:shrink-0 lg:whitespace-nowrap"
          style={{ fontSize: "clamp(28px, 3.6vw, 48px)", fontWeight: 500, letterSpacing: "-0.03em", lineHeight: 1.05 }}
        >
          {title}
        </h2>
        <p className="max-w-sm min-w-0 text-sm leading-relaxed font-light text-muted-foreground md:pb-1 md:text-base">
          {lead}
        </p>
      </div>
    </Reveal>
  );
}

export function SectionDivider() {
  return <div aria-hidden className="h-32 md:h-52" />;
}

/* ------------------------------------------------------------------ */
/* Franja de confiança                                                */
/* ------------------------------------------------------------------ */

export function TrustBar() {
  const items = [
    { icon: WifiOff, label: "Sense internet" },
    { icon: UserX, label: "Sense comptes" },
    { icon: ShieldCheck, label: "509 problemes verificats" },
    { icon: Cpu, label: "Tot a la placa" },
  ];
  return (
    <div className={cn(CONTAINER, "pt-12 md:pt-16")}>
      <Reveal className="grid grid-cols-2 justify-items-center gap-x-8 gap-y-4 md:flex md:justify-center md:gap-14">
        {items.map(({ icon: Icon, label }) => (
          <span key={label} className="flex items-center gap-2 text-[13px] font-medium text-foreground/70 md:text-[14px]">
            <Icon className="size-4 text-muted-foreground" /> {label}
          </span>
        ))}
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Targeta amb il·lustració (Com funciona i Modes)                    */
/* ------------------------------------------------------------------ */

function FeatureCard({
  index,
  step,
  title,
  text,
  visual,
  large = false,
}: {
  index: number;
  step?: string;
  title: string;
  text: string;
  visual: React.ReactNode;
  large?: boolean;
}) {
  return (
    <DoubleCard
      index={index}
      className="flex h-full flex-col gap-6 p-5 transition-shadow duration-300 ease-motion-enter hover:shadow-[0_2px_4px_rgba(0,0,0,0.03),0_18px_40px_-16px_rgba(0,0,0,0.14)] md:p-6"
    >
      <VisualFrame className={large ? "h-[230px] sm:h-[370px] md:h-[220px] lg:h-[290px] xl:h-[390px]" : undefined}>
        {visual}
      </VisualFrame>
      <div className="flex flex-col gap-1.5 px-1 pb-1">
        {step && <span className="font-mono text-[11px] font-semibold text-accent">{step}</span>}
        <h3 className={cn("font-medium tracking-[-0.015em]", large ? "text-2xl" : "text-lg")}>{title}</h3>
        <p className="max-w-sm text-[15px] leading-relaxed font-light text-muted-foreground">{text}</p>
      </div>
    </DoubleCard>
  );
}

/* ------------------------------------------------------------------ */
/* Com funciona: tres passos                                          */
/* ------------------------------------------------------------------ */

const STEPS = [
  { title: "Respon", text: "Un problema del Cangur al teu nivell.", visual: <VisualAnswer /> },
  { title: "T'encalles? Et preguntem", text: "Una sola pregunta sobre com ho has pensat.", visual: <VisualQuestion /> },
  { title: "Pista a pista", text: "Ajudes graduades. La solució, només si la demanes.", visual: <VisualLadder /> },
];

export function HowSection() {
  return (
    <section id="com-funciona" className={cn(CONTAINER, "scroll-mt-24")}>
      <SectionHeader
        eyebrow="Com funciona"
        title={
          <>
            Et donem el camí, <span className="text-gradient">no la resposta.</span>
          </>
        }
        lead="Tres passos. Cap resposta regalada."
      />
      <div className="grid grid-cols-1 gap-5 md:grid-cols-3 md:gap-6">
        {STEPS.map((s, i) => (
          <Reveal key={s.title} delay={i * 90} className="h-full">
            <FeatureCard index={i} step={`0${i + 1}`} title={s.title} text={s.text} visual={s.visual} />
          </Reveal>
        ))}
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Modes: dues portes                                                 */
/* ------------------------------------------------------------------ */

export function ModesSection() {
  return (
    <section id="modes" className={cn(CONTAINER, "scroll-mt-24")}>
      <SectionHeader
        eyebrow="Dos modes"
        title={
          <>
            Practica el Cangur. <span className="text-gradient">Porta els deures.</span>
          </>
        }
        lead="Problemes verificats al teu nivell, o el teu propi problema amb una foto."
      />
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 md:gap-6">
        <Reveal className="h-full">
          <Link href="/app/repte/" className="group block h-full rounded-2xl outline-none focus-visible:ring-3 focus-visible:ring-accent/40">
            <FeatureCard
              index={0}
              large
              title="Repte Cangur"
              text="El nivell s'ajusta a cada resposta."
              visual={<MiniRepte />}
            />
          </Link>
        </Reveal>
        <Reveal delay={90} className="h-full">
          <Link href="/app/xat/" className="group block h-full rounded-2xl outline-none focus-visible:ring-3 focus-visible:ring-accent/40">
            <FeatureCard
              index={1}
              large
              title="El meu problema"
              text="Fes-hi una foto i la IA el resol amb tu."
              visual={<MiniChat />}
            />
          </Link>
        </Reveal>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* La placa: dades en directe                                         */
/* ------------------------------------------------------------------ */

export function BoardSection() {
  const { data: stats, error } = useLive(() => api.stats(), 5000);
  const demo = useBackendMode() === "demo";
  const q = stats?.questions;
  const tiles = [
    { label: "IA local", value: stats ? (stats.llm === "up" ? "Activa" : "En repòs") : "—", live: stats?.llm === "up" },
    { label: "Resposta mitjana", value: q?.median_seconds != null ? `${q.median_seconds.toFixed(1)} s` : "—" },
    { label: "Dades que surten", value: "0" },
  ];
  return (
    <section id="placa" className={cn(CONTAINER, "scroll-mt-24")}>
      <SectionHeader
        eyebrow="La placa"
        pill={demo ? "Mode demo" : error ? "Sense connexió" : "En directe"}
        title={
          <>
            Tot passa aquí. <span className="text-gradient">Res surt.</span>
          </>
        }
        lead="Una Arduino UNO Q a l'aula: el model, els problemes i el progrés hi viuen a dins."
      />
      <Reveal>
        <DoubleCard plain className="grid gap-6 p-5 md:grid-cols-[1.3fr_1fr] md:items-center md:gap-10 md:p-6">
          <VisualFrame className="h-64 md:h-72">
            <VisualBoard />
          </VisualFrame>
          <div className="grid grid-cols-3 gap-3 md:grid-cols-1 md:gap-4 md:pr-4">
            {tiles.map((t) => (
              <div key={t.label} className="flex flex-col gap-1 border-black/[0.06] md:border-b md:pb-4 md:last:border-0">
                <span className="flex items-center gap-1.5 text-[10px] font-semibold tracking-widest text-muted-foreground uppercase">
                  {t.live !== undefined && (
                    <span className={cn("size-1.5 rounded-full", t.live ? "bg-success animate-pulse-soft" : "bg-black/20")} />
                  )}
                  {t.label}
                </span>
                <span className="font-mono text-[clamp(20px,2.4vw,30px)] font-semibold tracking-[-0.02em] tabular-nums">
                  {t.value}
                </span>
              </div>
            ))}
          </div>
        </DoubleCard>
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
          <div className="relative flex flex-col items-center gap-5 rounded-xl bg-white px-6 py-12 text-center md:py-14">
            <Mark className="h-8 text-foreground" />
            <h2 style={{ fontSize: "clamp(26px, 3.2vw, 40px)", fontWeight: 500, letterSpacing: "-0.03em", lineHeight: 1.05 }}>
              El primer problema <span className="text-gradient">t&apos;espera.</span>
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
    <footer className={cn(CONTAINER, "mt-32 border-t border-black/[0.06] pt-16 pb-10 md:mt-44")}>
      <div className="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr]">
        <div className="flex flex-col gap-3">
          <Logo className="h-6 self-start text-foreground" />
          <p className="max-w-xs text-sm leading-relaxed font-light text-gray-600">
            Matemàtiques socràtiques. Datathon FME 2026 · Repte Qualcomm.
          </p>
        </div>
        <div className="flex flex-col gap-2.5">
          <p className="text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">Producte</p>
          <Link href="/app/" className="text-sm font-light text-gray-600 hover:text-foreground">
            Comença
          </Link>
          <Link href="/placa/" className="text-sm font-light text-gray-600 hover:text-foreground">
            Sala de màquines
          </Link>
        </div>
        <div className="flex flex-col gap-2.5">
          <p className="text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">Equip</p>
          <p className="text-sm font-light text-gray-600">Subils · Alex · Dídac · David</p>
          <p className="text-[12px] leading-relaxed font-light text-gray-500">
            Problemes: M3Kang (Torres-Camps et al., 2026), només per a recerca. Model: Qwen3.5 0.8B amb llama.cpp.
          </p>
        </div>
      </div>
      <p className="mt-12 text-[10px] text-gray-400">
        Mathey · Funciona sense internet: totes les dades es queden a la placa de l&apos;aula.
      </p>
    </footer>
  );
}
