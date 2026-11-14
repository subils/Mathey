import { ArrowUp, ArrowUpRight, Check, Gauge, ImagePlus, Lightbulb, Lock, Plus, Sparkles, Type } from "lucide-react";
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
export function MiniScreen({ width, height, children }: { width: number; height: number; children: React.ReactNode }) {
  return (
    <div className="pointer-events-none flex size-full items-center justify-center select-none">
      <div
        className="origin-center scale-[0.46] sm:scale-[0.8] md:scale-[0.44] lg:scale-[0.6] xl:scale-[0.84]"
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

export function MiniRepte() {
  return (
    <MiniScreen width={640} height={430}>
      <div className="flex h-full flex-col gap-3.5 text-left">
        {/* Barra superior del Repte */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-[13px]">
            <span className="rounded-lg bg-foreground px-2.5 py-1 font-medium text-background">Aritmètica</span>
            <span className="relative inline-flex items-center gap-1.5 rounded-lg border border-black/[0.06] bg-white/80 px-2.5 py-1">
              <span className="text-muted-foreground">Elo</span>
              <span className="font-mono font-medium tabular-nums">1025</span>
              <span className="loop-count font-mono text-[12px] font-semibold text-success" style={d(0)}>
                +18
              </span>
            </span>
          </div>
          <div className="flex items-center gap-1 rounded-xl bg-black/[0.045] p-1 text-[12px] font-medium">
            <Gauge className="mx-1.5 size-3.5 text-muted-foreground" />
            <span className="px-2.5 py-1 text-muted-foreground">Més fàcil</span>
            <span className="rounded-lg bg-white px-2.5 py-1 shadow-[0_1px_2px_rgba(0,0,0,0.06)]">Al meu nivell</span>
            <span className="px-2.5 py-1 text-muted-foreground">Més difícil</span>
          </div>
        </div>

        <div className="grid flex-1 grid-cols-[1fr_190px] gap-3.5">
          <div className="flex flex-col gap-3">
            {/* El problema */}
            <div className="rounded-2xl bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] ring-1 ring-black/[0.05]">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold tracking-widest text-muted-foreground uppercase">
                  Cangur 2019 · Elo 1100
                </span>
                <span className="inline-flex items-center gap-1 text-[12px] font-medium">
                  <Type className="size-3.5" /> Lectura fàcil
                </span>
              </div>
              <p className="mt-3 text-[15px] leading-relaxed">
                La Laia té 3 germans. Cada germà té 2 germanes. Quants fills hi ha a la família?
              </p>
            </div>

            {/* Les cinc opcions */}
            <div className="grid grid-cols-5 gap-2">
              {OPTIONS.map((o) => (
                <span
                  key={o.l}
                  className={cn(
                    "relative flex flex-col items-center gap-1.5 rounded-2xl border border-black/[0.07] bg-white py-3",
                    o.state === "wrong" && "loop-wrong",
                    o.state === "right" && "loop-correct",
                  )}
                >
                  <span
                    className={cn(
                      "flex size-8 items-center justify-center rounded-xl bg-black/[0.045] font-mono text-[14px] font-semibold",
                      o.state === "right" && "loop-correct-badge",
                    )}
                  >
                    {o.l}
                  </span>
                  <span className="text-[14px]">{o.v}</span>
                  {o.state === "wrong" && (
                    <span className="loop-strike absolute inset-x-5 top-[62%] h-[1.5px] rounded-full bg-destructive/60" />
                  )}
                </span>
              ))}
            </div>

            {/* «Molt bé!» */}
            <div
              className="loop-count flex items-center gap-3 rounded-2xl border border-success/25 bg-white px-4 py-3"
              style={d(0)}
            >
              <span className="flex size-7 items-center justify-center rounded-full bg-success text-white">
                <Check className="size-4" strokeWidth={3} />
              </span>
              <div>
                <p className="text-[15px] font-medium">Molt bé!</p>
                <p className="text-[12px] text-muted-foreground">
                  Era la <span className="font-mono font-semibold text-foreground">B</span> · al primer intent
                </p>
              </div>
            </div>
          </div>

          {/* Escala d'ajudes */}
          <div className="flex flex-col gap-3 rounded-2xl bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)] ring-1 ring-black/[0.05]">
            <div className="flex items-center justify-between">
              <span className="text-[13px] font-medium">Escala d&apos;ajudes</span>
              <span className="font-mono text-[11px] text-muted-foreground">1/5</span>
            </div>
            {["Una estratègia", "La dada clau", "Un problema germà", "El primer pas", "La solució"].map((r, i) => (
              <div key={r} className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "flex size-5 items-center justify-center rounded-full font-mono text-[10px] font-semibold",
                      i === 0 ? "bg-foreground text-background" : i === 1 ? "bg-accent text-white" : "bg-black/[0.06] text-muted-foreground",
                    )}
                  >
                    {i === 4 ? <Lock className="size-2.5" /> : i + 1}
                  </span>
                  <span className={cn("text-[12px]", i > 1 && "text-muted-foreground")}>{r}</span>
                </div>
                {i === 0 && (
                  <div className="ml-7 space-y-1">
                    <div className="loop-type h-1.5 w-full rounded-full bg-black/[0.1]" style={d(0.3)} />
                    <div className="loop-type h-1.5 w-2/3 rounded-full bg-black/[0.1]" style={d(0.5)} />
                  </div>
                )}
              </div>
            ))}
            <span className="mt-auto flex items-center justify-center gap-1.5 rounded-xl border border-black/[0.08] py-2 text-[12px] font-medium">
              <Lightbulb className="size-3.5" /> Més ajuda
            </span>
          </div>
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
