import { Check, Cpu, ImagePlus, Lightbulb, Lock, Sparkles, WifiOff } from "lucide-react";
import { Mark } from "@/components/brand/logo";
import { cn } from "@/lib/utils";

/*
 * Il·lustracions abstractes de la landing: skeletons que es mouen en bucle.
 * Tot és CSS (classes .loop-* i .skel de globals.css): no depenen del
 * JavaScript i, amb «reduir moviment», queden quietes i visibles.
 * Cada bucle dura 6 s; els retards (animationDelay) expliquen la història.
 */

const d = (seconds: number) => ({ animationDelay: `${seconds}s` });

/** Marc comú: panell suau amb una trama de punts que s'esvaeix a les vores. */
export function VisualFrame({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "relative flex h-56 items-center justify-center overflow-hidden rounded-xl border border-black/[0.05] bg-[linear-gradient(180deg,#fbfbfa,#f4f4f2)]",
        className,
      )}
    >
      <div
        aria-hidden
        className="absolute inset-0 opacity-70"
        style={{
          backgroundImage: "radial-gradient(rgb(0 0 0 / 0.09) 1px, transparent 1px)",
          backgroundSize: "14px 14px",
          maskImage: "radial-gradient(ellipse 70% 70% at 50% 50%, #000 30%, transparent 80%)",
        }}
      />
      <div aria-hidden className="relative flex w-full items-center justify-center px-6">
        {children}
      </div>
    </div>
  );
}

function Card({ className, children, style }: { className?: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div
      style={style}
      className={cn(
        "rounded-xl border border-black/[0.06] bg-white shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_24px_-8px_rgba(0,0,0,0.10)]",
        className,
      )}
    >
      {children}
    </div>
  );
}

/* 1 · Respon: un problema, cinc opcions; una es descarta i una altra s'encerta. */
export function VisualAnswer() {
  return (
    <Card className="w-full max-w-[250px] p-4">
      <div className="space-y-2">
        <div className="skel h-2 w-11/12" />
        <div className="skel h-2 w-9/12" />
        <div className="skel h-2 w-5/12" />
      </div>
      <div className="mt-4 grid grid-cols-5 gap-1.5">
        {["A", "B", "C", "D", "E"].map((l) => (
          <span
            key={l}
            className={cn(
              "relative flex h-8 items-center justify-center rounded-lg border border-black/[0.07] bg-white font-mono text-[11px] font-semibold text-foreground/55",
              l === "C" && "loop-pick",
            )}
          >
            {l}
            {l === "B" && (
              <span className="loop-strike absolute inset-x-1.5 top-1/2 h-[1.5px] -translate-y-1/2 rounded-full bg-destructive/70" />
            )}
          </span>
        ))}
      </div>
    </Card>
  );
}

/* 2 · Et preguntem: l'alumne explica com ho ha pensat; el mentor respon amb una pregunta. */
export function VisualQuestion() {
  return (
    <div className="flex w-full max-w-[260px] flex-col gap-2.5">
      <div className="loop-in flex justify-end" style={d(0)}>
        <div className="w-[70%] space-y-1.5 rounded-2xl rounded-br-md bg-foreground px-3.5 py-3">
          <div className="h-1.5 w-full rounded-full bg-white/25" />
          <div className="h-1.5 w-2/3 rounded-full bg-white/25" />
        </div>
      </div>
      <div className="loop-in flex items-start gap-2" style={d(0.9)}>
        <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-black/[0.06]">
          <Mark className="h-2.5 text-foreground" />
        </span>
        <Card className="flex-1 space-y-1.5 rounded-2xl rounded-tl-md px-3.5 py-3">
          <div className="flex items-center gap-1.5">
            <span className="flex size-4 items-center justify-center rounded-full bg-accent/12 text-[9px] font-bold text-accent">
              ?
            </span>
            <div className="loop-type h-1.5 flex-1 rounded-full bg-accent/35" style={d(1.1)} />
          </div>
          <div className="loop-type h-1.5 w-4/5 rounded-full bg-black/[0.08]" style={d(1.35)} />
        </Card>
      </div>
    </div>
  );
}

/* 3 · Pista a pista: ajudes que s'omplen una darrere l'altra; la solució, tancada. */
export function VisualLadder() {
  return (
    <Card className="w-full max-w-[250px] space-y-2.5 p-4">
      {[0, 1, 2].map((i) => (
        <div key={i} className="flex items-center gap-2.5">
          <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-accent/12 text-accent">
            <Lightbulb className="size-3" />
          </span>
          <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-black/[0.06]">
            <div className="loop-fill absolute inset-0 rounded-full bg-accent/70" style={d(i * 0.7)} />
          </div>
        </div>
      ))}
      <div className="flex items-center gap-2.5 opacity-50">
        <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-black/[0.06]">
          <Lock className="size-2.5 text-foreground/60" />
        </span>
        <div className="skel h-2 w-1/2" />
      </div>
    </Card>
  );
}

