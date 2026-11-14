import type { Matrix } from "@/lib/api";

// Rèplica de la matriu de LEDs de la placa (8 files x 13 columnes, brillantor 0-7).
// A la placa, el mateix dibuix s'encén als LEDs de veritat.
export default function LedMatrix({ matrix, size = 10, label }: { matrix?: Matrix; size?: number; label?: string }) {
  const rows = matrix && matrix.length === 8 ? matrix : Array.from({ length: 8 }, () => Array(13).fill(0));
  return (
    <figure className="flex flex-col items-center gap-1" aria-label={label ?? "Matriu de LEDs de la placa"}>
      <div
        className="grid rounded-md bg-zinc-900 p-1.5 shadow-inner"
        style={{ gridTemplateColumns: `repeat(13, ${size}px)`, gap: Math.max(2, size / 4) }}
      >
        {rows.flatMap((row, r) =>
          row.map((value, c) => (
            <span
              key={`${r}-${c}`}
              className="rounded-full"
              style={{
                width: size,
                height: size,
                background: value > 0 ? `rgba(255, 64, 32, ${0.35 + (0.65 * value) / 7})` : "rgba(255,255,255,0.07)",
                boxShadow: value > 0 ? `0 0 ${size / 2}px rgba(255, 80, 40, 0.8)` : "none",
              }}
            />
          )),
        )}
      </div>
      <figcaption className="text-[11px] uppercase tracking-wide text-zinc-500">{label ?? "Matriu de la placa"}</figcaption>
    </figure>
  );
}
