import { ArrowUp, ArrowUpRight, Check, ImagePlus, Lightbulb, Plus, Sparkles } from "lucide-react";
import { Mark } from "@/components/brand/logo";
import { cn } from "@/lib/utils";

/*
 * Rèpliques en miniatura de les pantalles reals de l'app (/app/repte/ i /app/xat/),
 * simplificades, per a les targetes de la landing. Es dibuixen a mida real i el
 * contenidor les redueix amb una escala, així la proporció i la tipografia són les
 * de l'app. Animació en bucle només amb CSS (.loop-* de globals.css), 6 s.
 */

const d = (seconds: number) => ({ animationDelay: `${seconds}s` });

/** Encaixa una pantalla de mida fixa dins del marc, escalada. */
export function MiniScreen({
  width,
  height,
  scale = "scale-[0.46] sm:scale-[0.8] md:scale-[0.44] lg:scale-[0.6] xl:scale-[0.84]",
  children,
}: {
  width: number;
  height: number;
  /** Escala per amplada de pantalla (la targeta fa la meitat de l'amplada des de md). */
  scale?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="pointer-events-none flex size-full items-center justify-center select-none">
      <div
        className={cn("origin-center", scale)}
        style={{ width, height, flex: "none" }}
      >
        {children}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Repte Cangur                                                        */
/* ------------------------------------------------------------------ */

const OPTIONS: { l: string; v: string; state?: "wrong" | "right" }[] = [
  { l: "A", v: "4", state: "wrong" },
  { l: "B", v: "5", state: "right" },
  { l: "C", v: "6" },
  { l: "D", v: "7" },
  { l: "E", v: "8" },
];

/**
 * Repte Cangur com a composició de producte: la targeta del problema, gran i
 * protagonista; darrere, els problemes següents; a sobre, l'escala d'ajudes i
 * l'avís d'encert. Bucle: la A es descarta, la B s'encerta, «Molt bé!».
 */
export function MiniRepte() {
  return (
    <MiniScreen width={540} height={380} scale="scale-[0.55] sm:scale-[0.95] md:scale-[0.5] lg:scale-[0.7] xl:scale-[1]">
      <div className="relative flex h-full items-center justify-center text-left">
        {/* Els problemes següents, darrere */}
        <div className="absolute inset-x-14 top-6 h-56 rounded-[22px] bg-white/55 shadow-[0_1px_2px_rgba(0,0,0,0.04)] ring-1 ring-black/[0.03]" />
        <div className="absolute inset-x-8 top-10 h-56 rounded-[22px] bg-white/80 shadow-[0_1px_2px_rgba(0,0,0,0.04)] ring-1 ring-black/[0.03]" />

        {/* El problema */}
        <div className="relative mt-8 w-[480px] rounded-[22px] bg-white p-6 shadow-[0_1px_2px_rgba(0,0,0,0.05),0_24px_48px_-24px_rgba(0,0,0,0.22)] ring-1 ring-black/[0.05]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="rounded-lg bg-foreground px-2.5 py-1 text-[12px] font-medium text-background">Aritmètica</span>
              <span className="rounded-lg bg-black/[0.045] px-2.5 py-1 font-mono text-[12px] font-medium text-foreground/70">
                Elo 1100
              </span>
            </div>
            <span className="text-[10px] font-semibold tracking-widest text-muted-foreground uppercase">Cangur 2019</span>
          </div>

          <p className="mt-5 text-[19px] leading-[1.45] font-medium tracking-[-0.01em]">
            La Laia té 3 germans. Cada germà té 2 germanes. Quants fills hi ha a la família?
          </p>

          <div className="mt-6 grid grid-cols-5 gap-2">
            {OPTIONS.map((o) => (
              <span
                key={o.l}
                className={cn(
                  "flex h-12 items-center justify-center gap-2 rounded-xl border border-black/[0.07] bg-white",
                  o.state === "wrong" && "loop-wrong",
                  o.state === "right" && "loop-correct",
                )}
              >
                <span
                  className={cn(
                    "flex size-6 items-center justify-center rounded-md bg-black/[0.045] font-mono text-[12px] font-semibold",
                    o.state === "right" && "loop-correct-badge",
                  )}
                >
                  {o.l}
                </span>
                <span className={cn("text-[15px] font-medium", o.state === "wrong" && "relative")}>
                  {o.v}
                  {o.state === "wrong" && (
                    <span className="loop-strike absolute -inset-x-1 top-1/2 h-[1.5px] rounded-full bg-destructive/70" />
                  )}
                </span>
              </span>
            ))}
          </div>
        </div>

        {/* L'escala d'ajudes, flotant */}
        <div className="absolute top-2 right-0 flex items-center gap-3 rounded-2xl bg-white/90 py-2.5 pr-3.5 pl-2.5 shadow-[0_1px_2px_rgba(0,0,0,0.05),0_12px_28px_-12px_rgba(0,0,0,0.2)] ring-1 ring-black/[0.05] backdrop-blur">
          <span className="flex size-8 items-center justify-center rounded-xl bg-accent-subtle text-accent">
            <Lightbulb className="size-4" />
          </span>
          <span className="flex flex-col gap-1.5">
            <span className="text-[12px] font-medium">Pista 1 de 5</span>
            <span className="flex gap-1">
              {[0, 1, 2, 3, 4].map((i) => (
                <span
                  key={i}
                  className={cn("h-1 w-5 rounded-full", i === 0 ? "bg-foreground" : i === 1 ? "bg-accent/50" : "bg-black/[0.08]")}
                />
              ))}
            </span>
          </span>
        </div>

        {/* L'avís d'encert */}
        <div
          className="loop-count absolute bottom-1 left-6 flex items-center gap-2.5 rounded-2xl bg-foreground py-2.5 pr-4 pl-2.5 text-background shadow-[0_16px_32px_-12px_rgba(0,0,0,0.45)]"
          style={d(0)}
        >
          <span className="flex size-7 items-center justify-center rounded-full bg-success">
            <Check className="size-4" strokeWidth={3} />
          </span>
          <span className="text-[13px] font-medium">
            Molt bé! Era la <span className="font-mono">B</span>
          </span>
        </div>
      </div>
    </MiniScreen>
  );
}

/* ------------------------------------------------------------------ */
/* El meu problema (xat)                                               */
/* ------------------------------------------------------------------ */

const STEPS = [
  <>
    1. Tens 3 caixes de 12: <i className="font-serif">3 · 12 = 36</i> pomes.
  </>,
  <>
    2. En regales 7: <i className="font-serif">36 − 7 = 29</i>.
  </>,
  <>
    <b className="font-semibold">Resultat:</b> 29 pomes.
  </>,
];

export function MiniChat() {
  return (
    <MiniScreen width={560} height={430}>
      <div className="flex h-full flex-col gap-3.5 text-left">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-semibold tracking-widest text-muted-foreground uppercase">El meu problema</span>
          <span className="inline-flex items-center gap-1 text-[12px] font-medium">
            <Plus className="size-3.5" /> Nou problema
          </span>
        </div>

        {/* L'alumne: foto + pregunta */}
        <div className="loop-in flex flex-col items-end gap-2" style={d(0)}>
          <span className="relative h-16 w-24 overflow-hidden rounded-xl border border-black/[0.06] bg-[linear-gradient(135deg,#f6f4f1,#e7e3dd)] shadow-sm">
            <span className="absolute inset-x-2.5 top-3 h-1 rounded-full bg-black/20" />
            <span className="absolute inset-x-2.5 top-5.5 h-1 w-12 rounded-full bg-black/15" />
            <span className="absolute inset-x-2.5 top-8 h-1 w-16 rounded-full bg-black/15" />
            <span className="loop-scan absolute inset-x-0 top-0 h-full bg-gradient-to-b from-transparent via-accent/45 to-transparent" />
          </span>
          <p className="rounded-[18px] rounded-br-md bg-foreground px-4 py-2 text-[14px] text-background">
            Quantes pomes em queden?
          </p>
        </div>

        {/* Semblant del Cangur */}
        <div className="loop-in flex gap-3" style={d(0.5)}>
          <Avatar />
          <div className="flex flex-1 items-center gap-3 rounded-2xl bg-white p-2.5 pr-3.5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] ring-1 ring-black/[0.05]">
            <span className="h-10 w-14 rounded-lg bg-black/[0.04] ring-1 ring-black/[0.05]" />
            <span className="flex-1">
              <span className="block text-[9px] font-semibold tracking-widest text-muted-foreground uppercase">
                Cangur 2015 · Aritmètica
              </span>
              <span className="block text-[12px] leading-snug">En Lluís té 7 pomes i 2 plàtans…</span>
            </span>
            <span className="inline-flex items-center gap-0.5 text-[12px] font-medium text-accent">
              Practica&apos;l <ArrowUpRight className="size-3.5" />
            </span>
          </div>
        </div>

        {/* La IA resol pas a pas */}
        <div className="loop-in flex gap-3" style={d(0.9)}>
          <Avatar />
          <div className="flex flex-1 flex-col gap-1.5 pt-1 text-[14px] leading-relaxed">
            {STEPS.map((step, i) => (
              <p key={i} className="loop-reveal" style={d(1.1 + i * 0.45)}>
                {step}
              </p>
            ))}
            <p className="loop-in mt-1 flex items-center gap-2 text-[11px] text-muted-foreground" style={d(2.6)}>
              <span className="inline-flex items-center gap-1 rounded-md bg-accent-subtle px-1.5 py-0.5 font-medium text-accent">
                <Sparkles className="size-3" /> Proposta de la IA de la placa
              </span>
              Pot equivocar-se
            </p>
          </div>
        </div>

        {/* Compositor */}
        <div className="glass mt-auto flex items-center justify-between rounded-[22px] py-2 pr-2 pl-4">
          <span className="text-[14px] text-(--app-field-placeholder)">Què no entens? Pregunta-ho…</span>
          <span className="flex items-center gap-1.5">
            <span className="flex size-8 items-center justify-center rounded-full text-muted-foreground">
              <ImagePlus className="size-4" />
            </span>
            <span className="flex size-8 items-center justify-center rounded-full bg-foreground text-background">
              <ArrowUp className="size-4" strokeWidth={2.5} />
            </span>
          </span>
        </div>
      </div>
    </MiniScreen>
  );
}

function Avatar() {
  return (
    <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-black/[0.06]">
      <Mark className="h-3.5 text-foreground" />
    </span>
  );
}
