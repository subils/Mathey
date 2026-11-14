import { cn } from "@/lib/utils";

/**
 * Gradients dels panells de Faktu (sections/modulos-section.tsx): malva i sàlvia
 * molt suaus que s'alternen; `accent` els tenyeix amb el blau.
 */
export function panelGradient(index = 0, accent = false) {
  if (accent) {
    return [
      "radial-gradient(ellipse 65% 65% at 100% 0%, color-mix(in oklab, var(--accent) 16%, transparent) 0%, transparent 55%)",
      "radial-gradient(ellipse 65% 65% at 0% 100%, color-mix(in oklab, var(--accent) 8%, transparent) 0%, transparent 55%)",
      "linear-gradient(to bottom, rgba(255,255,255,0.6), transparent)",
    ].join(", ");
  }
  const mauve = "rgba(168,156,172,0.14)";
  const sage = "rgba(158,184,158,0.10)";
  const [a, b] = index % 2 === 0 ? [mauve, sage] : [sage, mauve];
  return [
    `radial-gradient(ellipse 65% 65% at 100% 0%, ${a} 0%, transparent 55%)`,
    `radial-gradient(ellipse 65% 65% at 0% 100%, ${b} 0%, transparent 55%)`,
    "linear-gradient(to bottom, rgba(255,255,255,0.6), transparent)",
  ].join(", ");
}

/**
 * La targeta de doble capa de Faktu: una vora gairebé invisible i, 5 px a dins,
 * el panell blanc amb el gradient. El contingut va per sobre.
 */
export function DoubleCard({
  className,
  innerClassName,
  index = 0,
  accent = false,
  plain = false,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  innerClassName?: string;
  index?: number;
  accent?: boolean;
  /** Sense gradient: panell blanc net. */
  plain?: boolean;
}) {
  return (
    <div className={cn("group relative isolate", className)} {...props}>
      <div className="pointer-events-none absolute inset-0 -z-10 rounded-2xl border border-black/[0.04]" />
      <div
        className={cn(
          "pointer-events-none absolute inset-[5px] -z-10 rounded-xl bg-white shadow-[0_1px_3px_rgba(0,0,0,0.03)]",
          accent && "ring-1 ring-accent/20",
          innerClassName,
        )}
        style={plain ? undefined : { backgroundImage: panelGradient(index, accent) }}
      />
      {children}
    </div>
  );
}

/** Etiqueta superior de secció (Faktu): petita, espaiada i en majúscules. */
export function Eyebrow({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p
      className={cn("text-[10px] font-semibold tracking-widest text-muted-foreground uppercase", className)}
      {...props}
    />
  );
}

/** Píndola petita de Faktu («Disponible ara»). */
export function Pill({ className, ...props }: React.ComponentProps<"span">) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border border-border bg-card px-2 py-0.5 text-[9px] font-semibold tracking-widest text-muted-foreground uppercase shadow-sm",
        className,
      )}
      {...props}
    />
  );
}
