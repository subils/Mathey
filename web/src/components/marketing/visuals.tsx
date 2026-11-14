import {
  Check,
  Cloud,
  Footprints,
  Image as ImageIcon,
  KeyRound,
  Lightbulb,
  Lock,
  MessageCircle,
  Timer,
  User,
} from "lucide-react";
import { Mark } from "@/components/brand/logo";
import { cn } from "@/lib/utils";

/*
 * Il·lustracions abstractes de la landing, en l'estil monocrom de la referència:
 * cercles grisos i negres, barres clares, píndoles negres i petites insígnies
 * d'icona al voltant. El taronja, només en un detall. Tot és CSS en bucle
 * (.loop-* i .skel de globals.css): no depèn del JavaScript i, amb «reduir
 * moviment», queda quiet i visible. Cada bucle dura 6 s; els retards expliquen
 * la història.
 */

const d = (seconds: number) => ({ animationDelay: `${seconds}s` });

/** Marc comú: panell gris molt clar amb una llum suau a dalt. */
export function VisualFrame({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "relative flex h-60 items-center justify-center overflow-hidden rounded-xl bg-[radial-gradient(120%_90%_at_50%_0%,#ffffff_0%,#f6f6f5_55%,#efefee_100%)] ring-1 ring-black/[0.04]",
        className,
      )}
    >
      <div aria-hidden className="relative flex size-full items-center justify-center">
        {children}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- peces */

/** Barra clara, com les de la referència. */
function Bar({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <div style={style} className={cn("h-2.5 rounded-full bg-white shadow-[0_0_0_1px_rgba(0,0,0,0.03)]", className)} />;
}

/** Cercle (avatar o node). */
function Dot({
  className,
  dark = false,
  size = "size-8",
  children,
  style,
}: {
  className?: string;
  dark?: boolean;
  size?: string;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <span
      style={style}
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full [&_svg]:size-[45%]",
        size,
        dark ? "bg-[#111] text-white" : "bg-[#c9c9c9] text-[#6b6b6b]",
        className,
      )}
    >
      {children}
    </span>
  );
}

/** Insígnia petita amb icona, que apareix (pop) en un moment del bucle. */
function Badge({
  icon,
  className,
  delay = 0,
  accent = false,
}: {
  icon: React.ReactNode;
  className?: string;
  delay?: number;
  accent?: boolean;
}) {
  return (
    <span
      style={d(delay)}
      className={cn(
        "loop-pop absolute flex size-7 items-center justify-center rounded-full shadow-[0_1px_2px_rgba(0,0,0,0.06)] [&_svg]:size-3.5",
        accent ? "bg-accent text-white" : "bg-[#dcdcdc] text-[#3a3a3a]",
        className,
      )}
    >
      {icon}
    </span>
  );
}

/** Píndola negra amb barres blanques (un missatge). */
function Pill({ className, bars = ["w-44", "w-28"], style }: { className?: string; bars?: string[]; style?: React.CSSProperties }) {
  return (
    <div style={style} className={cn("space-y-1.5 rounded-xl bg-[#111] px-3 py-2.5", className)}>
      {bars.map((w, i) => (
        <div key={i} className={cn("h-2 rounded-full bg-white", w)} />
      ))}
    </div>
  );
}

/** Tres punts d'«escrivint». */
function Typing({ className, dark = false }: { className?: string; dark?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-[3px]", className)}>
      {[0, 0.15, 0.3].map((t) => (
        <span
          key={t}
          className={cn("loop-dots size-[5px] rounded-full", dark ? "bg-[#111]" : "bg-[#6b6b6b]")}
          style={{ animationDelay: `${t}s` }}
        />
      ))}
    </span>
  );
}

/* ------------------------------------------------- 01 · Respon */

