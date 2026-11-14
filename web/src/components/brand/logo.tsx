import { cn } from "@/lib/utils";
import { KANGAROO_D, KANGAROO_VIEWBOX, LOGO_VIEWBOX, TRANSFORM, WORDMARK_D } from "./paths";

type Props = { className?: string; title?: string };

/** Logo complet (cangur + «Mathey»), en `currentColor`. L'alçada mana: `h-6`, `h-8`… */
export function Logo({ className, title = "Mathey" }: Props) {
  return (
    <svg
      viewBox={LOGO_VIEWBOX}
      role="img"
      aria-label={title}
      className={cn("h-6 w-auto", className)}
      fill="currentColor"
    >
      <g transform={TRANSFORM}>
        <path d={KANGAROO_D} />
        <path d={WORDMARK_D} />
      </g>
    </svg>
  );
}

/** Només el cangur. */
export function Mark({
  className,
  title,
  draw = false,
}: Props & { draw?: boolean }) {
  return (
    <svg
      viewBox={KANGAROO_VIEWBOX}
      role={title ? "img" : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
      className={cn("h-8 w-auto", className)}
      fill="currentColor"
    >
      <g transform={TRANSFORM}>
        {draw ? (
          <>
            {/* Primer es dibuixa el contorn i després s'omple. */}
            <path
              d={KANGAROO_D}
              fill="none"
              stroke="currentColor"
              strokeWidth={60}
              pathLength={1}
              strokeDasharray={1}
              strokeDashoffset={1}
              className="animate-draw"
            />
            <path
              d={KANGAROO_D}
              className="opacity-0 transition-opacity duration-500"
              style={{ animation: "page-enter 600ms var(--motion-ease-enter) 1.4s forwards" }}
            />
          </>
        ) : (
          <path d={KANGAROO_D} />
        )}
      </g>
    </svg>
  );
}

/**
 * El cangur saltant: carregant, «la placa està pensant». Només transform i
 * opacitat (compositor); amb `prefers-reduced-motion` queda quiet.
 */
export function HoppingKangaroo({
  className,
  label = "Carregant",
}: {
  className?: string;
  label?: string;
}) {
  return (
    <span
      role="status"
      aria-label={label}
      className={cn("relative inline-flex w-16 flex-col items-center", className)}
    >
      <span className="block w-full origin-bottom animate-hop">
        <Mark className="h-auto w-full" />
      </span>
      <span
        aria-hidden
        className="mt-[6%] block h-[7%] w-[70%] rounded-[50%] bg-foreground animate-hop-shadow blur-[1px]"
      />
    </span>
  );
}
