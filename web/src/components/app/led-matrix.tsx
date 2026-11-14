import type { Matrix } from "@/lib/api";
import { cn } from "@/lib/utils";

const EMPTY: Matrix = Array.from({ length: 8 }, () => Array(13).fill(0));

/**
 * Mirall de la matriu de LEDs de la placa (8 × 13, brillantor 0–7): el mateix
 * dibuix que s'encén als LEDs de veritat. Panell fosc, com el maquinari.
 */
export function LedMatrix({
  matrix,
  className,
  dot = 9,
}: {
  matrix?: Matrix;
  className?: string;
  /** Mida de cada LED en px. */
  dot?: number;
}) {
  const rows = matrix && matrix.length === 8 ? matrix : EMPTY;
  return (
    <div
      role="img"
      aria-label="Matriu de LEDs de la placa"
      className={cn(
        "inline-grid rounded-xl bg-[#151515] p-2.5 shadow-[inset_0_1px_0_rgb(255_255_255/0.06),0_1px_2px_rgb(0_0_0/0.2),0_8px_24px_rgb(0_0_0/0.12)] ring-1 ring-black/40",
        className,
      )}
      style={{ gridTemplateColumns: `repeat(13, ${dot}px)`, gap: Math.max(2, Math.round(dot / 3)) }}
    >
      {rows.flatMap((row, r) =>
        row.map((value, c) => (
          <span
            key={`${r}-${c}`}
            className="rounded-full transition-[background-color,box-shadow] duration-200"
            style={{
              width: dot,
              height: dot,
              background: value > 0 ? `rgb(var(--led-on) / ${0.35 + (0.65 * value) / 7})` : "rgb(255 255 255 / 0.06)",
              boxShadow: value > 0 ? `0 0 ${dot * 0.7}px rgb(255 80 40 / ${0.35 + (0.45 * value) / 7})` : "none",
            }}
          />
        )),
      )}
    </div>
  );
}