export function VisualAnswer() {
  return (
    <div className="relative">
      <div className="flex flex-col gap-3">
        {["A", "B", "C"].map((l, i) => (
          <div key={l} className="flex items-center gap-3">
            <span
              className={cn(
                "flex size-8 items-center justify-center rounded-full bg-black/[0.08] font-mono text-[11px] font-semibold text-[#1a1a1a]/50",
                i === 2 && "loop-select",
              )}
            >
              {l}
            </span>
            <Bar className={["w-28", "w-24", "w-32"][i]} />
          </div>
        ))}
      </div>
      <Badge icon={<Check strokeWidth={3} />} accent className="-top-3 -right-8" delay={0} />
      <Badge icon={<Timer />} className="-bottom-2 -left-9" delay={0.4} />
    </div>
  );
}

/* ------------------------------------------------- 02 · Et preguntem */

export function VisualQuestion() {
  return (
    <div className="relative flex flex-col gap-3">
      <div className="flex items-center gap-2.5 opacity-90">
        <Dot>
          <User />
        </Dot>
        <Bar className="w-32" />
      </div>
      <div className="loop-in flex items-center gap-2.5" style={d(0.6)}>
        <Dot dark>
          <Mark className="!h-3 !w-auto text-white" />
        </Dot>
        <Pill bars={["w-36", "w-20"]} />
      </div>
      <Badge icon={<span className="text-[11px] font-bold">?</span>} accent className="-top-4 right-2" delay={0.9} />
      <Badge icon={<Lightbulb />} className="-bottom-4 left-10" delay={1.2} />
      <Badge icon={<Typing />} className="top-1 -right-10 w-9" delay={0.2} />
    </div>
  );
}

/* ------------------------------------------------- 03 · Pista a pista */

export function VisualLadder() {
  const rungs = [<Lightbulb key="a" />, <KeyRound key="b" />, <Footprints key="c" />];
  return (
    <div className="relative flex flex-col gap-3">
      {rungs.map((icon, i) => (
        <div key={i} className="flex items-center gap-3" style={{ paddingLeft: i * 14 }}>
          <Dot className="loop-select" style={d(i * 0.55)}>
            {icon}
          </Dot>
          <div className="relative h-2.5 w-28 overflow-hidden rounded-full bg-white shadow-[0_0_0_1px_rgba(0,0,0,0.03)]">
            <div className="loop-fill absolute inset-0 rounded-full bg-[#111]/80" style={d(i * 0.55)} />
          </div>
        </div>
      ))}
      <div className="flex items-center gap-3" style={{ paddingLeft: 42 }}>
        <Dot dark>
          <Lock />
        </Dot>
        <div className="h-2.5 w-16 rounded-full bg-white/70" />
      </div>
    </div>
  );
}

/* ------------------------------------------------- La placa */

export function VisualBoard() {
  return (
    <div className="relative flex items-center gap-6">
      <div className="flex flex-col gap-4">
        <Dot>
          <ImageIcon />
        </Dot>
        <Dot>
          <MessageCircle />
        </Dot>
      </div>
      <div className="relative h-px w-14 border-t border-dashed border-black/20">
        <span className="loop-flow absolute -top-[4px] left-0 size-[7px] rounded-full bg-accent" style={{ ["--flow" as string]: "56px" }} />
      </div>
      <div className="relative">
        <span className="loop-ping absolute inset-0 rounded-[22px] border border-black/15" />
        <span className="loop-ping absolute inset-0 rounded-[22px] border border-black/10" style={{ animationDelay: "1.2s" }} />
        <div className="relative flex size-20 items-center justify-center rounded-[22px] bg-[#111] text-white shadow-[0_14px_32px_-10px_rgba(0,0,0,0.45)]">
          <Mark className="h-7 text-white" />
        </div>
      </div>
      <div className="relative h-px w-14 border-t border-dashed border-black/20">
        <span
          className="loop-flow absolute -top-[4px] left-0 size-[7px] rounded-full bg-accent"
          style={{ ["--flow" as string]: "56px", animationDelay: "1.5s" }}
        />
      </div>
      <Dot dark>
        <Lightbulb />
      </Dot>
      <span className="absolute -top-12 left-1/2 flex -translate-x-1/2 items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-[10px] font-medium text-[#6b6b6b] shadow-[0_1px_2px_rgba(0,0,0,0.06)]">
        <Cloud className="size-3" />
        <span className="line-through">Núvol</span>
      </span>
    </div>
  );
}