/* Mode 1 · Repte: una pila de problemes que passen; l'Elo puja. */
export function VisualDeck() {
  return (
    <div className="relative h-40 w-full max-w-[300px]">
      <Card className="absolute inset-x-6 top-5 h-28 rotate-[3deg] opacity-60">
        <span />
      </Card>
      <Card className="absolute inset-x-3 top-2.5 h-28 -rotate-[2deg] opacity-80">
        <span />
      </Card>
      <Card className="loop-deck absolute inset-x-0 top-0 h-32 p-4">
        <div className="space-y-2">
          <div className="skel h-2 w-10/12" />
          <div className="skel h-2 w-7/12" />
        </div>
        <div className="mt-5 flex gap-1.5">
          {["A", "B", "C", "D", "E"].map((l, i) => (
            <span
              key={l}
              className={cn(
                "flex h-7 flex-1 items-center justify-center rounded-md border border-black/[0.07] bg-white font-mono text-[10px] font-semibold text-foreground/55",
                i === 2 && "loop-pick",
              )}
            >
              {l}
            </span>
          ))}
        </div>
      </Card>
      <span
        className="loop-count absolute -top-3 -right-3 inline-flex items-center gap-1 rounded-full bg-foreground px-2.5 py-1 font-mono text-[11px] font-semibold text-background shadow-lg"
        style={d(0)}
      >
        <Check className="size-3 text-accent" strokeWidth={3} /> Elo +18
      </span>
    </div>
  );
}

/* Mode 2 · El meu problema: una foto que s'escaneja i una resposta que s'escriu. */
export function VisualChat() {
  return (
    <div className="flex w-full max-w-[300px] flex-col gap-3">
      <Card className="flex items-center gap-3 p-2.5">
        <div className="relative size-14 shrink-0 overflow-hidden rounded-lg bg-[linear-gradient(135deg,#f3f1ee,#e6e2dc)]">
          <div className="absolute inset-x-2 top-3 h-1 rounded-full bg-black/15" />
          <div className="absolute inset-x-2 top-5.5 h-1 w-6 rounded-full bg-black/10" />
          <div className="absolute inset-x-2 top-8 h-1 w-8 rounded-full bg-black/10" />
          <div className="loop-scan absolute inset-x-0 top-0 h-full bg-gradient-to-b from-transparent via-accent/45 to-transparent" />
        </div>
        <div className="flex-1 space-y-1.5">
          <div className="skel h-1.5 w-4/5" />
          <div className="skel h-1.5 w-1/2" />
        </div>
        <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-foreground text-background">
          <ImagePlus className="size-3.5" />
        </span>
      </Card>
      <Card className="space-y-2 p-3.5">
        <div className="flex items-center gap-1.5">
          <Sparkles className="size-3 text-accent" />
          <div className="loop-type h-1.5 w-1/3 rounded-full bg-accent/40" style={d(1.4)} />
        </div>
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex items-center gap-2">
            <span className="font-mono text-[9px] text-muted-foreground">{i + 1}.</span>
            <div
              className="loop-type h-1.5 rounded-full bg-black/[0.08]"
              style={{ ...d(1.7 + i * 0.35), width: ["85%", "70%", "55%"][i] }}
            />
          </div>
        ))}
      </Card>
    </div>
  );
}

/* La placa: tot entra i surt d'un xip, i res no surt cap a internet. */
export function VisualBoard() {
  return (
    <div className="relative flex h-40 w-full max-w-[360px] items-center justify-between">
      <div className="flex flex-col gap-2">
        {["Foto", "Dubte"].map((label) => (
          <span
            key={label}
            className="rounded-full border border-black/[0.07] bg-white px-2.5 py-1 text-[10px] font-medium text-muted-foreground shadow-sm"
          >
            {label}
          </span>
        ))}
      </div>
      <div className="relative mx-3 h-px flex-1 bg-black/10">
        <span className="loop-flow absolute -top-[3px] left-0 size-[7px] rounded-full bg-accent" style={{ ["--flow" as string]: "64px" }} />
      </div>
      <div className="relative">
        <span className="loop-ping absolute inset-0 rounded-2xl border border-accent/50" />
        <span className="loop-ping absolute inset-0 rounded-2xl border border-accent/40" style={{ animationDelay: "1.2s" }} />
        <div className="relative flex size-20 items-center justify-center rounded-2xl bg-foreground text-background shadow-[0_12px_32px_-8px_rgba(0,0,0,0.35)]">
          <Cpu className="size-8" strokeWidth={1.5} />
        </div>
      </div>
      <div className="relative mx-3 h-px flex-1 bg-black/10">
        <span className="loop-flow absolute -top-[3px] left-0 size-[7px] rounded-full bg-accent" style={{ ["--flow" as string]: "64px", animationDelay: "1.5s" }} />
      </div>
      <div className="flex flex-col items-end gap-2">
        <span className="rounded-full bg-accent px-2.5 py-1 text-[10px] font-semibold text-white shadow-sm">Pista</span>
        <span className="inline-flex items-center gap-1 rounded-full border border-dashed border-black/15 px-2.5 py-1 text-[10px] text-muted-foreground line-through">
          <WifiOff className="size-3" /> Núvol
        </span>
      </div>
    </div>
  );
}
